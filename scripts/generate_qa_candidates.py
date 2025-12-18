#!/usr/bin/env python
"""
generate_qa_candidates.py

Schritt 3 der DACHS-RAG-Pipeline: aus semantisch angereicherten Chunks
(semantic/json/*.jsonl) werden mithilfe eines LLM und des FAISS-Kontextindex
erste Frage–Antwort-Kandidaten erzeugt (qa_candidates/jsonl/*.jsonl).

Wichtige Eigenschaften:
- nutzt den globalen Kontextindex über FaissRetriever
- bildet Kontextgruppen aus einem Ankerchunk + FAISS-Nachbarn + lokalen Nachbarn
- erzeugt mit einem LLM mehrere Q/A-Paare pro Gruppe
- schreibt wiederaufnahmefähige JSONL-Ausgabedateien pro Eingabedatei
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

import requests  # für Ollama / HTTP-LLM-Backend

# ---------------------------------------------------------------------------
# Pfad-Setup: Repository-Root bestimmen und optional config.paths.paths_utils nutzen
# ---------------------------------------------------------------------------

THIS_FILE = Path(__file__).resolve()
DEFAULT_REPO_ROOT = THIS_FILE.parent.parent

if str(DEFAULT_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(DEFAULT_REPO_ROOT))

try:
    # Optional, aber bevorzugt: zentrale Pfad-Helfer benutzen, wenn vorhanden
    from config.paths.paths_utils import get_path, REPO_ROOT as CONFIG_REPO_ROOT  # type: ignore
    REPO_ROOT = Path(CONFIG_REPO_ROOT)
except Exception:  # pragma: no cover - Fallback, falls config nicht importierbar ist
    get_path = None  # type: ignore
    REPO_ROOT = DEFAULT_REPO_ROOT

try:
    from scripts.faiss_retriever import FaissRetriever  # type: ignore
except Exception as e:  # pragma: no cover
    raise ImportError(
        "Konnte 'FaissRetriever' aus 'scripts/faiss_retriever' nicht importieren. "
        "Bitte sicherstellen, dass das Skript im selben Repository liegt."
    ) from e


# ---------------------------------------------------------------------------
# Dataklassen / Typen
# ---------------------------------------------------------------------------

@dataclass
class QAConfig:
    """Stark vereinfachter Wrapper um die JSON-Konfiguration."""
    raw: Dict[str, Any]
    config_path: Path

    @property
    def paths(self) -> Dict[str, Any]:
        return self.raw.get("paths", {})

    @property
    def filters(self) -> Dict[str, Any]:
        return self.raw.get("filters", {})

    @property
    def neighbors(self) -> Dict[str, Any]:
        return self.raw.get("neighbors", {})

    @property
    def grouping(self) -> Dict[str, Any]:
        return self.raw.get("grouping", {})

    @property
    def sampling(self) -> Dict[str, Any]:
        return self.raw.get("sampling", {})

    @property
    def llm(self) -> Dict[str, Any]:
        return self.raw.get("llm", {})

    @property
    def runtime(self) -> Dict[str, Any]:
        return self.raw.get("runtime", {})

    @property
    def output(self) -> Dict[str, Any]:
        return self.raw.get("output", {})

    @property
    def debug(self) -> Dict[str, Any]:
        return self.raw.get("debug", {})


# ---------------------------------------------------------------------------
# Hilfsfunktionen für Dateien & JSON
# ---------------------------------------------------------------------------

def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_text(path: Path) -> str:
    with path.open("r", encoding="utf-8") as f:
        return f.read()


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def iter_semantic_files(semantic_dir: Path, limit_num_files: int = 0) -> Iterable[Path]:
    """Liefert alle relevanten semantic/json-Dateien (JSONL oder JSON)."""
    files = sorted(
        p for p in semantic_dir.glob("*.jsonl")
        if p.is_file()
    ) + sorted(
        p for p in semantic_dir.glob("*.json")
        if p.is_file()
    )
    if limit_num_files > 0:
        files = files[:limit_num_files]
    return files


def load_semantic_file(path: Path) -> List[Dict[str, Any]]:
    """Lädt eine semantic-Datei (JSONL oder JSON) komplett in den Speicher."""
    if path.suffix == ".jsonl":
        chunks: List[Dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    chunks.append(json.loads(line))
                except json.JSONDecodeError as e:
                    logging.warning("Fehler beim Parsen von %s: %s", path, e)
        return chunks
    elif path.suffix == ".json":
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        logging.warning("Unerwartetes JSON-Format in %s (kein Listentop-Level)", path)
        return []
    else:
        raise ValueError(f"Unbekanntes Datei-Format für semantic-Datei: {path}")


def read_existing_anchor_ids(out_path: Path) -> List[str]:
    """Liest vorhandene Q/A-Datei und extrahiert anchor_chunk_id für Resume."""
    if not out_path.exists():
        return []
    anchor_ids: List[str] = []
    with out_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            anchor = obj.get("anchor_chunk_id")
            if isinstance(anchor, str):
                anchor_ids.append(anchor)
    return anchor_ids


def open_output_file(out_path: Path, resume_mode: str) -> Tuple[Any, List[str]]:
    """
    Öffnet die Ausgabedatei im passenden Modus.

    - resume_mode == "overwrite": existierende Datei wird gelöscht.
    - resume_mode == "append": Datei wird im Append-Modus geöffnet,
      bestehende anchor_chunk_ids werden zurückgegeben.
    """
    if resume_mode == "overwrite" and out_path.exists():
        logging.info("Überschreibe existierende Datei: %s", out_path)
        out_path.unlink()

    ensure_dir(out_path.parent)

    if resume_mode in ("append", "resume"):
        processed = read_existing_anchor_ids(out_path)
        f = out_path.open("a", encoding="utf-8")
        return f, processed

    # Fallback: overwrite
    f = out_path.open("w", encoding="utf-8")
    return f, []


# ---------------------------------------------------------------------------
# Semantik-Helfer
# ---------------------------------------------------------------------------

def get_semantic_field(chunk: Dict[str, Any], field: str, default: Any = None) -> Any:
    """Liest ein Feld z. B. 'trust_level' entweder flach oder aus semantic.*."""
    if field in chunk:
        return chunk[field]
    semantic = chunk.get("semantic") or {}
    if isinstance(semantic, dict):
        return semantic.get(field, default)
    return default


def get_flat_list_field(chunk: Dict[str, Any], field: str) -> List[str]:
    value = get_semantic_field(chunk, field, [])
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [str(v) for v in value]
    return []


def is_candidate_chunk(chunk: Dict[str, Any], cfg: QAConfig) -> bool:
    """Prüft, ob ein Chunk als Kandidat für Q/A-Generierung taugt."""
    filters = cfg.filters
    lang_allowed = set(filters.get("languages_allowed", []))
    trust_allowed = set(filters.get("trust_levels_allowed", []))
    roles_allowed = set(filters.get("chunk_roles_allowed", []))
    content_types_allowed = set(filters.get("content_types_allowed", []))

    language = chunk.get("language")
    if lang_allowed and language not in lang_allowed:
        return False

    trust_level = get_semantic_field(chunk, "trust_level")
    if trust_allowed and trust_level not in trust_allowed:
        return False

    chunk_role = get_semantic_field(chunk, "chunk_role")
    if roles_allowed and chunk_role not in roles_allowed:
        return False

    content_types = get_flat_list_field(chunk, "content_type")
    if content_types_allowed and not (set(content_types) & content_types_allowed):
        return False

    content = chunk.get("content") or ""
    if not isinstance(content, str) or not content.strip():
        # ohne Text keine sinnvollen Fragen
        return False

    return True


# ---------------------------------------------------------------------------
# Kontextbildung mit FAISS + lokalen Nachbarn
# ---------------------------------------------------------------------------

def get_local_neighbors(
    chunks: Sequence[Dict[str, Any]],
    idx: int,
    cfg: QAConfig,
) -> List[Dict[str, Any]]:
    """Wählt lokale Nachbarn vor/nach dem Index."""
    n_before = int(cfg.neighbors.get("max_local_neighbors_before", 1))
    n_after = int(cfg.neighbors.get("max_local_neighbors_after", 1))

    local_neighbors: List[Dict[str, Any]] = []

    # vorherige Chunks
    for offset in range(1, n_before + 1):
        j = idx - offset
        if j < 0:
            break
        local_neighbors.append(chunks[j])

    # folgende Chunks
    for offset in range(1, n_after + 1):
        j = idx + offset
        if j >= len(chunks):
            break
        local_neighbors.append(chunks[j])

    return local_neighbors


def filter_faiss_neighbors(
    candidate: Dict[str, Any],
    neighbors: Sequence[Dict[str, Any]],
    cfg: QAConfig,
) -> List[Dict[str, Any]]:
    """Filtert FAISS-Nachbarn nach Score, Domain, Trust etc."""
    filters = cfg.filters
    neighbors_cfg = cfg.neighbors

    lang_allowed = set(filters.get("languages_allowed", []))
    trust_allowed = set(filters.get("trust_levels_allowed", []))
    content_types_allowed = set(filters.get("content_types_allowed", []))
    domains_candidate = set(get_flat_list_field(candidate, "domain"))

    similarity_threshold = float(neighbors_cfg.get("similarity_threshold", 0.0))
    max_neighbors = int(neighbors_cfg.get("max_neighbors", 8))

    filtered: List[Dict[str, Any]] = []
    candidate_chunk_id = candidate.get("chunk_id")

    for nb in neighbors:
        nb_chunk_id = nb.get("chunk_id")
        if nb_chunk_id == candidate_chunk_id:
            # Ankerchunk selbst ignorieren
            continue

        score = nb.get("score")
        try:
            score_f = float(score) if score is not None else 1.0
        except (TypeError, ValueError):
            score_f = 1.0

        if similarity_threshold > 0.0 and score_f < similarity_threshold:
            continue

        # Sprache
        nb_lang = nb.get("language")
        if lang_allowed and nb_lang not in lang_allowed:
            continue

        # Trust
        nb_trust = get_semantic_field(nb, "trust_level")
        if trust_allowed and nb_trust not in trust_allowed:
            continue

        # Content-Type
        nb_ct = set(get_flat_list_field(nb, "content_type"))
        if content_types_allowed and not (nb_ct & content_types_allowed):
            continue

        # Domain-Nähe (wenn Domain bekannt)
        nb_domains = set(get_flat_list_field(nb, "domain"))
        if domains_candidate and nb_domains and not (domains_candidate & nb_domains):
            # komplett fachfremd
            continue

        filtered.append(nb)

    # Nach Score sortieren (absteigend), falls vorhanden
    filtered.sort(key=lambda x: float(x.get("score") or 0.0), reverse=True)

    if max_neighbors > 0:
        filtered = filtered[:max_neighbors]

    return filtered


def build_context_group(
    candidate: Dict[str, Any],
    local_neighbors: Sequence[Dict[str, Any]],
    faiss_neighbors: Sequence[Dict[str, Any]],
    cfg: QAConfig,
) -> List[Dict[str, Any]]:
    """
    Baut aus Anker + lokalen + FAISS-Nachbarn eine Gruppenliste.
    Jede Gruppe besteht aus dicts mit Minimalfeldern für den Prompt.
    """
    grouping = cfg.grouping
    min_group_size = int(grouping.get("min_group_size", 2))
    max_group_size = int(grouping.get("max_group_size", 6))

    # Reihenfolge: Ankerchunk, lokale Nachbarn, dann FAISS-Nachbarn
    ordered_chunks: List[Dict[str, Any]] = []
    seen_ids: set[str] = set()

    def add_chunk(ch: Dict[str, Any]) -> None:
        cid = str(ch.get("chunk_id"))
        if not cid or cid in seen_ids:
            return
        seen_ids.add(cid)

        # Kontextobjekt mit den wichtigsten Feldern
        summary_short = get_semantic_field(ch, "summary_short")
        if not isinstance(summary_short, str):
            summary_short = None

        ordered_chunks.append(
            {
                "chunk_id": cid,
                "doc_id": ch.get("doc_id"),
                "language": ch.get("language"),
                "trust_level": get_semantic_field(ch, "trust_level"),
                "content_type": get_flat_list_field(ch, "content_type"),
                "domain": get_flat_list_field(ch, "domain"),
                "summary_short": summary_short,
                "content": ch.get("content"),
            }
        )

    add_chunk(candidate)
    for ch in local_neighbors:
        add_chunk(ch)
    for ch in faiss_neighbors:
        add_chunk(ch)

    if len(ordered_chunks) < min_group_size:
        return []

    if len(ordered_chunks) > max_group_size:
        ordered_chunks = ordered_chunks[:max_group_size]

    return ordered_chunks


# ---------------------------------------------------------------------------
# LLM-Aufruf (Ollama-Backend, einfach gehalten)
# ---------------------------------------------------------------------------

def extract_json_from_text(text: str) -> Any:
    """
    Versucht, aus einer beliebigen LLM-Antwort ein JSON-Array zu extrahieren.
    Erwartet ein Top-Level-Array mit Objekten.
    """
    text = text.strip()
    # einfacher Fall: Text beginnt direkt mit '['
    if text.startswith("["):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

    # Suche erstes '[' und letztes ']'
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1 and end > start:
        candidate = text[start : end + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    raise ValueError("Konnte kein gültiges JSON-Array aus LLM-Antwort extrahieren.")


def call_llm_ollama(
    system_prompt: str,
    user_prompt: str,
    model: str,
    temperature: float,
    top_p: float,
    max_tokens: int,
    timeout_s: int,
) -> List[Dict[str, Any]]:
    """
    Ruft ein Ollama-Chat-Modell auf und erwartet einen JSON-Array-Body
    mit Q/A-Objekten.
    """
    url = os.environ.get("OLLAMA_API_URL", "http://127.0.0.1:11434/api/chat")

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
        "options": {
            "temperature": float(temperature),
            "top_p": float(top_p),
        },
    }

    logging.debug("Sende Anfrage an Ollama (%s, Modell=%s)", url, model)
    resp = requests.post(url, json=payload, timeout=timeout_s)
    resp.raise_for_status()
    data = resp.json()

    # laut Ollama-Doku enthält die Antwort i. d. R. ein 'message'-Objekt
    message = data.get("message") or {}
    content = message.get("content") or ""
    if not isinstance(content, str):
        raise ValueError("Ollama-Antwort enthält keinen Text-Content.")

    parsed = extract_json_from_text(content)
    if not isinstance(parsed, list):
        raise ValueError("LLM-Output ist kein JSON-Array.")

    return parsed  # Liste von Q/A-Objekten


def build_context_text_for_prompt(
    context_group: Sequence[Dict[str, Any]],
    max_chars_per_chunk: int = 1200,
) -> str:
    """
    Baut den textuellen Kontextteil des Prompts.
    Jeder Chunk wird mit chunk_id/doc_id gelabelt und abgeschnitten.
    """
    lines: List[str] = []
    for idx, ch in enumerate(context_group, start=1):
        cid = ch.get("chunk_id")
        did = ch.get("doc_id")
        summary = ch.get("summary_short")
        content = ch.get("content") or ""

        # bevorzugt Summary, ansonsten Content
        if isinstance(summary, str) and summary.strip():
            text = summary.strip()
        else:
            text = str(content).strip()

        if max_chars_per_chunk > 0 and len(text) > max_chars_per_chunk:
            text = text[:max_chars_per_chunk] + " …"

        header = f"[Chunk {idx} | chunk_id={cid} | doc_id={did}]"
        lines.append(header)
        lines.append(text)
        lines.append("")  # Leerzeile
    return "\n".join(lines)


def render_user_prompt(
    context_group: Sequence[Dict[str, Any]],
    user_template: str,
    max_qa_per_group: int,
) -> str:
    """Setzt die Kontexttexte und Parameter in das User-Prompt-Template ein."""
    context_text = build_context_text_for_prompt(context_group)
    prompt = user_template
    prompt = prompt.replace("{CONTEXT}", context_text)
    prompt = prompt.replace("{MAX_QA_PER_GROUP}", str(max_qa_per_group))
    return prompt

def load_or_default_prompts(cfg: QAConfig) -> Tuple[str, str]:
    """Lädt System- und User-Prompt aus Dateien, fällt ansonsten auf Default zurück."""
    paths = cfg.paths

    system_path = paths.get("prompt_system_file")
    user_path = paths.get("prompt_user_template_file")

    system_prompt: Optional[str] = None
    user_template: Optional[str] = None

    if system_path:
        p = REPO_ROOT / system_path
        if p.exists():
            system_prompt = load_text(p)

    if user_path:
        p = REPO_ROOT / user_path
        if p.exists():
            user_template = load_text(p)

    if system_prompt is None:
        system_prompt = (
            "You are an expert assistant for engineering, thermodynamics and numerical simulation. "
            "Your task is to design exam-style and practice question–answer pairs strictly from small sets "
            "of technical document chunks.\n\n"
            "Core rules:\n"
            "- Use only information that is explicitly present in the provided chunks. Never invent formulas, "
            "  symbols, parameter values, assumptions or definitions that are not clearly stated there.\n"
            "- Prefer non-trivial, conceptually rich questions over simple recall of isolated facts.\n"
            "- When the text is ambiguous or incomplete, omit that aspect instead of guessing.\n"
            "- Use the same technical terminology, symbols and notation as in the text (including Greek letters, "
            "  indices, subscripts, units, etc.).\n"
            "- Generate questions and answers in the same main language as the context (German vs. English).\n"
            "- Keep answers precise, technically correct and as compact as possible while still fully answering the question.\n"
        )

    if user_template is None:
        user_template = (
            "You are given a set of context chunks from technical documents. Each chunk is labeled with a "
            "chunk_id and doc_id so you can orient yourself, but you must NOT mention chunk_id or doc_id in the "
            "questions or answers.\n\n"
            "{CONTEXT}\n\n"
            "Your goals:\n"
            "1. Based only on the information in these chunks, generate between 1 and {MAX_QA_PER_GROUP} "
            "   high-quality, non-trivial question–answer pairs.\n"
            "2. Focus on conceptual understanding, conditions of validity, relationships between quantities, "
            "   assumptions, limitations and the physical or mathematical meaning of formulas.\n"
            "3. When formulas, derivations or numerical relationships are present, you may ask for interpretation, "
            "   explanation of steps or qualitative effects (\"what happens if …\"), but every step must be justified "
            "   by the text.\n"
            "4. Avoid purely trivial questions that simply restate a single sentence or definition without any deeper aspect.\n"
            "5. Do not rely on outside knowledge: if something is not clearly stated in the chunks, you must NOT use it.\n\n"
            "Question style guidelines:\n"
            "- Questions and answers must be in the same main language as the context.\n"
            "- Use precise technical wording and correct units.\n"
            "- Questions should be self-contained: a student reading only the question (and answer) should not need to "
            "  see the chunk labels.\n"
            "- Vary difficulty: some questions can be basic, but prefer intermediate or advanced where the text allows it.\n\n"
            "Difficulty label:\n"
            "- For each pair, set \"difficulty\" to one of: \"basic\", \"intermediate\", \"advanced\".\n"
            "- Use \"basic\" only for simple recall or direct application; \"intermediate\" for multi-step reasoning; "
            "  \"advanced\" for subtle conditions, combined concepts or complex derivations.\n\n"
            "Output format (very important):\n"
            "- Return your answer as a JSON array ONLY, with no explanation, no comments and no extra text before or after.\n"
            "- Each element of the array must be an object with exactly these required keys:\n"
            "  - \"question\": string\n"
            "  - \"answer\": string\n"
            "  - \"difficulty\": \"basic\" | \"intermediate\" | \"advanced\"\n\n"
            "Example of the required output structure:\n"
            "[\n"
            "  {\"question\": \"...\", \"answer\": \"...\", \"difficulty\": \"intermediate\"},\n"
            "  {\"question\": \"...\", \"answer\": \"...\", \"difficulty\": \"advanced\"}\n"
            "]\n"
        )

    return system_prompt, user_template



# ---------------------------------------------------------------------------
# Hauptlogik pro Datei
# ---------------------------------------------------------------------------

def process_semantic_file(
    in_path: Path,
    out_path: Path,
    cfg: QAConfig,
    retriever: FaissRetriever,
) -> int:
    """
    Verarbeitet eine semantic-Datei und schreibt Q/A-Kandidaten.
    Gibt die Anzahl der geschriebenen Q/A-Paare zurück.
    """
    runtime = cfg.runtime
    sampling = cfg.sampling
    neighbors_cfg = cfg.neighbors

    resume_mode = runtime.get("resume_mode", "append")
    dry_run = bool(runtime.get("dry_run", False))
    log_every = int(runtime.get("log_every_n_examples", 50))
    max_chunks_debug = int(cfg.debug.get("limit_num_chunks", 0))

    max_qa_per_group = int(sampling.get("max_qa_per_group", 3))
    max_groups_per_chunk = int(sampling.get("max_groups_per_chunk", 1))
    max_qa_per_document = int(sampling.get("max_qa_per_document", 0))
    global_qa_limit = int(sampling.get("global_qa_limit", 0))

    # Für diesen einzelnen Datei-Lauf lokaler Limitwert
    remaining_qa_for_document = max_qa_per_document if max_qa_per_document > 0 else None

    # LLM-Konfiguration
    llm_cfg = cfg.llm
    backend = llm_cfg.get("backend", "ollama")
    model = llm_cfg.get("model", "llama3.1:8b-instruct")
    temperature = float(llm_cfg.get("temperature", 0.2))
    top_p = float(llm_cfg.get("top_p", 0.9))
    max_tokens = int(llm_cfg.get("max_tokens", 1024))
    timeout_s = int(llm_cfg.get("request_timeout_s", 60))

    system_prompt, user_template = load_or_default_prompts(cfg)

    # Datei laden
    chunks = load_semantic_file(in_path)
    if not chunks:
        logging.warning("Keine Chunks in %s gefunden, überspringe.", in_path)
        return 0

    # Map für lokale Nachbarn
    chunk_index_by_id = {
        str(ch.get("chunk_id")): idx for idx, ch in enumerate(chunks)
    }

    out_f, processed_anchor_ids = open_output_file(out_path, resume_mode)
    processed_set = set(processed_anchor_ids)

    total_written = 0
    total_groups = 0

    logging.info(
        "Verarbeite Datei %s (%d Chunks, bereits %d Anker-Chunks in Ausgabe).",
        in_path.name,
        len(chunks),
        len(processed_set),
    )

    for idx, chunk in enumerate(chunks):
        if max_chunks_debug and idx >= max_chunks_debug:
            logging.info(
                "Debug-Limit 'limit_num_chunks' erreicht (%d), breche ab für Datei %s.",
                max_chunks_debug,
                in_path.name,
            )
            break

        chunk_id = str(chunk.get("chunk_id"))
        if not chunk_id:
            continue

        if chunk_id in processed_set:
            continue

        if not is_candidate_chunk(chunk, cfg):
            continue

        if remaining_qa_for_document is not None and remaining_qa_for_document <= 0:
            logging.info(
                "max_qa_per_document für %s erreicht, breche ab.",
                in_path.name,
            )
            break

        # lokale Nachbarn
        local_neighbors = get_local_neighbors(chunks, idx, cfg)

        # FAISS-Nachbarn holen
        top_k_faiss = int(neighbors_cfg.get("top_k_faiss", 16))
        try:
            faiss_neighbors = retriever.get_neighbors_for_chunk(
                chunk_id_or_uid=chunk_id,
                top_k=top_k_faiss,
            )
        except Exception as e:
            logging.warning(
                "Fehler beim FAISS-Retrieval für chunk_id=%s in %s: %s",
                chunk_id,
                in_path.name,
                e,
            )
            faiss_neighbors = []

        faiss_neighbors_filtered = filter_faiss_neighbors(
            candidate=chunk,
            neighbors=faiss_neighbors,
            cfg=cfg,
        )

        context_group = build_context_group(
            candidate=chunk,
            local_neighbors=local_neighbors,
            faiss_neighbors=faiss_neighbors_filtered,
            cfg=cfg,
        )

        if not context_group:
            continue

        # Q/A-Gruppenbegrenzung pro Chunk (aktuell max 1)
        num_groups_for_chunk = 0

        # Eine Gruppe pro Kandidatenchunk (simple MVP-Variante)
        user_prompt = render_user_prompt(
            context_group=context_group,
            user_template=user_template,
            max_qa_per_group=max_qa_per_group,
        )

        if backend != "ollama":
            raise ValueError(f"Nicht unterstützter LLM-Backend-Typ: {backend!r}")

        if dry_run:
            logging.info(
                "[Dry-Run] Würde LLM für chunk_id=%s in %s aufrufen.",
                chunk_id,
                in_path.name,
            )
            continue

        try:
            qa_list = call_llm_ollama(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model=model,
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
                timeout_s=timeout_s,
            )
        except Exception as e:
            logging.warning(
                "LLM-Aufruf für chunk_id=%s in %s fehlgeschlagen: %s",
                chunk_id,
                in_path.name,
                e,
            )
            continue

        if not qa_list:
            continue

        # Q/A-Objekte auf Schema bringen
        written_for_chunk = 0
        for qa_obj in qa_list:
            if not isinstance(qa_obj, dict):
                continue
            question = qa_obj.get("question")
            answer = qa_obj.get("answer")
            if not question or not answer:
                continue

            difficulty = qa_obj.get("difficulty") or "unknown"

            # Aggregierte Metadaten
            all_chunk_ids = [c["chunk_id"] for c in context_group if "chunk_id" in c]
            all_doc_ids = [c.get("doc_id") for c in context_group if c.get("doc_id")]

            language = chunk.get("language")
            trust_level = get_semantic_field(chunk, "trust_level")
            content_types = get_flat_list_field(chunk, "content_type")
            domains = get_flat_list_field(chunk, "domain")

            out_record = {
                "id": f"{chunk_id}_qa{total_written + 1}",
                "anchor_chunk_id": chunk_id,
                "anchor_doc_id": chunk.get("doc_id"),
                "source_chunks": all_chunk_ids,
                "doc_ids": all_doc_ids,
                "question": question,
                "answer": answer,
                "difficulty": difficulty,
                "language": language,
                "content_type": content_types,
                "domain": domains,
                "trust_level": trust_level,
                "workspace_file": in_path.name,
            }

            out_f.write(json.dumps(out_record, ensure_ascii=False) + "\n")
            written_for_chunk += 1
            total_written += 1

            if remaining_qa_for_document is not None:
                remaining_qa_for_document -= 1
                if remaining_qa_for_document <= 0:
                    break

            if global_qa_limit and total_written >= global_qa_limit:
                logging.info(
                    "Globales Q/A-Limit (%d) erreicht, breche Verarbeitung ab.",
                    global_qa_limit,
                )
                break

        if written_for_chunk > 0:
            processed_set.add(chunk_id)
            num_groups_for_chunk += 1
            total_groups += 1

        if total_written and (total_written % max(1, log_every) == 0):
            logging.info(
                "Zwischenstand %s: %d Q/A-Paare aus %d Gruppen.",
                in_path.name,
                total_written,
                total_groups,
            )

        if global_qa_limit and total_written >= global_qa_limit:
            break

        if max_groups_per_chunk and num_groups_for_chunk >= max_groups_per_chunk:
            continue

    out_f.close()

    logging.info(
        "Fertig mit %s: %d Q/A-Paare aus %d Gruppen geschrieben.",
        in_path.name,
        total_written,
        total_groups,
    )
    return total_written


# ---------------------------------------------------------------------------
# CLI & Main
# ---------------------------------------------------------------------------

def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generiert Q/A-Kandidaten aus semantic/json mithilfe eines LLM und eines FAISS-Kontextindex.",
    )
    parser.add_argument(
        "--workspace-root",
        type=str,
        default=None,
        help="Wurzel des Workspaces (überschreibt Wert aus Config).",
    )
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Pfad zur QA-Konfigurationsdatei (JSON). Standard: config/qa/qa_generation.default.json",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default=None,
        help="Log-Level (DEBUG, INFO, WARNING, ERROR). Überschreibt Config.",
    )
    parser.add_argument(
        "--limit-num-files",
        type=int,
        default=None,
        help="Optionales Limit der Anzahl zu verarbeitender Dateien.",
    )
    return parser.parse_args(argv)


def setup_logging(level_name: str) -> None:
    level = getattr(logging, level_name.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def load_qa_config(config_path: Optional[str]) -> QAConfig:
    """Lädt die QA-Konfiguration oder verwendet den Standardpfad."""
    if config_path is not None:
        path = Path(config_path)
    else:
        path = REPO_ROOT / "config" / "qa" / "qa_generation.default.json"

    if not path.exists():
        raise FileNotFoundError(f"QA-Config-Datei nicht gefunden: {path}")

    raw = load_json(path)
    return QAConfig(raw=raw, config_path=path)


def main(argv: Optional[Sequence[str]] = None) -> None:
    args = parse_args(argv)
    cfg = load_qa_config(args.config)

    # Logging konfigurieren
    log_level = args.log_level or cfg.runtime.get("log_level") or "INFO"
    setup_logging(log_level)

    logging.info("Starte generate_qa_candidates.py")
    logging.info("Verwendete Config: %s", cfg.config_path)

    # Workspace-Root bestimmen
    workspace_root: Path
    if args.workspace_root:
        workspace_root = Path(args.workspace_root).expanduser().resolve()
    else:
        # Fallback: Wert aus Config
        ws_cfg = cfg.paths.get("workspace_root")
        if ws_cfg:
            workspace_root = Path(ws_cfg).expanduser().resolve()
        elif get_path is not None:
            # letzter Fallback: zentraler Pfad-Helfer
            try:
                workspace_root = Path(get_path("workspace_root"))
            except Exception:
                workspace_root = REPO_ROOT
        else:
            workspace_root = REPO_ROOT

    logging.info("Workspace-Root: %s", workspace_root)

    semantic_dir = workspace_root / cfg.paths.get("semantic_dir", "semantic/json")
    qa_candidates_dir = workspace_root / cfg.paths.get("qa_candidates_dir", "qa_candidates/jsonl")

    ensure_dir(qa_candidates_dir)

    limit_num_files_cfg = int(cfg.debug.get("limit_num_files", 0))
    if args.limit_num_files is not None and args.limit_num_files > 0:
        limit_num_files = args.limit_num_files
    else:
        limit_num_files = limit_num_files_cfg

    # Retriever initialisieren
    retriever = FaissRetriever(workspace_root=str(workspace_root))

    logging.info("Semantic-Verzeichnis: %s", semantic_dir)
    logging.info("QA-Candidates-Verzeichnis: %s", qa_candidates_dir)

    semantic_files = list(iter_semantic_files(semantic_dir, limit_num_files))
    if not semantic_files:
        logging.warning("Keine semantic/json-Dateien in %s gefunden.", semantic_dir)
        return

    total_written_global = 0
    t_start = time.time()

    for in_path in semantic_files:
        in_basename = in_path.stem  # z. B. incropera_semantic
        pattern = cfg.output.get("output_file_pattern", "{input_basename}.qa_candidates.jsonl")
        out_name = pattern.format(input_basename=in_basename)
        out_path = qa_candidates_dir / out_name

        written = process_semantic_file(
            in_path=in_path,
            out_path=out_path,
            cfg=cfg,
            retriever=retriever,
        )
        total_written_global += written

    elapsed = time.time() - t_start
    logging.info(
        "Q/A-Generierung abgeschlossen: %d Q/A-Paare in %.1f s.",
        total_written_global,
        elapsed,
    )


if __name__ == "__main__":
    main()
