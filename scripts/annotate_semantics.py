#!/usr/bin/env python
"""
annotate_semantics.py

Schritt 2 der Pipeline: normalisierte Chunks (normalized/json/*.jsonl)
werden per LLM (Ollama) semantisch annotiert:

- content_type   (Liste von IDs aus config/taxonomy/content_type.json)
- domain         (Liste von IDs aus config/taxonomy/domain.json)
- artifact_role  (Liste von IDs aus config/taxonomy/artifact_role.json)
- trust_level    (eine ID aus config/taxonomy/trust_level.json)
- chunk_role     (optionale pädagogische Rolle des Chunks: definition, example, ...)
- language       (de/en/mixed/unknown)

Zusätzliche angereicherte Felder:
- summary_short  (kurze, 1–3-sätzige Chunk-Zusammenfassung als String)
- equations      (Liste von Objekten mit Informationen zu Gleichungen)
- key_quantities (Liste von Strings mit wichtigen physikalischen Größen/Themen)

Ergebnis wird als identische JSONL-Struktur in semantic/json/ geschrieben.

Wiederaufnahmefähig:
- Existiert bereits eine Ausgabedatei, werden vorhandene Records pro chunk_id
  eingelesen.
- Bereits annotierte Chunks (semantic.trust_level vorhanden) werden übersprungen.
- Ist die Ausgabe für eine Datei bereits vollständig annotiert, wird sie komplett
  übersprungen.

Erweitertes Logging:
- Zählt die Gesamtzahl der Records.
- Gibt Fortschritt in der Form [aktuell/gesamt] aus.
- Schreibt Zeitstempel in den Log.
- Schätzt anhand des bisherigen Fortschritts eine ETA (voraussichtliche Fertigstellungszeit).

Sharding:
- Die Menge der Eingabedateien kann über (--num-shards, --shard-id) auf mehrere
  Jobs (z. B. SLURM-Array) verteilt werden.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import logging
import os
import re
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

# ---------------------------------------------------------------------------
# Pfade / Taxonomie laden (paths_utils per absolutem Pfad laden)
# ---------------------------------------------------------------------------

# Verzeichnis dieses Skripts: ./dachs_rag_framework/scripts
THIS_DIR = Path(__file__).resolve().parent

# Repo-Root: ./dachs_rag_framework
REPO_ROOT = THIS_DIR.parent

# Absoluter Pfad zu config/paths/paths_utils.py
PATHS_UTILS_PATH = REPO_ROOT / "config" / "paths" / "paths_utils.py"

# Modul aus Datei laden (ohne dass "config" als Package existieren muss)
spec = importlib.util.spec_from_file_location("dachs_paths_utils", PATHS_UTILS_PATH)
paths_utils = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(paths_utils)

# Funktionen/Variablen aus paths_utils übernehmen
get_path = paths_utils.get_path
REPO_ROOT = paths_utils.REPO_ROOT  # gleiche Logik wie in paths_utils.py

# Taxonomie- und LLM-Konfig-Pfade im Repo
TAXONOMY_DIR = REPO_ROOT / "config" / "taxonomy"
LLM_CONFIG_PATH = REPO_ROOT / "config" / "LLM" / "semantic_llm.json"


# ---------------------------------------------------------------------------
# Pfade / Taxonomie laden
# ---------------------------------------------------------------------------


def load_json_file(path: Path) -> Any:
    """Hilfsfunktion: JSON-Datei laden oder klarer Fehler."""
    if not path.is_file():
        raise FileNotFoundError(f"Datei nicht gefunden: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_taxonomies() -> Dict[str, List[Dict[str, Any]]]:
    """
    Lädt die Taxonomien aus config/taxonomy/*.

    Erwartet mindestens:
      - content_type.json
      - domain.json
      - artifact_role.json
      - trust_level.json

    Optional:
      - chunk_role.json
    """
    taxonomies = {
        "content_type": load_json_file(TAXONOMY_DIR / "content_type.json"),
        "domain": load_json_file(TAXONOMY_DIR / "domain.json"),
        "artifact_role": load_json_file(TAXONOMY_DIR / "artifact_role.json"),
        "trust_level": load_json_file(TAXONOMY_DIR / "trust_level.json"),
    }

    chunk_role_path = TAXONOMY_DIR / "chunk_role.json"
    if chunk_role_path.is_file():
        taxonomies["chunk_role"] = load_json_file(chunk_role_path)
    else:
        taxonomies["chunk_role"] = []

    return taxonomies


def extract_ids(tax_list: List[Dict[str, Any]]) -> List[str]:
    """Extrahiert alle 'id'-Felder aus einer Taxonomie-Liste."""
    return [str(entry["id"]) for entry in tax_list if "id" in entry]


# ---------------------------------------------------------------------------
# LLM-Client (Ollama /api/chat)
# ---------------------------------------------------------------------------


class LLMSemanticClassifier:
    """
    Dünner Wrapper um Ollama /api/chat für unsere Klassifikations- und
    Anreicherungsaufgabe (Semantik + summary_short + equations + key_quantities).
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        # Basis-URL aus config oder aus OLLAMA_HOST
        base = config.get("endpoint") or os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        if not str(base).startswith("http"):
            base = f"http://{base}"
        self.base_url = str(base).rstrip("/")

        self.model = config.get("model", "llama3.1:8b")
        self.temperature = float(config.get("temperature", 0.0))
        # max_tokens -> num_predict bei Ollama (Antwortlänge)
        self.max_tokens = int(config.get("max_tokens", 512))
        # Sicherheits-Limit für Chunk-Textlänge (in Zeichen)
        self.max_chars = int(config.get("max_chars", 4000))

    def classify_chunk(
        self,
        text: str,
        doc_title: str,
        taxonomies: Dict[str, List[Dict[str, Any]]],
        prev_text: Optional[str] = None,
        next_text: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Ruft das LLM auf und erwartet ein reines JSON-Objekt als Antwort.

        prev_text / next_text: Nachbar-Chunks als Kontext (optional).
        """
        if not text:
            return None

        # Haupt-Text ggf. hart beschneiden
        if len(text) > self.max_chars:
            text = text[: self.max_chars]

        # Nachbar-Kontext leicht beschneiden, damit der Prompt nicht explodiert
        def _clip_neighbor(s: Optional[str], max_len: int = 1000) -> Optional[str]:
            if not s:
                return None
            s = s.strip()
            if len(s) <= max_len:
                return s
            return s[:max_len]

        prev_text = _clip_neighbor(prev_text)
        next_text = _clip_neighbor(next_text)

        # IDs + optionale Beschreibungen für den Prompt vorbereiten
        def fmt_list(name: str) -> str:
            items = []
            for entry in taxonomies.get(name, []):
                _id = entry.get("id")
                desc = entry.get("description", "")
                label = entry.get("label", "")
                if label:
                    items.append(f'- "{_id}": {label} – {desc}')
                else:
                    items.append(f'- "{_id}": {desc}')
            return "\n".join(items) if items else "(none)"

        content_type_block = fmt_list("content_type")
        domain_block = fmt_list("domain")
        artifact_role_block = fmt_list("artifact_role")
        trust_level_block = fmt_list("trust_level")
        chunk_role_block = fmt_list("chunk_role") if taxonomies.get("chunk_role") else ""

        system_prompt = (
            "You are a precise classifier for technical engineering documents "
            "(thermodynamics, simulations, experiments, HPC, GT-Power, documentation). "
            "Your job is to assign semantic tags from a fixed taxonomy and to extract "
            "a short summary and structured information about equations.\n\n"
            "You MUST respond with a single JSON object only. No explanations, "
            "no markdown, no surrounding text.\n\n"
            "If the MAIN CHUNK contains no meaningful content (shorter than 5 characters, "
            "or only punctuation, or only numbers), then:\n"
            "- set language to \"unknown\",\n"
            "- set all taxonomy lists (content_type, domain, artifact_role, chunk_role, key_quantities) to empty lists,\n"
            "- set trust_level to \"low\" if available in the taxonomy, otherwise choose any valid ID,\n"
            "- set summary_short to an empty string \"\",\n"
            "- set equations to an empty list.\n"
            "Do NOT invent semantics for such chunks."
        )

        # Basis-User-Prompt
        user_prompt = f"""
We have a text CHUNK from a larger document.

Document title: "{doc_title}"

MAIN CHUNK TEXT:
\"\"\"{text}\"\"\""""

        # Nachbar-Kontext optional einfügen
        if prev_text or next_text:
            user_prompt += "\n\nNEIGHBORING CONTEXT (for orientation, do NOT classify these separately):\n"
            if prev_text:
                user_prompt += f'\n[PREVIOUS CHUNK]:\n\"\"\"{prev_text}\"\"\"\n'
            if next_text:
                user_prompt += f'\n[NEXT CHUNK]:\n\"\"\"{next_text}\"\"\"\n'

        user_prompt += """

TASK:
Classify ONLY the MAIN CHUNK according to the following taxonomy.
Use ONLY IDs from the lists. If nothing clearly fits, use empty lists.

Allowed values:

1) language (free choice, not from taxonomy):
   - "de"      : German
   - "en"      : English
   - "mixed"   : clearly mixed German/English
   - "unknown" : cannot be determined

2) content_type (0–2 items from this list):
""" + content_type_block + """

3) domain (0–3 items from this list):
""" + domain_block + """

4) artifact_role (0–3 items from this list):
""" + artifact_role_block + """

5) trust_level (exactly ONE item from this list):
""" + trust_level_block + """
"""

        if chunk_role_block:
            user_prompt += """

6) chunk_role (0–2 items from this list, pedagogical function of the MAIN CHUNK):
""" + chunk_role_block + """
"""

        user_prompt += """

Additionally, extract:

7) summary_short:
   - 1–3 sentences in plain text
   - Summarize the MAIN CHUNK (not the whole document).

8) equations:
   - List of objects describing important equations in the MAIN CHUNK.
   - Each object SHOULD have the following keys where possible:
       - "latex": equation in LaTeX style (e.g. "q = h A (T_s - T_∞)")
       - "description": short description of what the equation represents
       - "variables": list of objects with keys:
           - "symbol": variable symbol (e.g. "q")
           - "name": variable name in words (e.g. "heat transfer rate")
           - "unit": SI unit if known (e.g. "W"). If unknown, use "".
   - If there are no relevant equations, use an empty list.

9) key_quantities:
   - List of strings naming the most important physical or technical quantities
     in the MAIN CHUNK (e.g. "evaporation_rate", "heat_transfer_coefficient").
   - If none are relevant, use an empty list.

OUTPUT FORMAT:
Return EXACTLY one JSON object with keys:
  "language": string,
  "content_type": list of strings,
  "domain": list of strings,
  "artifact_role": list of strings,
  "trust_level": string,"""

        if chunk_role_block:
            user_prompt += """
  "chunk_role": list of strings,"""

        user_prompt += """
  "summary_short": string,
  "equations": list of objects,
  "key_quantities": list of strings

Example (schema only, NOT the real answer):
{
  "language": "de",
  "content_type": ["textbook"],
  "domain": ["thermodynamics"],
  "artifact_role": ["statement"],
  "trust_level": "high","""

        if chunk_role_block:
            user_prompt += """
  "chunk_role": ["definition"],"""

        user_prompt += """
  "summary_short": "Kurze Zusammenfassung des Chunk-Inhalts.",
  "equations": [
    {
      "latex": "q = h A (T_s - T_∞)",
      "description": "Convective heat transfer from a surface to the surrounding fluid.",
      "variables": [
        {"symbol": "q",  "name": "heat transfer rate", "unit": "W"},
        {"symbol": "h",  "name": "convective heat transfer coefficient", "unit": "W/m^2 K"},
        {"symbol": "A",  "name": "surface area", "unit": "m^2"},
        {"symbol": "T_s","name": "surface temperature", "unit": "K"},
        {"symbol": "T_∞","name": "fluid temperature far from the surface", "unit": "K"}
      ]
    }
  ],
  "key_quantities": ["heat_transfer_coefficient", "surface_temperature"]
}

Now produce the JSON classification and enrichment for the MAIN CHUNK.
"""

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": self.temperature,
            "stream": False,
            # kein explizites format=json hier – wir parsen selbst robust
            "options": {
                "num_predict": self.max_tokens,
            },
        }

        url = self.base_url + "/api/chat"

        try:
            resp = requests.post(url, json=payload, timeout=120)
            resp.raise_for_status()
        except Exception as e:
            logging.error("LLM-Request failed: %s", e)
            return None

        try:
            data = resp.json()
            content = data.get("message", {}).get("content", "")
        except Exception as e:
            logging.error("Failed to parse LLM JSON response: %s", e)
            return None

        return self._safe_parse_json(str(content))

    @staticmethod
    def _safe_parse_json(text: str) -> Optional[Dict[str, Any]]:
        """
        Robustheitsschicht: versucht, aus einem Text ein Dict zu parsen.
        (inkl. Fällen, wo das Modell fälschlich ```json ... ``` drumherum packt.)
        """
        text = text.strip()
        # Falls Modell blöderweise ```json ... ``` liefert
        if text.startswith("```"):
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                text = text[start : end + 1]

        # direct try
        try:
            obj = json.loads(text)
            if isinstance(obj, dict):
                return obj
        except Exception:
            pass

        # zweiter Versuch: substring zwischen { ... }
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                obj = json.loads(text[start : end + 1])
                if isinstance(obj, dict):
                    return obj
            except Exception:
                pass

        logging.error("Could not parse LLM output as JSON: %r", text[:200])
        return None


# ---------------------------------------------------------------------------
# Semantik anwenden / Validierung gegen Taxonomie
# ---------------------------------------------------------------------------


def normalize_semantic_result(
    raw: Dict[str, Any],
    taxonomies: Dict[str, List[Dict[str, Any]]],
) -> Dict[str, Any]:
    """
    Filtert und normalisiert die LLM-Ausgabe gegen die Taxonomien.

    - entfernt unbekannte IDs
    - enforced Sprach-Werte
    - begrenzt Listengrößen
    - reicht summary_short, equations, key_quantities strukturiert weiter
    """
    allowed_content_type = set(extract_ids(taxonomies.get("content_type", [])))
    allowed_domain = set(extract_ids(taxonomies.get("domain", [])))
    allowed_artifact_role = set(extract_ids(taxonomies.get("artifact_role", [])))
    allowed_trust_level = set(extract_ids(taxonomies.get("trust_level", [])))
    allowed_chunk_role = set(extract_ids(taxonomies.get("chunk_role", [])))

    # Sprache
    language = raw.get("language", "unknown")
    if language not in {"de", "en", "mixed", "unknown"}:
        language = "unknown"

    # helper: Liste von Strings, die in einem Set liegen müssen
    def filter_list(field: str, allowed: set[str], max_len: int | None = None) -> List[str]:
        vals = raw.get(field, [])
        if not isinstance(vals, list):
            return []
        out = []
        for v in vals:
            s = str(v)
            if s in allowed and s not in out:
                out.append(s)
        if max_len is not None:
            return out[:max_len]
        return out

    content_type = filter_list("content_type", allowed_content_type, max_len=2)
    domain = filter_list("domain", allowed_domain, max_len=3)
    artifact_role = filter_list("artifact_role", allowed_artifact_role, max_len=3)
    chunk_role = filter_list("chunk_role", allowed_chunk_role, max_len=2)

    # trust_level: genau eins, sonst Fallback
    tl_raw = str(raw.get("trust_level", "")).strip()
    trust_level = tl_raw if tl_raw in allowed_trust_level else None
    if trust_level is None:
        # Fallback: "medium", falls vorhanden, sonst erster Eintrag
        if "medium" in allowed_trust_level:
            trust_level = "medium"
        else:
            trust_level = next(iter(allowed_trust_level)) if allowed_trust_level else "unknown"

    # summary_short
    summary_raw = raw.get("summary_short", "")
    summary_short = ""
    if isinstance(summary_raw, str):
        summary_short = summary_raw.strip()

    # equations
    equations_raw = raw.get("equations")
    equations: List[Dict[str, Any]] = []
    if isinstance(equations_raw, list):
        for eq in equations_raw:
            if isinstance(eq, dict):
                equations.append(eq)
            else:
                equations.append({"description": str(eq)})

    # key_quantities
    kq_raw = raw.get("key_quantities", [])
    key_quantities: List[str] = []
    if isinstance(kq_raw, list):
        for item in kq_raw:
            key_quantities.append(str(item))

    return {
        "language": language,
        "content_type": content_type,
        "domain": domain,
        "artifact_role": artifact_role,
        "trust_level": trust_level,
        "chunk_role": chunk_role,
        "summary_short": summary_short,
        "equations": equations,
        "key_quantities": key_quantities,
    }


# ---------------------------------------------------------------------------
# Hauptlogik: JSONL lesen, annotieren, wieder schreiben (mit Nachbar-Kontext,
# und Wiederaufnahme über vorhandene Ausgabedatei / chunk_id)
# ---------------------------------------------------------------------------


def process_file(
    in_path: Path,
    out_path: Path,
    classifier: LLMSemanticClassifier,
    taxonomies: Dict[str, List[Dict[str, Any]]],
    progress: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Liest eine JSONL-Datei, annotiert jeden Chunk mit LLM und schreibt
    eine neue JSONL-Datei.

    Wiederaufnahme:
    - Falls out_path bereits existiert, werden vorhandene Records pro chunk_id
      eingelesen.
    - Für Chunks mit vorhandener semantic.trust_level wird kein LLM-Call mehr gemacht.
    - Ist die bestehende Ausgabe vollständig annotiert, wird die Datei übersprungen.

    Erweiterter Fortschritts-Log:
    - Zählt total Chunks.
    - Loggt nach jedem Chunk: [aktuell/gesamt] prozentualen Fortschritt, Elapsed, ETA.
    """
    logging.info("Verarbeite %s → %s", in_path.name, out_path.name)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # 1) komplette Eingabedatei einlesen
    records: List[Dict[str, Any]] = []
    with in_path.open("r", encoding="utf-8") as fin:
        for line in fin:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                logging.warning("Überspringe ungültige JSON-Zeile in %s", in_path)
                continue
            records.append(rec)

    total = len(records)
    if total == 0:
        logging.warning("Keine gültigen Records in %s", in_path)
        # leere Ausgabedatei erzeugen
        out_path.write_text("", encoding="utf-8")
        return

    # Erlaubte artifact_role-IDs aus Taxonomie (für heuristische Ergänzungen)
    allowed_artifact_role = set(extract_ids(taxonomies.get("artifact_role", [])))

    # Fortschritts-Tracking: falls kein globales progress-Objekt übergeben wurde, lokal anlegen
    if progress is None:
        progress = {
            "job_done": 0,
            "job_total": total,
            "job_start_time": time.time(),
        }
    else:
        # job_total wird bei der ersten Datei einmalig gesetzt
        if "job_total" not in progress or not progress["job_total"]:
            progress["job_total"] = total
        if "job_start_time" not in progress or not progress["job_start_time"]:
            progress["job_start_time"] = time.time()

    # 2) bestehende Ausgabedatei (falls vorhanden) einlesen
    existing_by_chunk: Dict[str, Dict[str, Any]] = {}
    existing_annotated = 0
    existing_annotated_cids: set[str] = set()

    if out_path.is_file():
        logging.info("Bestehende Ausgabedatei gefunden, nutze vorhandene Annotationen: %s", out_path)
        with out_path.open("r", encoding="utf-8") as f_old:
            for line in f_old:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec_old = json.loads(line)
                except json.JSONDecodeError:
                    continue
                cid_old = rec_old.get("chunk_id")
                if not cid_old:
                    continue
                existing_by_chunk[cid_old] = rec_old
                sem_old = rec_old.get("semantic") or {}
                if isinstance(sem_old, dict) and sem_old.get("trust_level"):
                    existing_annotated += 1
                    existing_annotated_cids.add(cid_old)

        if existing_annotated == total and len(existing_by_chunk) == total:
            logging.info(
                "Ausgabe bereits vollständig annotiert (%d Chunks) – überspringe Datei %s.",
                total,
                in_path.name,
            )
            # Den Fortschrittszähler trotzdem auf "fertig" setzen
            progress["job_done"] = progress.get("job_done", 0) + total
            return
        else:
            logging.info(
                "Bereits annotierte Chunks: %d/%d (%.1f%%)",
                existing_annotated,
                total,
                existing_annotated * 100.0 / total,
            )

    # 3) annotieren (neue Chunks) + vorhandene übernehmen
    annotated_new = 0
    start_time = time.time()

    # Helper zum Schreiben (ohne die Datei ständig neu zu öffnen)
    fout = out_path.open("w", encoding="utf-8")

    def _write_record(rec: Dict[str, Any]) -> None:
        """Einen Record als JSON-Linie in die Ausgabedatei schreiben."""
        fout.write(json.dumps(rec, ensure_ascii=False) + "\n")

    try:
        for idx, rec in enumerate(records):
            cid = rec.get("chunk_id")

            # 3a) Bereits vorhandener, vollständig annotierter Record → direkt übernehmen (kein LLM)
            if cid and cid in existing_annotated_cids:
                _write_record(existing_by_chunk[cid])
            else:
                # 3b) Neuer / noch nicht annotierter Record → LLM-Klassifikation
                content = rec.get("content", "")
                title = rec.get("title", "") or rec.get("doc_id", "")

                prev_text = records[idx - 1]["content"] if idx > 0 else None
                next_text = records[idx + 1]["content"] if idx + 1 < total else None

                semantic_meta: Dict[str, Any] = {
                    "mode": None,
                    "used_prev_next": bool(prev_text or next_text),
                    "used_faiss": False,
                    "faiss_neighbors": [],
                }
                empty_reasons: Dict[str, Optional[str]] = {
                    "content_type": None,
                    "domain": None,
                    "artifact_role": None,
                    "summary_short": None,
                }

                # ------------------------------------------------------------
                # RULE 2: Expand context for heading-only chunks
                # ------------------------------------------------------------
                meta = rec.get("meta") or {}
                is_heading = bool(meta.get("has_heading"))

                if is_heading and len(content.strip()) < 80:
                    # Wir hängen die nächsten 1–2 Chunks als Kontext an next_text an,
                    # damit das LLM den Abschnitt besser versteht.
                    context_parts: List[str] = []

                    # direkter Nachfolger
                    if idx + 1 < total:
                        context_parts.append(records[idx + 1].get("content", ""))

                    # noch ein weiterer danach
                    if idx + 2 < total:
                        context_parts.append(records[idx + 2].get("content", ""))

                    joined = "\n\n".join(p for p in context_parts if p)
                    if joined:
                        next_text = joined
                # ------------------------------------------------------------
                # Ende RULE 2 – ab hier haben Headings mehr Kontext im LLM-Prompt
                # ------------------------------------------------------------

                # ------------------------------------------------------------
                # RULE 1: Skip meaningless / structural chunks before LLM call
                # ------------------------------------------------------------
                import re

                text_clean = content.strip()
                is_heading = rec.get("meta", {}).get("has_heading", False)

                # A) Viel zu kurz → keine Information
                if len(text_clean) < 5:
                    llm_raw_struct = {
                        "language": "unknown",
                        "content_type": [],
                        "domain": [],
                        "artifact_role": ["structural"],
                        "trust_level": "low",
                        "summary_short": "",
                        "equations": [],
                        "key_quantities": [],
                        "chunk_role": ["heading"] if is_heading else [],
                    }
                    sem_norm = normalize_semantic_result(llm_raw_struct, taxonomies)

                    rec["language"] = sem_norm["language"]
                    sem_block = rec.get("semantic") or {}
                    sem_block.update(
                        {
                            "content_type": sem_norm["content_type"],
                            "domain": sem_norm["domain"],
                            "artifact_role": sem_norm["artifact_role"],
                            "trust_level": sem_norm["trust_level"],
                            "summary_short": sem_norm["summary_short"],
                            "equations": sem_norm["equations"],
                            "key_quantities": sem_norm["key_quantities"],
                        }
                    )
                    if taxonomies.get("chunk_role"):
                        sem_block["chunk_role"] = sem_norm["chunk_role"]

                    semantic_meta["mode"] = "structural_rule1_short"
                    semantic_meta["used_prev_next"] = False
                    empty_reasons["content_type"] = "structural_rule1"
                    empty_reasons["domain"] = "structural_rule1"
                    empty_reasons["summary_short"] = "structural_rule1"

                    meta_block = sem_block.get("meta") or {}
                    meta_block.update(semantic_meta)
                    meta_block["empty_reasons"] = empty_reasons
                    sem_block["meta"] = meta_block

                    rec["semantic"] = sem_block

                    _write_record(rec)
                    continue

                # B) Nur Zahlen / Punkte / Bindestriche → Kapitelnummern
                if re.fullmatch(r"[0-9.\- ]+", text_clean):
                    llm_raw_struct = {
                        "language": "unknown",
                        "content_type": [],
                        "domain": [],
                        "artifact_role": ["structural"],
                        "trust_level": "low",
                        "summary_short": "",
                        "equations": [],
                        "key_quantities": [],
                        "chunk_role": ["heading"] if is_heading else [],
                    }
                    sem_norm = normalize_semantic_result(llm_raw_struct, taxonomies)

                    rec["language"] = sem_norm["language"]
                    sem_block = rec.get("semantic") or {}
                    sem_block.update(
                        {
                            "content_type": sem_norm["content_type"],
                            "domain": sem_norm["domain"],
                            "artifact_role": sem_norm["artifact_role"],
                            "trust_level": sem_norm["trust_level"],
                            "summary_short": sem_norm["summary_short"],
                            "equations": sem_norm["equations"],
                            "key_quantities": sem_norm["key_quantities"],
                        }
                    )
                    if taxonomies.get("chunk_role"):
                        sem_block["chunk_role"] = sem_norm["chunk_role"]

                    semantic_meta["mode"] = "structural_rule1_numeric"
                    semantic_meta["used_prev_next"] = False
                    empty_reasons["content_type"] = "structural_rule1"
                    empty_reasons["domain"] = "structural_rule1"
                    empty_reasons["summary_short"] = "structural_rule1"

                    meta_block = sem_block.get("meta") or {}
                    meta_block.update(semantic_meta)
                    meta_block["empty_reasons"] = empty_reasons
                    sem_block["meta"] = meta_block

                    rec["semantic"] = sem_block

                    _write_record(rec)
                    continue

                # C) typische strukturelle Labels wie Figure 3.1, Table 2.4
                if re.match(r"^(Figure|Table|Fig\.|Tab\.)\s*\d", text_clean, re.IGNORECASE):
                    llm_raw_struct = {
                        "language": "unknown",
                        "content_type": [],
                        "domain": [],
                        "artifact_role": ["structural"],
                        "trust_level": "low",
                        "summary_short": "",
                        "equations": [],
                        "key_quantities": [],
                        "chunk_role": ["heading"] if is_heading else [],
                    }
                    sem_norm = normalize_semantic_result(llm_raw_struct, taxonomies)

                    rec["language"] = sem_norm["language"]
                    sem_block = rec.get("semantic") or {}
                    sem_block.update(
                        {
                            "content_type": sem_norm["content_type"],
                            "domain": sem_norm["domain"],
                            "artifact_role": sem_norm["artifact_role"],
                            "trust_level": sem_norm["trust_level"],
                            "summary_short": sem_norm["summary_short"],
                            "equations": sem_norm["equations"],
                            "key_quantities": sem_norm["key_quantities"],
                        }
                    )
                    if taxonomies.get("chunk_role"):
                        sem_block["chunk_role"] = sem_norm["chunk_role"]

                    semantic_meta["mode"] = "structural_rule1_label"
                    semantic_meta["used_prev_next"] = False
                    empty_reasons["content_type"] = "structural_rule1"
                    empty_reasons["domain"] = "structural_rule1"
                    empty_reasons["summary_short"] = "structural_rule1"

                    meta_block = sem_block.get("meta") or {}
                    meta_block.update(semantic_meta)
                    meta_block["empty_reasons"] = empty_reasons
                    sem_block["meta"] = meta_block

                    rec["semantic"] = sem_block

                    _write_record(rec)
                    continue

                # ------------------------------------------------------------
                # Ende RULE 1 (ab hier: LLM wird nur noch für echte Inhalte aufgerufen)
                # ------------------------------------------------------------

                llm_raw = classifier.classify_chunk(
                    text=content,
                    doc_title=title,
                    taxonomies=taxonomies,
                    prev_text=prev_text,
                    next_text=next_text,
                )

                if llm_raw is None:
                    # Chunk bleibt wie er ist
                    _write_record(rec)
                else:
                    semantic = normalize_semantic_result(llm_raw, taxonomies)

                    semantic_meta["mode"] = "llm"
                    if not semantic.get("content_type"):
                        empty_reasons["content_type"] = "llm_empty"
                    if not semantic.get("domain"):
                        empty_reasons["domain"] = "llm_empty"
                    if not semantic.get("artifact_role"):
                        empty_reasons["artifact_role"] = "llm_empty"
                    if not semantic.get("summary_short"):
                        empty_reasons["summary_short"] = "llm_empty"

                    # DEFAULT artifact_role für strukturelle Chunks (Ticket 3)
                    meta = rec.get("meta") or {}
                    ar_list = list(semantic.get("artifact_role") or [])
                    if meta.get("has_heading") and "heading" in allowed_artifact_role:
                        if "heading" not in ar_list:
                            ar_list.append("heading")
                    if meta.get("has_table") and "table" in allowed_artifact_role:
                        if "table" not in ar_list:
                            ar_list.append("table")
                    # Nur gültige Taxonomie-IDs weiterreichen
                    semantic["artifact_role"] = [r for r in ar_list if r in allowed_artifact_role]

                    # RULE 4: summary_short bei strukturellen / schwachen Chunks unterdrücken
                    text_clean = content.strip()
                    if meta.get("has_heading") or meta.get("has_table") or len(text_clean) < 40:
                        if len(semantic.get("summary_short", "")) < 20:
                            semantic["summary_short"] = ""
                            empty_reasons["summary_short"] = "rule4_suppressed"

                    # semantic an den Record hängen
                    existing_sem = rec.get("semantic") or {}
                    if not isinstance(existing_sem, dict):
                        existing_sem = {}

                    # Felder zusammenführen (semantic kann schon content_type/domain enthalten, falls vorher
                    # heuristisch gesetzt wurde; wir überschreiben gezielt oder ergänzen sinnvoll)
                    merged_sem = dict(existing_sem)
                    for key in ["language", "content_type", "domain", "artifact_role", "trust_level"]:
                        merged_sem[key] = semantic.get(key, merged_sem.get(key))

                    merged_sem["summary_short"] = semantic.get("summary_short", merged_sem.get("summary_short", ""))

                    merged_sem["equations"] = semantic.get("equations", merged_sem.get("equations", []))
                    merged_sem["key_quantities"] = semantic.get("key_quantities", merged_sem.get("key_quantities", []))

                    if semantic.get("chunk_role"):
                        merged_sem["chunk_role"] = semantic["chunk_role"]

                    meta_block = merged_sem.get("meta") or {}
                    meta_block.update(semantic_meta)
                    meta_block["empty_reasons"] = empty_reasons
                    merged_sem["meta"] = meta_block

                    rec["semantic"] = merged_sem

                    _write_record(rec)
                    annotated_new += 1

            # Fortschritt + ETA loggen (jobweit, nicht nur pro Datei)
            job_done = int(progress.get("job_done", 0)) if progress is not None else idx + 1
            job_total = int(progress.get("job_total", total)) if progress is not None else total
            job_start = float(progress.get("job_start_time", start_time)) if progress is not None else start_time

            elapsed = time.time() - job_start
            frac = job_done / job_total if job_total > 0 else 0.0

            if frac > 0:
                est_total = elapsed / frac
                remaining = max(0.0, est_total - elapsed)
                eta_dt = datetime.now() + timedelta(seconds=remaining)
                eta_str = eta_dt.strftime("%Y-%m-%d %H:%M:%S")
            else:
                eta_str = "unknown"

            logging.info(
                "[JOB] progress: %d/%d (%.1f%%) elapsed %.1fs, ETA %s",
                job_done,
                job_total,
                frac * 100.0,
                elapsed,
                eta_str,
            )

            if progress is not None:
                progress["job_done"] = job_done

    finally:
        fout.close()

    logging.info(
        "Fertig: %s (Chunks gesamt: %d, vorhandene: %d, neu annotiert: %d)",
        in_path.name,
        total,
        len(existing_by_chunk),
        annotated_new,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Semantische Anreicherung normalisierter JSONL-Chunks per LLM (Ollama)."
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        default=str(get_path("normalized_json")),
        help="Eingabeverzeichnis mit JSONL-Dateien (normalized/json).",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(get_path("semantic_json")),
        help="Ausgabeverzeichnis für angereicherte JSONL-Dateien (semantic/json).",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=str(LLM_CONFIG_PATH),
        help="Pfad zu semantic_llm.json (LLM-Konfiguration).",
    )
    parser.add_argument(
        "--limit-files",
        type=int,
        default=None,
        help="Optional: Anzahl Eingabedateien begrenzen (Debug).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Mehr Logging ausgeben.",
    )
    parser.add_argument(
        "--num-shards",
        type=int,
        default=1,
        help="Gesamtzahl der Shards (Array-Jobs).",
    )
    parser.add_argument(
        "--shard-id",
        type=int,
        default=0,
        help="Shard-Index dieses Jobs (0-basiert).",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    input_dir = Path(args.input_dir).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve()
    llm_config_path = Path(args.config).expanduser().resolve()

    if not input_dir.is_dir():
        raise SystemExit(f"Eingabeverzeichnis existiert nicht: {input_dir}")

    if not llm_config_path.is_file():
        raise SystemExit(f"LLM-Konfigurationsdatei fehlt: {llm_config_path}")

    if args.num_shards < 1:
        raise SystemExit(f"--num-shards muss >= 1 sein, erhalten: {args.num_shards}")
    if args.shard_id < 0 or args.shard_id >= args.num_shards:
        raise SystemExit(
            f"--shard-id muss im Bereich [0, {args.num_shards - 1}] liegen, erhalten: {args.shard_id}"
        )

    llm_config = load_json_file(llm_config_path)
    taxonomies = load_taxonomies()
    classifier = LLMSemanticClassifier(llm_config)

    logging.info("Input : %s", input_dir)
    logging.info("Output: %s", output_dir)
    logging.info("LLM   : %s @ %s", classifier.model, classifier.base_url)

    # Vollständige Dateiliste
    files_all = sorted(input_dir.glob("*.jsonl"))
    if args.limit_files is not None:
        files_all = files_all[: args.limit_files]

    if not files_all:
        logging.warning("Keine JSONL-Dateien in %s gefunden.", input_dir)
        return

    # Sharding anwenden: einfacher Modulo-Split über den Index
    if args.num_shards == 1:
        files = files_all
    else:
        files = [
            f
            for idx, f in enumerate(files_all)
            if idx % args.num_shards == args.shard_id
        ]

    logging.info(
        "Sharding-Konfiguration: num_shards=%d, shard_id=%d, files_total=%d, files_in_this_shard=%d",
        args.num_shards,
        args.shard_id,
        len(files_all),
        len(files),
    )

    if not files:
        logging.warning(
            "Shard %d hat keine Dateien zu verarbeiten (num_shards=%d, files_total=%d).",
            args.shard_id,
            args.num_shards,
            len(files_all),
        )
        return

    output_dir.mkdir(parents=True, exist_ok=True)

    # globales Fortschrittsobjekt für den ganzen Job
    job_total = len(files_all)
    progress = {
        "job_done": 0,
        "job_total": job_total,
        "job_start_time": time.time(),
    }

    for in_file in files:
        rel = in_file.name
        out_file = output_dir / rel
        process_file(in_file, out_file, classifier, taxonomies, progress)

    logging.info("Semantische Anreicherung abgeschlossen.")


if __name__ == "__main__":
    main()
