#!/usr/bin/env python
"""
annotate_semantics.py

Schritt 2 der Pipeline: normalisierte Chunks (normalized/json/*.jsonl)
werden per LLM (Ollama) semantisch annotiert:

- content_type  (Liste von IDs aus config/taxonomy/content_type.json)
- domain        (Liste von IDs aus config/taxonomy/domain.json)
- artifact_role (Liste von IDs aus config/taxonomy/artifact_role.json)
- trust_level   (eine ID aus config/taxonomy/trust_level.json)
- chunk_role    (optionale pädagogische Rolle des Chunks: definition, example, ...)
- language      (de/en/mixed/unknown)

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
"""

import argparse
import json
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
from config.paths.paths_utils import get_path

import requests

# ---------------------------------------------------------------------------
# Pfade / Taxonomie laden
# ---------------------------------------------------------------------------

THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parent
TAXONOMY_DIR = REPO_ROOT / "config" / "taxonomy"
LLM_CONFIG_PATH = REPO_ROOT / "config" / "LLM" / "semantic_llm.json"


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
    Dünner Wrapper um Ollama /api/chat für unsere Klassifikationsaufgabe.
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
            "Your job is to assign semantic tags from a fixed taxonomy.\n\n"
            "You MUST respond with a single JSON object only. No explanations, "
            "no markdown, no surrounding text."
        )

        # Basis-User-Prompt
        user_prompt = f"""
We have a text CHUNK from a larger document.

Document title: "{doc_title}"

MAIN CHUNK TEXT:
\"\"\"{text}\"\"\"
"""

        # Nachbar-Kontext optional einfügen
        if prev_text or next_text:
            user_prompt += "\nNEIGHBORING CONTEXT (for orientation, do NOT classify these separately):\n"
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

        # Output-Schema
        user_prompt += """

OUTPUT FORMAT:
Return EXACTLY one JSON object with keys:
  "language": string,
  "content_type": list of strings,
  "domain": list of strings,
  "artifact_role": list of strings,
  "trust_level": string
"""

        if chunk_role_block:
            user_prompt += '  "chunk_role": list of strings\n'

        user_prompt += """

Example (schema only, NOT the real answer):
{
  "language": "de",
  "content_type": ["textbook"],
  "domain": ["thermodynamics"],
  "artifact_role": ["statement"],
  "trust_level": "high"
}

Now produce the JSON classification for the MAIN CHUNK.
"""

        # Ollama-Payload mit JSON-Mode + num_predict
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": self.temperature,
            "stream": False,
            "format": "json",  # zwingt das Modell, valides JSON auszugeben
            "options": {
                "num_predict": self.max_tokens,  # genug Platz, damit JSON nicht abgeschnitten wird
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

        return self._safe_parse_json(content)

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
    """
    allowed_content_type = set(extract_ids(taxonomies["content_type"]))
    allowed_domain = set(extract_ids(taxonomies["domain"]))
    allowed_artifact_role = set(extract_ids(taxonomies["artifact_role"]))
    allowed_trust_level = set(extract_ids(taxonomies["trust_level"]))
    allowed_chunk_role = set(extract_ids(taxonomies.get("chunk_role", [])))

    def as_list(value) -> List[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        if isinstance(value, list):
            return [str(v) for v in value]
        return []

    # Sprache normieren
    language = str(raw.get("language", "unknown")).lower()
    if language not in {"de", "en", "mixed", "unknown"}:
        language = "unknown"

    # Taxonomie-Listen filtern
    ct = [v for v in as_list(raw.get("content_type")) if v in allowed_content_type]
    dom = [v for v in as_list(raw.get("domain")) if v in allowed_domain]
    ar = [v for v in as_list(raw.get("artifact_role")) if v in allowed_artifact_role]
    cr = [v for v in as_list(raw.get("chunk_role")) if v in allowed_chunk_role]

    # trust_level: genau eins, sonst Fallback
    tl_raw = str(raw.get("trust_level", "")).strip()
    trust = tl_raw if tl_raw in allowed_trust_level else None
    if trust is None:
        # Fallback: "medium", falls vorhanden, sonst erster Eintrag
        if "medium" in allowed_trust_level:
            trust = "medium"
        else:
            trust = next(iter(allowed_trust_level)) if allowed_trust_level else "unknown"

    # Begrenze Anzahl pro Liste (sicherheitshalber)
    ct = ct[:2]
    dom = dom[:3]
    ar = ar[:3]
    cr = cr[:2]

    return {
        "language": language,
        "content_type": ct,
        "domain": dom,
        "artifact_role": ar,
        "trust_level": trust,
        "chunk_role": cr,
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

    logging.info("Chunks in Datei %s: %d", in_path.name, total)

    # 2) bestehende Ausgabedatei (falls vorhanden) einlesen
    existing_by_chunk: Dict[str, Dict[str, Any]] = {}
    existing_annotated = 0

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

        if existing_annotated == total and len(existing_by_chunk) == total:
            logging.info(
                "Ausgabe bereits vollständig annotiert (%d Chunks) – überspringe Datei %s.",
                total,
                in_path.name,
            )
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
        for idx, rec in enumerate(records):
            cid = rec.get("chunk_id")

            # 3a) Bereits vorhandener Record → direkt übernehmen (kein LLM)
            if cid and cid in existing_by_chunk:
                fout.write(json.dumps(existing_by_chunk[cid], ensure_ascii=False) + "\n")
            else:
                # 3b) Neuer / noch nicht annotierter Record → LLM-Klassifikation
                content = rec.get("content", "")
                title = rec.get("title", "") or rec.get("doc_id", "")

                prev_text = records[idx - 1]["content"] if idx > 0 else None
                next_text = records[idx + 1]["content"] if idx + 1 < total else None

                llm_raw = classifier.classify_chunk(
                    text=content,
                    doc_title=title,
                    taxonomies=taxonomies,
                    prev_text=prev_text,
                    next_text=next_text,
                )

                if llm_raw is None:
                    # Chunk bleibt wie er ist
                    fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
                else:
                    semantic = normalize_semantic_result(llm_raw, taxonomies)

                    # language auf oberster Ebene ebenfalls setzen
                    lang_existing = rec.get("language")
                    if not lang_existing or lang_existing == "unknown":
                        rec["language"] = semantic["language"]

                    # semantic-Block im Record aktualisieren
                    sem_block = rec.get("semantic") or {}
                    sem_block.update(
                        {
                            "content_type": semantic["content_type"],
                            "domain": semantic["domain"],
                            "artifact_role": semantic["artifact_role"],
                            "trust_level": semantic["trust_level"],
                        }
                    )
                    # chunk_role nur schreiben, wenn Taxonomie existiert
                    if taxonomies.get("chunk_role"):
                        sem_block["chunk_role"] = semantic["chunk_role"]

                    rec["semantic"] = sem_block

                    fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    annotated_new += 1

            # Fortschritt + ETA loggen
            processed = idx + 1
            elapsed = time.time() - start_time
            frac = processed / total if total > 0 else 0.0

            if frac > 0:
                est_total = elapsed / frac
                remaining = max(0.0, est_total - elapsed)
                eta_dt = datetime.now() + timedelta(seconds=remaining)
                eta_str = eta_dt.strftime("%Y-%m-%d %H:%M:%S")
            else:
                eta_str = "unknown"

            logging.info(
                "[%d/%d] (%.1f%%) elapsed %.1fs, ETA %s",
                processed,
                total,
                frac * 100.0,
                elapsed,
                eta_str,
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

    llm_config = load_json_file(llm_config_path)
    taxonomies = load_taxonomies()
    classifier = LLMSemanticClassifier(llm_config)

    logging.info("Input : %s", input_dir)
    logging.info("Output: %s", output_dir)
    logging.info("LLM   : %s @ %s", classifier.model, classifier.base_url)

    files = sorted(input_dir.glob("*.jsonl"))
    if args.limit_files is not None:
        files = files[: args.limit_files]

    if not files:
        logging.warning("Keine JSONL-Dateien in %s gefunden.", input_dir)
        return

    for in_file in files:
        rel = in_file.name
        out_file = output_dir / rel
        process_file(in_file, out_file, classifier, taxonomies)

    logging.info("Semantische Anreicherung abgeschlossen.")


if __name__ == "__main__":#!/usr/bin/env python
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
    - summary_short  (kurze, 2–3-sätzige Chunk-Zusammenfassung als String)
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
    """

import argparse
import json
import logging
import os
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional

import requests

# ---------------------------------------------------------------------------
# Pfade / Taxonomie laden
# ---------------------------------------------------------------------------

THIS_DIR = Path(__file__).resolve().parent
REPO_ROOT = THIS_DIR.parent
TAXONOMY_DIR = REPO_ROOT / "config" / "taxonomy"
LLM_CONFIG_PATH = REPO_ROOT / "config" / "LLM" / "semantic_llm.json"


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
    Dünner Wrapper um Ollama /api/chat für unsere Klassifikationsaufgabe.
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
            "no markdown, no surrounding text."
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

        # Ollama-Payload mit JSON-Mode + num_predict
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": self.temperature,
            "stream": False,
            "format": "json",  # zwingt das Modell, valides JSON auszugeben
            "options": {
                "num_predict": self.max_tokens,  # genug Platz, damit JSON nicht abgeschnitten wird
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

        return self._safe_parse_json(content)

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
    allowed_content_type = set(extract_ids(taxonomies["content_type"]))
    allowed_domain = set(extract_ids(taxonomies["domain"]))
    allowed_artifact_role = set(extract_ids(taxonomies["artifact_role"]))
    allowed_trust_level = set(extract_ids(taxonomies["trust_level"]))
    allowed_chunk_role = set(extract_ids(taxonomies.get("chunk_role", [])))

    def as_list(value) -> List[str]:
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        if isinstance(value, list):
            return [str(v) for v in value]
        return []

    # Sprache normieren
    language = str(raw.get("language", "unknown")).lower()
    if language not in {"de", "en", "mixed", "unknown"}:
        language = "unknown"

    # Taxonomie-Listen filtern
    ct = [v for v in as_list(raw.get("content_type")) if v in allowed_content_type]
    dom = [v for v in as_list(raw.get("domain")) if v in allowed_domain]
    ar = [v for v in as_list(raw.get("artifact_role")) if v in allowed_artifact_role]
    cr = [v for v in as_list(raw.get("chunk_role")) if v in allowed_chunk_role]

    # trust_level: genau eins, sonst Fallback
    tl_raw = str(raw.get("trust_level", "")).strip()
    trust = tl_raw if tl_raw in allowed_trust_level else None
    if trust is None:
        # Fallback: "medium", falls vorhanden, sonst erster Eintrag
        if "medium" in allowed_trust_level:
            trust = "medium"
        else:
            trust = next(iter(allowed_trust_level)) if allowed_trust_level else "unknown"

    # Begrenze Anzahl pro Liste (sicherheitshalber)
    ct = ct[:2]
    dom = dom[:3]
    ar = ar[:3]
    cr = cr[:2]

    # summary_short: einfacher String, kein Taxonomie-Feld
    summary_raw = raw.get("summary_short", "")
    if summary_raw is None:
        summary_short = ""
    else:
        summary_short = str(summary_raw).strip()

    # key_quantities: Liste von Strings, frei, aber sauber normalisiert
    key_quantities = as_list(raw.get("key_quantities"))

    # equations: Liste von Objekten, minimale Formattoleranz
    equations_raw = raw.get("equations")
    if isinstance(equations_raw, list):
        # sicherstellen, dass jeder Eintrag ein Dict ist (sonst droppen)
        equations: List[Dict[str, Any]] = []
        for eq in equations_raw:
            if isinstance(eq, dict):
                equations.append(eq)
            else:
                # wenn z. B. nur ein String kam, wrappe ihn minimal
                equations.append({"description": str(eq)})
    else:
        equations = []

    return {
        "language": language,
        "content_type": ct,
        "domain": dom,
        "artifact_role": ar,
        "trust_level": trust,
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

    logging.info("Chunks in Datei %s: %d", in_path.name, total)

    # 2) bestehende Ausgabedatei (falls vorhanden) einlesen
    existing_by_chunk: Dict[str, Dict[str, Any]] = {}
    existing_annotated = 0

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

        if existing_annotated == total and len(existing_by_chunk) == total:
            logging.info(
                "Ausgabe bereits vollständig annotiert (%d Chunks) – überspringe Datei %s.",
                total,
                in_path.name,
            )
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
        for idx, rec in enumerate(records):
            cid = rec.get("chunk_id")

            # 3a) Bereits vorhandener Record → direkt übernehmen (kein LLM)
            if cid and cid in existing_by_chunk:
                fout.write(json.dumps(existing_by_chunk[cid], ensure_ascii=False) + "\n")
            else:
                # 3b) Neuer / noch nicht annotierter Record → LLM-Klassifikation
                content = rec.get("content", "")
                title = rec.get("title", "") or rec.get("doc_id", "")

                prev_text = records[idx - 1]["content"] if idx > 0 else None
                next_text = records[idx + 1]["content"] if idx + 1 < total else None

                llm_raw = classifier.classify_chunk(
                    text=content,
                    doc_title=title,
                    taxonomies=taxonomies,
                    prev_text=prev_text,
                    next_text=next_text,
                )

                if llm_raw is None:
                    # Chunk bleibt wie er ist
                    fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
                else:
                    semantic = normalize_semantic_result(llm_raw, taxonomies)

                    # language auf oberster Ebene ebenfalls setzen
                    lang_existing = rec.get("language")
                    if not lang_existing or lang_existing == "unknown":
                        rec["language"] = semantic["language"]

                    # semantic-Block im Record aktualisieren
                    sem_block = rec.get("semantic") or {}
                    sem_block.update(
                        {
                            "content_type": semantic["content_type"],
                            "domain": semantic["domain"],
                            "artifact_role": semantic["artifact_role"],
                            "trust_level": semantic["trust_level"],
                            "summary_short": semantic["summary_short"],
                            "equations": semantic["equations"],
                            "key_quantities": semantic["key_quantities"],
                        }
                    )
                    # chunk_role nur schreiben, wenn Taxonomie existiert
                    if taxonomies.get("chunk_role"):
                        sem_block["chunk_role"] = semantic["chunk_role"]

                    rec["semantic"] = sem_block

                    fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    annotated_new += 1

            # Fortschritt + ETA loggen
            processed = idx + 1
            elapsed = time.time() - start_time
            frac = processed / total if total > 0 else 0.0

            if frac > 0:
                est_total = elapsed / frac
                remaining = max(0.0, est_total - elapsed)
                eta_dt = datetime.now() + timedelta(seconds=remaining)
                eta_str = eta_dt.strftime("%Y-%m-%d %H:%M:%S")
            else:
                eta_str = "unknown"

            logging.info(
                "[%d/%d] (%.1f%%) elapsed %.1fs, ETA %s",
                processed,
                total,
                frac * 100.0,
                elapsed,
                eta_str,
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

    llm_config = load_json_file(llm_config_path)
    taxonomies = load_taxonomies()
    classifier = LLMSemanticClassifier(llm_config)

    logging.info("Input : %s", input_dir)
    logging.info("Output: %s", output_dir)
    logging.info("LLM   : %s @ %s", classifier.model, classifier.base_url)

    files = sorted(input_dir.glob("*.jsonl"))
    if args.limit_files is not None:
        files = files[: args.limit_files]

    if not files:
        logging.warning("Keine JSONL-Dateien in %s gefunden.", input_dir)
        return

    for in_file in files:
        rel = in_file.name
        out_file = output_dir / rel
        process_file(in_file, out_file, classifier, taxonomies)

    logging.info("Semantische Anreicherung abgeschlossen.")


if __name__ == "__main__":
    main()

    main()
