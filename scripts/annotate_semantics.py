#!/usr/bin/env python
"""
annotate_semantics.py

Schritt 2 der Pipeline: normalisierte Chunks (normalized/json/*.jsonl)
werden per LLM (Ollama) semantisch annotiert.

Ziele der Anreicherung:
- Taxonomie-Klassifikation:
  - content_type   (Liste von IDs aus config/taxonomy/content_type.json)
  - domain         (Liste von IDs aus config/taxonomy/domain.json)
  - artifact_role  (Liste von IDs aus config/taxonomy/artifact_role.json)
  - trust_level    (eine ID aus config/taxonomy/trust_level.json)
  - chunk_role     (0–2 IDs aus config/taxonomy/chunk_role.json, z.B. definition/derivation/example/…)

- Metadaten:
  - language       (de/en/mixed/unknown, zusätzlich auch auf oberster Ebene gesetzt)

- Inhaltliche Verdichtung (für Q&A-Generierung):
  - summary    : kurze technische Zusammenfassung des Chunk-Inhalts
  - key_facts  : Liste zentraler Aussagen/Formeln/Fakten
  - tags       : kurze thematische Tags (frei, keine Taxonomie)

Nachbar-Kontext:
- Für die Klassifikation eines Fokus-Chunks werden optional Ausschnitte
  aus dem vorherigen und dem nächsten Chunk als Kontext mitgegeben
  (CONTEXT_BEFORE / CONTEXT_AFTER), um Ableitungen / Definitionen besser
  zu verstehen. Klassifiziert wird immer nur der Fokus-Chunk.

Ergebnis wird als identische JSONL-Struktur in semantic/json/ geschrieben,
nur mit gefülltem "semantic"-Block und ggf. aktualisiertem "language"-Feld.
"""

