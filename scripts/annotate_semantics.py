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

Wichtige Aspekte:
- robustes Error-Handling (HTTP-Ausfälle, JSON-Parsing, etc.)
- Wiederaufnahme: falls semantic/json/*.jsonl bereits existiert, werden nur
  fehlende Chunks ergänzt (über chunk_id + trust_level).
- Headings, Tabellen, extrem kurze/strukturierte Chunks werden heuristisch
  behandelt, ggf. ohne LLM-Aufruf.
"""

from __future__ import annotations

import sys
from pathlib import Path

import argparse
import json
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
import importlib.util

import requests

# Pfadberechnung:
# Wir gehen davon aus, dass dieses Skript unter REPO_ROOT/scripts/ liegt.
# Dann ist REPO_ROOT = dieses_file.parent.parent
THIS_FILE = Path(__file__).resolve()
REPO_ROOT = THIS_FILE.parent.parent

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
    Lädt die Taxonomie-Dateien aus config/taxonomy.

    Erwartete Dateien:
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


def load_llm_config() -> Dict[str, Any]:
    """Lädt die LLM-Konfiguration aus config/LLM/semantic_llm.json."""
    return load_json_file(LLM_CONFIG_PATH)


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
        # Robustheit: Timeout + Retries für Ollama-Calls
        self.request_timeout_s = float(config.get("request_timeout_s", 120))
        self.max_retries = int(config.get("max_retries", 3))
        self.retry_backoff_s = float(config.get("retry_backoff_s", 5.0))

    def classify_chunk(
        self,
        text: str,
        doc_title: str,
        taxonomies: Dict[str, List[Dict[str, Any]]],
        prev_text: Optional[str] = None,
        next_text: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Führt einen Klassifikations-/Anreicherungs-Call an das LLM durch
        und erwartet als Antwort ein JSON-Objekt.

        Gibt im Erfolgsfall ein Dict zurück, sonst None (Fehler-Logging).
        """
        # Text ggf. hart begrenzen
        if len(text) > self.max_chars:
            text = text[: self.max_chars]

        def fmt_list(name: str) -> str:
            """Hilfsfunktion, um Taxonomie-Listen als 'id: desc' auszugeben."""
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
            "format": "json",
            "options": {
                "num_predict": self.max_tokens,
            },
        }

        url = self.base_url + "/api/chat"

        last_err: Optional[Exception] = None
        resp = None  # type: ignore[assignment]
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = requests.post(url, json=payload, timeout=self.request_timeout_s)
                resp.raise_for_status()
                last_err = None
                break
            except Exception as e:
                last_err = e
                if attempt < self.max_retries:
                    sleep_s = self.retry_backoff_s * attempt
                    logging.warning(
                        "LLM-Request failed (attempt %d/%d): %s – retry in %.1fs",
                        attempt,
                        self.max_retries,
                        e,
                        sleep_s,
                    )
                    time.sleep(sleep_s)

        if last_err is not None:
            logging.error("LLM-Request failed (final): %s", last_err)
            return None

        try:
            data = resp.json()
            content = data.get("message", {}).get("content", "")
        except Exception as e:
            logging.error("Failed to parse LLM JSON response: %s", e)
            return None

        # Der Response-Body sollte bereits ein gültiges JSON-Objekt (dict) sein,
        # weil wir format=json gesetzt haben. Fallback: falls content nur ein
        # JSON-String ist, versuchen wir diesen zu parsen.
        if isinstance(content, dict):
            return content

        if isinstance(content, str):
            try:
                obj = json.loads(content)
                if isinstance(obj, dict):
                    return obj
            except Exception:
                pass

        # Fallback: falls das Modell trotz format=json zusätzlich Text drumherum
        # schreibt, versuchen wir, die erste JSON-Objekt-Klammerung zu finden.
        text = str(content)
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
    allowed_content_type = set(extract_ids(taxonomies["content_type"]))
    allowed_domain = set(extract_ids(taxonomies["domain"]))
    allowed_artifact_role = set(extract_ids(taxonomies["artifact_role"]))
    allowed_trust_level = set(extract_ids(taxonomies["trust_level"]))

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
            if max_len is not None and len(out) >= max_len:
                break
        return out

    ct = filter_list("content_type", allowed_content_type, max_len=2)
    dom = filter_list("domain", allowed_domain, max_len=3)
    ar = filter_list("artifact_role", allowed_artifact_role, max_len=3)
    cr = filter_list("chunk_role", set(extract_ids(taxonomies.get("chunk_role", []))), max_len=2)

    trust = raw.get("trust_level")
    if isinstance(trust, str) and trust in allowed_trust_level:
        trust_str = trust
    else:
        trust_str = "medium"

    summary_short = raw.get("summary_short", "")
    if not isinstance(summary_short, str):
        summary_short = ""

    # equations: Liste von Objekten, wir vertrauen hier weitgehend dem Modell
    equations_raw = raw.get("equations", [])
    equations: List[Dict[str, Any]] = []
    if isinstance(equations_raw, list):
        for eq in equations_raw:
            if not isinstance(eq, dict):
                continue
            latex = eq.get("latex", "")
            desc = eq.get("description", "")
            vars_raw = eq.get("variables", [])
            vars_norm = []
            if isinstance(vars_raw, list):
                for v in vars_raw:
                    if not isinstance(v, dict):
                        continue
                    vars_norm.append(
                        {
                            "symbol": str(v.get("symbol", "")),
                            "name": str(v.get("name", "")),
                            "unit": str(v.get("unit", "")),
                        }
                    )
            equations.append(
                {
                    "latex": str(latex),
                    "description": str(desc),
                    "variables": vars_norm,
                }
            )

    key_quantities_raw = raw.get("key_quantities", [])
    key_quantities: List[str] = []
    if isinstance(key_quantities_raw, list):
        for v in key_quantities_raw:
            key_quantities.append(str(v))

    return {
        "language": language,
        "content_type": ct,
        "domain": dom,
        "artifact_role": ar,
        "trust_level": trust_str,
        "chunk_role": cr,
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

    logging.info("Chunks in Datei %s: %d", in_path.name, total)

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
                cid = rec_old.get("chunk_id")
                if not cid:
                    continue
                existing_by_chunk[cid] = rec_old
                sem = rec_old.get("semantic") or {}
                if isinstance(sem, dict) and sem.get("trust_level"):
                    existing_annotated += 1
                    existing_annotated_cids.add(cid)

        if existing_annotated == total and len(existing_by_chunk) == total:
            logging.info(
                "Ausgabe bereits vollständig annotiert (%d Chunks) – überspringe Datei %s.",
                total,
                in_path.name,
            )
            if progress is not None:
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

    with out_path.open("w", encoding="utf-8") as fout:

        def _write_record(obj: Dict[str, Any]) -> None:
            fout.write(json.dumps(obj, ensure_ascii=False) + "\n")
            if progress is not None:
                progress["job_done"] = progress.get("job_done", 0) + 1

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

                # ------------------------------------------------------------
                # RULE 2: Expand context for heading-only chunks
                # ------------------------------------------------------------
                meta = rec.get("meta") or {}
                is_heading = bool(meta.get("has_heading"))
                text_clean = content.strip()

                if is_heading and len(text_clean) < 80:
                    context_parts: List[str] = []

                    # nächster Chunk
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
                "[job %d/%d] (%.1f%%) elapsed %.1fs, ETA %s (file %s %d/%d)",
                job_done,
                job_total,
                frac * 100.0,
                elapsed,
                eta_str,
                in_path.name,
                idx + 1,
                total,
            )

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
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Log-Level (Standard: INFO).",
    )
    parser.add_argument(
        "--only-file",
        type=str,
        default=None,
        help="Optional: Nur diese eine Datei (Name) verarbeiten (Filter auf input-dir).",
    )
    parser.add_argument(
        "--shard-id",
        type=int,
        default=None,
        help="Optional: Shard-ID (0-basiert) für parallele Verarbeitung.",
    )
    parser.add_argument(
        "--num-shards",
        type=int,
        default=None,
        help="Optional: Anzahl Shards für parallele Verarbeitung. "
        "Files werden deterministisch auf Shards aufgeteilt.",
    )

    args = parser.parse_args()

    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(message)s",
        stream=sys.stdout,
    )

    # Taxonomien + LLM-Konfig laden
    logging.info("Lade Taxonomien aus %s", TAXONOMY_DIR)
    taxonomies = load_taxonomies()

    logging.info("Lade LLM-Konfiguration aus %s", LLM_CONFIG_PATH)
    llm_config = load_llm_config()

    classifier = LLMSemanticClassifier(llm_config)

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)

    if not input_dir.is_dir():
        logging.error("Input-Verzeichnis existiert nicht: %s", input_dir)
        sys.exit(1)

    output_dir.mkdir(parents=True, exist_ok=True)

    # Alle JSONL-Dateien im input_dir einsammeln
    files_all = sorted(p for p in input_dir.glob("*.jsonl") if p.is_file())

    if args.only_file:
        files_all = [p for p in files_all if p.name == args.only_file]
        if not files_all:
            logging.error("Keine Datei '%s' im Eingabeverzeichnis gefunden.", args.only_file)
            sys.exit(1)

    # Sharding (einfaches Round-Robin über die sortierte Liste)
    if args.shard_id is not None and args.num_shards is not None:
        shard_id = args.shard_id
        num_shards = args.num_shards
        if shard_id < 0 or num_shards <= 0 or shard_id >= num_shards:
            logging.error("Ungültige Shard-Konfiguration: shard_id=%d, num_shards=%d", shard_id, num_shards)
            sys.exit(1)
        files = [f for i, f in enumerate(files_all) if i % num_shards == shard_id]
        logging.info(
            "Shard %d/%d: Verarbeite %d Dateien (von gesamt %d).",
            shard_id,
            num_shards,
            len(files),
            len(files_all),
        )
    else:
        files = files_all
        logging.info("Verarbeite %d Dateien ohne Sharding.", len(files))

    if not files:
        logging.warning(
            "Keine Dateien zu verarbeiten. (input_dir=%s, only_file=%s, shard_id=%s, num_shards=%s)",
            input_dir,
            args.only_file,
            args.shard_id,
            args.num_shards,
        )
        return

    # Job-weiter Fortschritt (nur für diesen Shard / diesen SLURM-Task)
    job_total = 0
    for p in files:
        try:
            with p.open("r", encoding="utf-8") as f:
                job_total += sum(1 for line in f if line.strip())
        except Exception:
            # Fehler wird später in process_file geloggt; hier nur best effort.
            continue

    if job_total <= 0:
        # Fallback: zumindest Anzahl Dateien verwenden, damit ETA nicht crasht
        job_total = len(files)

    progress: Dict[str, Any] = {
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