import argparse
import json
import logging
import os
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
    if not path.is_file():
        raise FileNotFoundError(f"Datei nicht gefunden: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_taxonomies() -> Dict[str, List[Dict[str, Any]]]:
    """
    Lädt alle Taxonomien:
      - content_type
      - domain
      - artifact_role
      - trust_level
      - chunk_role
    """
    taxonomies = {
        "content_type": load_json_file(TAXONOMY_DIR / "content_type.json"),
        "domain": load_json_file(TAXONOMY_DIR / "domain.json"),
        "artifact_role": load_json_file(TAXONOMY_DIR / "artifact_role.json"),
        "trust_level": load_json_file(TAXONOMY_DIR / "trust_level.json"),
        "chunk_role": load_json_file(TAXONOMY_DIR / "chunk_role.json"),
    }
    return taxonomies


def extract_ids(tax_list: List[Dict[str, Any]]) -> List[str]:
    return [str(entry["id"]) for entry in tax_list if "id" in entry]


# ---------------------------------------------------------------------------
# LLM-Client (Ollama /api/chat)
# ---------------------------------------------------------------------------

class LLMSemanticClassifier:
    """
    Kapselt den Zugriff auf das Ollama-/api/chat-Interface.

    Konfig-Parameter (semantic_llm.json):
      - endpoint          : Basis-URL (z.B. "http://localhost:11434")
      - model             : Modell-ID (z.B. "llama3.1:8b")
      - temperature       : Sampling-Temperatur
      - max_tokens        : (aktuell nur informativ, da Ollama das selbst handhabt)
      - max_chars         : max. Anzahl Zeichen des Fokus-Chunks
      - max_context_chars : max. Anzahl Zeichen je Kontext-Snippet (vorher/nachher)
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
        self.max_tokens = int(config.get("max_tokens", 256))
        # max_chars begrenzt den übergebenen Fokus-Chunk
        self.max_chars = int(config.get("max_chars", 4000))
        # separate Begrenzung für Kontext vor/nach dem Chunk
        self.max_context_chars = int(config.get("max_context_chars", 800))

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

        Erwartete Felder in der Antwort:
          - language: string ("de"/"en"/"mixed"/"unknown")
          - content_type: list[str] (Taxonomie-IDs)
          - domain: list[str] (Taxonomie-IDs)
          - artifact_role: list[str] (Taxonomie-IDs)
          - trust_level: string (Taxonomie-ID)
          - chunk_role: list[str] (Taxonomie-IDs)
          - summary: string (kurze technische Zusammenfassung)
          - key_facts: list[str] (zentrale Aussagen/Formeln/Fakten)
          - tags: list[str] (kurze thematische Tags, frei)

        prev_text / next_text:
          - optionale Ausschnitte aus vorherigem / nächstem Chunk
          - dienen nur als Kontext, klassifiziert wird ausschließlich der Fokus-Chunk
        """
        if not text:
            return None

        # Fokus-Chunk hart beschneiden
        if len(text) > self.max_chars:
            text = text[: self.max_chars]

        # Kontext-Snippets begrenzen
        ctx_before = ""
        if prev_text:
            prev_text = str(prev_text)
            ctx_before = prev_text[-self.max_context_chars :]

        ctx_after = ""
        if next_text:
            next_text = str(next_text)
            ctx_after = next_text[: self.max_context_chars]

        # IDs und optionale Beschreibungen für den Prompt vorbereiten
        def fmt_list(name: str) -> str:
            items = []
            for entry in taxonomies[name]:
                _id = entry.get("id")
                desc = entry.get("description", "")
                label = entry.get("label", "")
                if label:
                    items.append(f'- "{_id}": {label} – {desc}')
                else:
                    items.append(f'- "{_id}": {desc}')
            return "\n".join(items)

        content_type_block = fmt_list("content_type")
        domain_block = fmt_list("domain")
        artifact_role_block = fmt_list("artifact_role")
        trust_level_block = fmt_list("trust_level")
        chunk_role_block = fmt_list("chunk_role")

        system_prompt = (
            "You are a precise classifier and summarizer for technical engineering documents "
            "(thermodynamics, simulations, experiments, HPC, GT-Power, documentation).\n"
            "Your job is to:\n"
            "  (1) assign semantic tags from a fixed taxonomy and\n"
            "  (2) extract a short technical summary and key facts for Q&A generation.\n\n"
            "You MAY use CONTEXT_BEFORE and CONTEXT_AFTER to better understand the position of "
            "the focus chunk in a derivation or section, but you MUST classify only the FOCUS_CHUNK.\n\n"
            "You MUST respond with a single JSON object only. No explanations, "
            "no markdown, no surrounding text."
        )

        # Kontextblöcke nur einfügen, wenn vorhanden
        ctx_before_block = f'CONTEXT_BEFORE (optional, previous chunk):\n\"\"\"{ctx_before}\"\"\"\n\n' if ctx_before else ""
        ctx_after_block = f'CONTEXT_AFTER  (optional, next chunk):\n\"\"\"{ctx_after}\"\"\"\n\n' if ctx_after else ""

        user_prompt = f"""
We have a FOCUS_CHUNK from a larger document.

Document title: "{doc_title}"

{ctx_before_block}FOCUS_CHUNK (this is what you must classify and summarize):
\"\"\"{text}\"\"\"

{ctx_after_block}TASK 1: CLASSIFICATION

Classify this FOCUS_CHUNK according to the following taxonomy. Use ONLY IDs from the lists.

Allowed values:

1) language (free choice, not from taxonomy):
   - "de"      : German
   - "en"      : English
   - "mixed"   : clearly mixed German/English
   - "unknown" : cannot be determined

2) content_type (0–2 items from this list):
{content_type_block}

3) domain (0–3 items from this list):
{domain_block}

4) artifact_role (0–3 items from this list):
{artifact_role_block}

5) trust_level (exactly ONE item from this list):
{trust_level_block}

6) chunk_role (0–2 items from this list):
   Use this to describe the pedagogical role of the FOCUS_CHUNK.
{chunk_role_block}


TASK 2: SEMANTIC ENRICHMENT FOR Q&A

Based on the same FOCUS_CHUNK:

7) summary:
   - Provide a short technical summary (1–3 sentences),
   - Focus on the main idea, not on page layout or file paths.

8) key_facts:
   - Provide a list (array) of 3–8 short key facts,
   - Each entry should be a self-contained statement or formula that could be used
     to create technical Q&A questions (e.g. definitions, derived equations,
     parameter relationships, qualitative statements).

9) tags:
   - Provide 2–6 short topic tags (free text, not from taxonomy),
   - Use concise, technical phrases in English, e.g. "equation_of_state",
     "van_der_waals", "critical_point", "compressibility_factor".


OUTPUT FORMAT (STRICT):

Return EXACTLY one JSON object with keys:
  "language": string,
  "content_type": list of strings,
  "domain": list of strings,
  "artifact_role": list of strings,
  "trust_level": string,
  "chunk_role": list of strings,
  "summary": string,
  "key_facts": list of strings,
  "tags": list of strings

Example (schema only, NOT the real answer):
{{
  "language": "en",
  "content_type": ["textbook"],
  "domain": ["thermodynamics"],
  "artifact_role": ["statement"],
  "trust_level": "high",
  "chunk_role": ["derivation"],
  "summary": "Short technical summary of what this chunk explains.",
  "key_facts": [
    "First key fact in one sentence.",
    "Second key fact or important equation.",
    "Third key fact about assumptions or limitations."
  ],
  "tags": ["equation_of_state", "critical_point", "compressibility_factor"]
}}

Now produce the JSON classification and enrichment for the FOCUS_CHUNK.
"""

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": self.temperature,
            "stream": False,
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

        # Robust: ggf. JSON aus Text "herausziehen"
        return self._safe_parse_json(content)

    @staticmethod
    def _safe_parse_json(text: str) -> Optional[Dict[str, Any]]:
        text = text.strip()
        # Falls Modell blöderweise ```json ... ``` liefert
        if text.startswith("```"):
            # alles zwischen erster "{" und letzter "}" nehmen
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

def _as_list_of_str(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(v) for v in value if str(v).strip()]
    return []


def normalize_semantic_result(
    raw: Dict[str, Any],
    taxonomies: Dict[str, List[Dict[str, Any]]],
) -> Dict[str, Any]:
    """
    Filtert und normalisiert die LLM-Ausgabe gegen die Taxonomien und
    begrenzt Listenlängen.

    Rückgabeformat:
      {
        "language": str,
        "content_type": list[str],
        "domain": list[str],
        "artifact_role": list[str],
        "trust_level": str,
        "chunk_role": list[str],
        "summary": str,
        "key_facts": list[str],
        "tags": list[str],
      }
    """
    allowed_content_type = set(extract_ids(taxonomies["content_type"]))
    allowed_domain = set(extract_ids(taxonomies["domain"]))
    allowed_artifact_role = set(extract_ids(taxonomies["artifact_role"]))
    allowed_trust_level = set(extract_ids(taxonomies["trust_level"]))
    allowed_chunk_role = set(extract_ids(taxonomies["chunk_role"]))

    # Sprache
    language = str(raw.get("language", "unknown")).lower()
    if language not in {"de", "en", "mixed", "unknown"}:
        language = "unknown"

    # Taxonomie-Listen
    ct = [v for v in _as_list_of_str(raw.get("content_type")) if v in allowed_content_type]
    dom = [v for v in _as_list_of_str(raw.get("domain")) if v in allowed_domain]
    ar = [v for v in _as_list_of_str(raw.get("artifact_role")) if v in allowed_artifact_role]
    cr = [v for v in _as_list_of_str(raw.get("chunk_role")) if v in allowed_chunk_role]

    # trust_level
    tl_raw = str(raw.get("trust_level", "")).strip()
    trust = tl_raw if tl_raw in allowed_trust_level else None
    if trust is None:
        # Fallback: medium, falls vorhanden, sonst erster Eintrag
        if "medium" in allowed_trust_level:
            trust = "medium"
        else:
            trust = next(iter(allowed_trust_level)) if allowed_trust_level else "unknown"

    # Begrenze Anzahl pro Liste (sicherheitshalber)
    ct = ct[:2]
    dom = dom[:3]
    ar = ar[:3]
    cr = cr[:2]

    # Summary
    summary = raw.get("summary", "")
    if summary is None:
        summary = ""
    if not isinstance(summary, str):
        summary = str(summary)
    summary = summary.strip()
    # Hard limit, um Ausreißer einzufangen
    if len(summary) > 2000:
        summary = summary[:2000]

    # key_facts
    key_facts = _as_list_of_str(raw.get("key_facts"))
    # Leerzeilen entfernen und hart begrenzen
    key_facts = [kf.strip() for kf in key_facts if kf.strip()]
    key_facts = key_facts[:10]

    # tags
    tags = _as_list_of_str(raw.get("tags"))
    tags = [t.strip() for t in tags if t.strip()]
    tags = tags[:10]

    return {
        "language": language,
        "content_type": ct,
        "domain": dom,
        "artifact_role": ar,
        "trust_level": trust,
        "chunk_role": cr,
        "summary": summary,
        "key_facts": key_facts,
        "tags": tags,
    }


# ---------------------------------------------------------------------------
# Hauptlogik: JSONL lesen, annotieren, wieder schreiben (mit Nachbar-Kontext)
# ---------------------------------------------------------------------------

def process_file(
    in_path: Path,
    out_path: Path,
    classifier: LLMSemanticClassifier,
    taxonomies: Dict[str, List[Dict[str, Any]]],
) -> None:
    """
    Liest alle Records einer JSONL-Datei in eine Liste, damit für jeden
    Fokus-Chunk optional der vorherige und nächste Chunk als Kontext
    mitgegeben werden kann.
    """
    logging.info("Verarbeite %s → %s", in_path.name, out_path.name)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # 1) gesamte Datei einlesen und JSON dekodieren
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
    annotated = 0

    # 2) über alle Records iterieren, mit Index für Kontext
    with out_path.open("w", encoding="utf-8") as fout:
        for idx, rec in enumerate(records):
            content = rec.get("content", "")
            title = rec.get("title", "") or rec.get("doc_id", "")

            # Nachbar-Kontext vorbereiten
            prev_content = records[idx - 1].get("content", "") if idx > 0 else None
            next_content = records[idx + 1].get("content", "") if idx + 1 < total else None

            llm_raw = classifier.classify_chunk(
                content,
                title,
                taxonomies,
                prev_text=prev_content,
                next_text=next_content,
            )

            if llm_raw is None:
                # Nichts überschreiben, Chunk bleibt wie er ist
                fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
                continue

            semantic = normalize_semantic_result(llm_raw, taxonomies)

            # language auf oberster Ebene ebenfalls setzen
            lang_existing = rec.get("language")
            if not lang_existing or lang_existing == "unknown":
                rec["language"] = semantic["language"]

            # semantic-Block im Record aktualisieren / erweitern
            sem_block = rec.get("semantic") or {}
            sem_block.update(
                {
                    "content_type": semantic["content_type"],
                    "domain": semantic["domain"],
                    "artifact_role": semantic["artifact_role"],
                    "trust_level": semantic["trust_level"],
                    "chunk_role": semantic["chunk_role"],
                    "summary": semantic["summary"],
                    "key_facts": semantic["key_facts"],
                    "tags": semantic["tags"],
                }
            )
            rec["semantic"] = sem_block

            fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
            annotated += 1

    logging.info(
        "Fertig: %s (Chunks gesamt: %d, annotiert: %d)",
        in_path.name,
        total,
        annotated,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Semantische Anreicherung normalisierter JSONL-Chunks per LLM (Ollama), inkl. Nachbar-Kontext und chunk_role."
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        default=str(REPO_ROOT / "normalized" / "json"),
        help="Eingabeverzeichnis mit JSONL-Dateien (normalized/json).",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(REPO_ROOT / "semantic" / "json"),
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
        format="[%(levelname)s] %(message)s",
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
