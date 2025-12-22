#!/usr/bin/env python3
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
import hashlib
import json
import logging
import math
import os
import random
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Set, Iterator

import requests

# ---------------------------------------------------------------------------
# Pfad-Setup: Repository-Root bestimmen und optional config.paths.paths_utils nutzen
# ---------------------------------------------------------------------------

THIS_FILE = Path(__file__).resolve()
DEFAULT_REPO_ROOT = THIS_FILE.parent.parent

if str(DEFAULT_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(DEFAULT_REPO_ROOT))

try:
    from config.paths.paths_utils import get_path, REPO_ROOT as CONFIG_REPO_ROOT  # type: ignore

    REPO_ROOT = Path(CONFIG_REPO_ROOT)
except Exception:  # pragma: no cover
    get_path = None  # type: ignore
    REPO_ROOT = DEFAULT_REPO_ROOT

try:
    from scripts.faiss_retriever import FaissRetriever  # type: ignore
except Exception as e:  # pragma: no cover
    raise ImportError(
        "Konnte 'FaissRetriever' aus 'scripts/faiss_retriever' nicht importieren. "
        "Bitte sicherstellen, dass das Skript im selben Repository liegt."
    ) from e

logger = logging.getLogger("generate_qa_candidates")


@dataclass
class QAConfig:
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


@dataclass(frozen=True)

class PromptBundle:
    plan_system: str
    plan_user: str
    gen_system: str
    gen_user: str

def render_prompt(
    *,
    context_group: Sequence[Dict[str, Any]],
    template: str,
    cfg: QAConfig,
    max_qa_per_group: Optional[int] = None,
    plan_json: Optional[str] = None,
) -> str:
    max_chars_per_chunk = int(cfg.grouping.get("max_chars_per_chunk", 1200))
    max_total_chars = int(cfg.grouping.get("max_total_context_chars", 0))

    context_text = build_context_text_for_prompt(
        context_group=context_group,
        max_chars_per_chunk=max_chars_per_chunk,
        max_total_chars=max_total_chars,
    )

    prompt = template.replace("{CONTEXT}", context_text)

    # Optional placeholders (only replace if provided)
    if max_qa_per_group is not None:
        prompt = prompt.replace("{MAX_QA_PER_GROUP}", str(int(max_qa_per_group)))
    if plan_json is not None:
        prompt = prompt.replace("{PLAN_JSON}", plan_json)

    return prompt


def parse_plan_output(plan_arr: Any) -> Optional[Dict[str, Any]]:
    """
    Expect: JSON array with exactly 1 object:
    {
      "takeaways": [ { "takeaway": str, "evidence_chunks": [str,...] }, { ... } ],
      "equations_present": bool,
      "equation_quotes": [str, ...],
      "generator_checks": [str, ...]
    }
    Return dict if valid else None.
    """
    if not isinstance(plan_arr, list) or len(plan_arr) != 1:
        return None
    obj = plan_arr[0]
    if not isinstance(obj, dict):
        return None

    takeaways = obj.get("takeaways")
    if not isinstance(takeaways, list) or len(takeaways) != 2:
        return None
    for t in takeaways:
        if not isinstance(t, dict):
            return None
        if not isinstance(t.get("takeaway"), str) or not t["takeaway"].strip():
            return None
        ev = t.get("evidence_chunks")
        if not isinstance(ev, list) or not ev or not all(isinstance(x, str) and x.strip() for x in ev):
            return None

    if not isinstance(obj.get("equations_present"), bool):
        return None
    eq = obj.get("equation_quotes")
    if not isinstance(eq, list) or not all(isinstance(x, str) for x in eq):
        return None
    gc = obj.get("generator_checks")
    if not isinstance(gc, list) or not all(isinstance(x, str) for x in gc):
        return None

    return obj

@dataclass(frozen=True)
class FaissMetricInfo:
    metric: str
    index_type: str
    normalized: bool

    @property
    def higher_is_better(self) -> bool:
        return self.metric.upper() == "IP"


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_text(path: Path) -> str:
    with path.open("r", encoding="utf-8") as f:
        return f.read()

def _stable_sha1_16(obj: dict) -> str:
    s = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:16]


def make_candidate_id(anchor_chunk_id: str, qa_index: int, payload: dict) -> str:
    q = (payload.get("question") or "").strip()
    a = (payload.get("answer") or "").strip()
    h = _stable_sha1_16({"q": q, "a": a, "i": int(qa_index)})
    return f"{anchor_chunk_id}:{h}"


def _contains_meta_leak(text: str) -> bool:
    t = (text or "").lower()
    bad = [
        "in the text", "in this text", "in the article", "in this article", "in this paper",
        "this section", "this chapter", "as mentioned", "as described", "here", "above", "below",
        "im text", "in diesem text", "im artikel", "in diesem artikel", "in dieser arbeit",
        "dieser abschnitt", "dieses kapitel", "wie oben", "wie unten", "hier", "oben", "unten",
    ]
    return any(p in t for p in bad)


def compute_max_qa_per_document(max_cfg, num_chunks: int, total_chars: int) -> int:
    if isinstance(max_cfg, int):
        return max_cfg
    if isinstance(max_cfg, dict):
        mode = (max_cfg.get("mode") or "adaptive").lower()
        if mode == "adaptive":
            mn = int(max_cfg.get("min", 10))
            mx = int(max_cfg.get("max", 200))
            per_100_chunks = float(max_cfg.get("per_100_chunks", 5.0))
            per_100k_chars = float(max_cfg.get("per_100k_chars", 0.0))
            v = int(round((num_chunks / 100.0) * per_100_chunks + (total_chars / 100000.0) * per_100k_chars))
            return max(mn, min(mx, v))
        if mode == "fixed":
            return int(max_cfg.get("value", 50))
    return 50


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def sha1_text(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def sha1_json(obj: Any) -> str:
    s = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return sha1_text(s)

def _as_int(x: Any) -> Optional[int]:
    try:
        return int(x)
    except Exception:
        return None

def _json_preview(x: object, max_len: int = 900) -> str:
    try:
        s = json.dumps(x, ensure_ascii=False)
    except Exception:
        s = repr(x)
    if len(s) > max_len:
        return s[:max_len] + "…"
    return s


def make_source_ref(chunk: Dict[str, Any]) -> Dict[str, Any]:
    meta = chunk.get("meta") if isinstance(chunk.get("meta"), dict) else {}
    return {
        "chunk_id": chunk.get("chunk_id"),
        "doc_id": chunk.get("doc_id"),
        "source_path": chunk.get("source_path"),
        "title": chunk.get("title"),
        "page_start": _as_int(meta.get("page_start")),
        "page_end": _as_int(meta.get("page_end")),
    }

def normalize_chunk_id_list(x: Any) -> List[str]:
    if not isinstance(x, list):
        return []
    out: List[str] = []
    for v in x:
        if isinstance(v, str) and v.strip():
            out.append(v.strip())
    return out

def load_semantic_file(path: Path) -> List[Dict[str, Any]]:
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
    if path.suffix == ".json":
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        logging.warning("Unerwartetes JSON-Format in %s (kein Listentop-Level)", path)
        return []
    raise ValueError(f"Unbekanntes Datei-Format für semantic-Datei: {path}")


def read_existing_anchor_ids(out_path: Path) -> List[str]:
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
    if resume_mode == "overwrite" and out_path.exists():
        logging.info("Überschreibe existierende Datei: %s", out_path)
        out_path.unlink()

    ensure_dir(out_path.parent)

    if resume_mode in ("append", "resume"):
        processed = read_existing_anchor_ids(out_path)
        f = out_path.open("a", encoding="utf-8")
        return f, processed

    f = out_path.open("w", encoding="utf-8")
    return f, []


def load_faiss_metric_info(workspace_root: Path) -> FaissMetricInfo:
    cfg_path = workspace_root / "indices" / "faiss" / "contextual_config.json"
    if not cfg_path.exists():
        return FaissMetricInfo(metric="IP", index_type="IndexFlatIP", normalized=True)
    raw = load_json(cfg_path)
    metric = str(raw.get("metric") or "IP")
    index_type = str(raw.get("index_type") or "")
    normalized = bool(raw.get("normalized", False))
    return FaissMetricInfo(metric=metric, index_type=index_type, normalized=normalized)


def get_semantic_field(chunk: Dict[str, Any], field: str, default: Any = None) -> Any:
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
    filters = cfg.filters
    lang_allowed = set(filters.get("languages_allowed", []))
    trust_allowed = set(filters.get("trust_levels_allowed", []))
    roles_allowed = set(filters.get("chunk_roles_allowed", []))
    content_types_allowed = set(filters.get("content_types_allowed", []))
    artifact_roles_excluded = set(filters.get("artifact_roles_excluded", []))
    min_content_chars = int(filters.get("min_content_chars", 0))

    language = chunk.get("language")
    if lang_allowed and language not in lang_allowed:
        return False

    trust_level = get_semantic_field(chunk, "trust_level")
    if trust_allowed:
        if isinstance(trust_level, list):
            if not (set(str(v) for v in trust_level) & trust_allowed):
                return False
        else:
            if trust_level not in trust_allowed:
                return False

    chunk_role = get_semantic_field(chunk, "chunk_role")
    if roles_allowed:
        if isinstance(chunk_role, list):
            if not (set(str(v) for v in chunk_role) & roles_allowed):
                return False
        else:
            if chunk_role not in roles_allowed:
                return False


    content_types = get_flat_list_field(chunk, "content_type")
    if content_types_allowed and not (set(content_types) & content_types_allowed):
        return False

    artifact_roles = set(get_flat_list_field(chunk, "artifact_role"))
    if artifact_roles_excluded and (artifact_roles & artifact_roles_excluded):
        return False

    content = chunk.get("content") or ""
    if not isinstance(content, str) or not content.strip():
        return False
    if min_content_chars > 0 and len(content.strip()) < min_content_chars:
        return False

    return True


def get_local_neighbors(
    chunks: Sequence[Dict[str, Any]],
    idx: int,
    cfg: QAConfig,
) -> List[Dict[str, Any]]:
    n_before = int(cfg.neighbors.get("max_local_neighbors_before", 1))
    n_after = int(cfg.neighbors.get("max_local_neighbors_after", 1))

    local_neighbors: List[Dict[str, Any]] = []

    for offset in range(1, n_before + 1):
        j = idx - offset
        if j < 0:
            break
        local_neighbors.append(chunks[j])

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
    metric_info: FaissMetricInfo,
) -> List[Dict[str, Any]]:
    filters = cfg.filters
    neighbors_cfg = cfg.neighbors

    lang_allowed = set(filters.get("languages_allowed", []))
    trust_allowed = set(filters.get("trust_levels_allowed", []))
    content_types_allowed = set(filters.get("content_types_allowed", []))
    artifact_roles_excluded = set(filters.get("artifact_roles_excluded", []))
    domains_candidate = set(get_flat_list_field(candidate, "domain"))

    score_threshold = float(neighbors_cfg.get("similarity_threshold", 0.0))
    max_neighbors = int(neighbors_cfg.get("max_neighbors", 8))

    filtered: List[Dict[str, Any]] = []
    candidate_chunk_id = candidate.get("chunk_id")

    for nb in neighbors:
        nb_chunk_id = nb.get("chunk_id")
        if nb_chunk_id == candidate_chunk_id:
            continue

        score = nb.get("score")
        try:
            score_f = float(score) if score is not None else 0.0
        except (TypeError, ValueError):
            score_f = 0.0

        if score_threshold > 0.0:
            if metric_info.higher_is_better:
                if score_f < score_threshold:
                    continue
            else:
                if score_f > score_threshold:
                    continue

        nb_lang = nb.get("language")
        if lang_allowed and nb_lang not in lang_allowed:
            continue

        nb_trust = get_semantic_field(nb, "trust_level")
        if trust_allowed and nb_trust not in trust_allowed:
            continue

        nb_ct = set(get_flat_list_field(nb, "content_type"))
        if content_types_allowed and not (nb_ct & content_types_allowed):
            continue

        nb_artifact_roles = set(get_flat_list_field(nb, "artifact_role"))
        if artifact_roles_excluded and (nb_artifact_roles & artifact_roles_excluded):
            continue

        nb_domains = set(get_flat_list_field(nb, "domain"))
        if domains_candidate and nb_domains and not (domains_candidate & nb_domains):
            continue

        filtered.append(nb)

    filtered.sort(
        key=lambda x: float(x.get("score") or 0.0),
        reverse=metric_info.higher_is_better,
    )

    if max_neighbors > 0:
        filtered = filtered[:max_neighbors]

    return filtered

def extract_json_from_text(text: str) -> Any:
    text = text.strip()
    if text.startswith("["):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1 and end > start:
        candidate = text[start : end + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    raise ValueError("Konnte kein gültiges JSON-Array aus LLM-Antwort extrahieren.")


def call_llm_ollama_once(
    system_prompt: str,
    user_prompt: str,
    model: str,
    temperature: float,
    top_p: float,
    max_tokens: int,
    timeout_s: int,
    num_ctx: int = 0,          # <-- NEU
) -> List[Dict[str, Any]]:

    url = os.environ.get("OLLAMA_API_URL", "http://127.0.0.1:11434/api/chat")

    options = {
        "temperature": float(temperature),
        "top_p": float(top_p),
        "num_predict": int(max_tokens),
    }
    if int(num_ctx) > 0:
        options["num_ctx"] = int(num_ctx)   # <-- NEU: Kontextfenster wirklich setzen

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
        "options": options,
    }

    resp = requests.post(url, json=payload, timeout=timeout_s)

    if resp.status_code == 404:
        detail = ""
        try:
            detail = json.dumps(resp.json(), ensure_ascii=False)[:600]
        except Exception:
            detail = (resp.text or "")[:300].replace("\n", " ")
        raise RuntimeError(
            f"Ollama returned HTTP 404 for /api/chat. "
            f"This is most likely because the model tag is not available on this node: model='{model}'. "
            f"Verify with: curl -s http://127.0.0.1:PORT/api/tags. "
            f"Details: {detail}"
        )

    resp.raise_for_status()
    data = resp.json()

    message = data.get("message") or {}
    content = message.get("content") or ""
    if not isinstance(content, str) or not content.strip():
        raise ValueError("Ollama-Antwort enthält keinen Text-Content.")

    parsed = extract_json_from_text(content)
    if not isinstance(parsed, list):
        raise ValueError("LLM-Output ist kein JSON-Array.")
    return parsed


def call_llm_ollama_with_retries(
    system_prompt: str,
    user_prompt: str,
    model: str,
    temperature: float,
    top_p: float,
    max_tokens: int,
    timeout_s: int,
    max_retries: int,
    retry_backoff_s: float,
    num_ctx: int = 0,
) -> List[Dict[str, Any]]:
    """
    Unchanged. You reuse this for BOTH passes:
      - Plan pass: call_llm_ollama_with_retries(prompts.plan_system, plan_user_prompt, ..., max_tokens=plan_max_tokens)
      - Generate pass: call_llm_ollama_with_retries(prompts.gen_system, gen_user_prompt, ..., max_tokens=max_tokens)
    """
    last_err: Optional[Exception] = None
    for attempt in range(max_retries + 1):
        try:
            return call_llm_ollama_once(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                model=model,
                temperature=temperature,
                top_p=top_p,
                max_tokens=max_tokens,
                timeout_s=timeout_s,
                num_ctx=num_ctx,
            )
        except Exception as e:
            last_err = e
            if attempt >= max_retries:
                break
            sleep_s = retry_backoff_s * (2.0**attempt)
            sleep_s = sleep_s * (0.9 + 0.2 * random.random())
            time.sleep(max(0.0, sleep_s))

    if last_err is not None:
        raise last_err
    raise RuntimeError("Unbekannter Fehler beim LLM-Aufruf.")


def build_context_text_for_prompt(
    context_group: Sequence[Dict[str, Any]],
    max_chars_per_chunk: int = 1200,
    max_total_chars: int = 0,
) -> str:
    lines: List[str] = []
    total = 0
    for idx, ch in enumerate(context_group, start=1):
        cid = ch.get("chunk_id")
        did = ch.get("doc_id")
        summary = ch.get("summary_short")
        content = ch.get("content") or ""

        if isinstance(summary, str) and summary.strip():
            text = summary.strip()
        else:
            text = str(content).strip()

        if max_chars_per_chunk > 0 and len(text) > max_chars_per_chunk:
            text = text[:max_chars_per_chunk] + " …"

        block = f"[Chunk {idx} | chunk_id={cid} | doc_id={did}]\n{text}\n"
        if max_total_chars > 0 and (total + len(block)) > max_total_chars:
            break

        lines.append(f"[Chunk {idx} | chunk_id={cid} | doc_id={did}]")
        lines.append(text)
        lines.append("")
        total += len(block)

    return "\n".join(lines)

@dataclass(frozen=True)
class PromptBundle:
    plan_system: str
    plan_user: str
    gen_system: str
    gen_user: str

def load_prompt_bundle(cfg: "QAConfig") -> PromptBundle:
    """
    Load double-pass prompts from config/qa/prompts.json (single source of truth).
    """
    prompts_path = REPO_ROOT / "config" / "qa" / "prompts.json"
    data = load_json(prompts_path)

    try:
        plan = data["plan"]
        gen = data["generate"]
        plan_system = str(plan["system"])
        plan_user = str(plan["user"])
        gen_system = str(gen["system"])
        gen_user = str(gen["user"])
    except Exception as e:
        raise KeyError(f"prompts.json invalid or missing keys: {e}")

    # hard validation
    for name, val in [
        ("plan.system", plan_system),
        ("plan.user", plan_user),
        ("generate.system", gen_system),
        ("generate.user", gen_user),
    ]:
        if not isinstance(val, str) or not val.strip():
            raise ValueError(f"prompts.json: '{name}' must be a non-empty string")

    return PromptBundle(
        plan_system=plan_system,
        plan_user=plan_user,
        gen_system=gen_system,
        gen_user=gen_user,
    )

def process_semantic_file(
    in_path: Path,
    out_path: Path,
    cfg: QAConfig,
    retriever: FaissRetriever,
    metric_info: FaissMetricInfo,
    global_state: Dict[str, Any],
) -> int:
    runtime = cfg.runtime
    sampling = cfg.sampling
    neighbors_cfg = cfg.neighbors

    resume_mode = runtime.get("resume_mode", "append")
    dry_run = bool(runtime.get("dry_run", False))
    log_every = int(runtime.get("log_every_n_examples", 50))
    max_chunks_debug = int(cfg.debug.get("limit_num_chunks", 0))

    max_qa_per_group = int(sampling.get("max_qa_per_group", 3))
    max_groups_per_chunk = int(sampling.get("max_groups_per_chunk", 1))
    max_qa_per_document_cfg = sampling.get("max_qa_per_document", 0)

    remaining_qa_for_document = None

    llm_cfg = cfg.llm
    backend = llm_cfg.get("backend", "ollama")
    model = llm_cfg.get("model", "qwen2.5:32b-instruct-q4_K_M")
    temperature = float(llm_cfg.get("temperature", 0.2))
    top_p = float(llm_cfg.get("top_p", 0.9))
    max_tokens = int(llm_cfg.get("max_tokens", 1024))
    num_ctx = int(llm_cfg.get("num_ctx", 8192))
    timeout_s = int(llm_cfg.get("request_timeout_s", 600))
    max_retries = int(llm_cfg.get("max_retries", 3))
    retry_backoff_s = float(llm_cfg.get("retry_backoff_s", 5.0))

    # NEW: prompts.json bundle + hashes (double-pass)
    prompts = load_prompt_bundle(cfg)
    plan_system_hash = sha1_text(prompts.plan_system)
    plan_user_hash = sha1_text(prompts.plan_user)
    gen_system_hash = sha1_text(prompts.gen_system)
    gen_user_hash = sha1_text(prompts.gen_user)

    # legacy keys (keep downstream compatibility)
    system_prompt_hash = gen_system_hash
    user_template_hash = gen_user_hash

    config_hash = sha1_json(cfg.raw)

    # NEW: plan tokens (small budget; overrideable)
    plan_max_tokens = int(llm_cfg.get("plan_max_tokens", min(900, max_tokens)))

    chunks = load_semantic_file(in_path)
    if isinstance(max_qa_per_document_cfg, int) and max_qa_per_document_cfg <= 0:
        remaining_qa_for_document = None
    else:
        doc_total_chars = sum(len((c.get("content") or c.get("text") or "")) for c in chunks)
        max_qa_per_document = compute_max_qa_per_document(max_qa_per_document_cfg, len(chunks), doc_total_chars)
        remaining_qa_for_document = max_qa_per_document
        logger.info(
            f"max_qa_per_document (computed): {max_qa_per_document} (chunks={len(chunks)}, chars={doc_total_chars})"
        )

    if not chunks:
        logging.warning("Keine Chunks in %s gefunden, überspringe.", in_path)
        return 0

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
            logging.info("max_qa_per_document für %s erreicht, breche ab.", in_path.name)
            break

        remaining_global = global_state.get("remaining_global")
        if isinstance(remaining_global, int) and remaining_global <= 0:
            break

        local_neighbors = get_local_neighbors(chunks, idx, cfg)
        local_neighbor_ids = [str(ch.get("chunk_id")) for ch in local_neighbors if ch.get("chunk_id")]

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
            metric_info=metric_info,
        )

        faiss_neighbor_ids = [str(nb.get("chunk_id")) for nb in faiss_neighbors_filtered if nb.get("chunk_id")]
        faiss_neighbor_scores = [float(nb.get("score") or 0.0) for nb in faiss_neighbors_filtered]

        context_groups = build_context_groups(
            candidate=chunk,
            local_neighbors=local_neighbors,
            faiss_neighbors=faiss_neighbors_filtered,
            cfg=cfg,
            max_groups_per_chunk=max_groups_per_chunk,
        )
        if not context_groups:
            continue

        written_any_for_chunk = 0
        num_groups_for_chunk = 0  # attempted groups for this chunk

        for context_group in context_groups:
            if remaining_qa_for_document is not None and remaining_qa_for_document <= 0:
                break

            remaining_global = global_state.get("remaining_global")
            if isinstance(remaining_global, int) and remaining_global <= 0:
                break

            num_groups_for_chunk += 1
            total_groups += 1

            if backend != "ollama":
                raise ValueError(f"Nicht unterstützter LLM-Backend-Typ: {backend!r}")

            if dry_run:
                logging.info(
                    "[Dry-Run] Würde PLAN+GENERATE LLM für chunk_id=%s in %s aufrufen (group %d/%d).",
                    chunk_id,
                    in_path.name,
                    num_groups_for_chunk,
                    len(context_groups),
                )
                continue

            # --------------------
            # PASS 1: PLAN
            # --------------------
            plan_user_prompt = render_prompt(
                context_group=context_group,
                template=prompts.plan_user,
                cfg=cfg,
            )

            try:
                plan_arr = call_llm_ollama_with_retries(
                    system_prompt=prompts.plan_system,
                    user_prompt=plan_user_prompt,
                    model=model,
                    temperature=temperature,
                    top_p=top_p,
                    max_tokens=plan_max_tokens,
                    timeout_s=timeout_s,
                    max_retries=max_retries,
                    retry_backoff_s=retry_backoff_s,
                    num_ctx=num_ctx,
                )
            except Exception as e:
                logging.warning(
                    "LLM-PLAN-Aufruf für chunk_id=%s in %s fehlgeschlagen: %s",
                    chunk_id,
                    in_path.name,
                    e,
                )
                continue

            plan_obj = parse_plan_output(plan_arr)
            if plan_obj is None:
                logging.warning(
                    "PLAN-Output ungültig ... für chunk_id=%s in %s -> FALLBACK: generate without plan",
                    chunk_id,
                    in_path.name,
                )
                plan_obj = {
                    "takeaways": [],
                    "equations_present": False,
                    "equation_quotes": [],
                    "generator_checks": [],
                }
                continue

            plan_json_str = json.dumps(plan_obj, ensure_ascii=False, separators=(",", ":"))

            # --------------------
            # PASS 2: GENERATE
            # --------------------
            user_prompt = render_prompt(
                context_group=context_group,
                template=prompts.gen_user,
                max_qa_per_group=max_qa_per_group,
                plan_json=plan_json_str,
                cfg=cfg,
            )

            try:
                qa_list = call_llm_ollama_with_retries(
                    system_prompt=prompts.gen_system,
                    user_prompt=user_prompt,
                    model=model,
                    temperature=temperature,
                    top_p=top_p,
                    max_tokens=max_tokens,
                    timeout_s=timeout_s,
                    max_retries=max_retries,
                    retry_backoff_s=retry_backoff_s,
                    num_ctx=num_ctx,
                )
            except Exception as e:
                logging.warning(
                    "LLM-GENERATE-Aufruf für chunk_id=%s in %s fehlgeschlagen: %s",
                    chunk_id,
                    in_path.name,
                    e,
                )
                continue

            if not qa_list:
                continue

            written_for_group = 0
            for qa_idx, qa_obj in enumerate(qa_list):
                remaining_global = global_state.get("remaining_global")
                if isinstance(remaining_global, int) and remaining_global <= 0:
                    break

                if not isinstance(qa_obj, dict):
                    continue

                question = qa_obj.get("question")
                answer = qa_obj.get("answer")
                difficulty = qa_obj.get("difficulty")

                if not isinstance(question, str) or not question.strip():
                    continue
                if not isinstance(answer, str) or not answer.strip():
                    continue
                if difficulty not in ("basic", "intermediate", "advanced"):
                    continue

                all_chunk_ids = [c.get("chunk_id") for c in context_group if isinstance(c.get("chunk_id"), str)]
                allowed = set(all_chunk_ids)

                raw_evidence = (
                    qa_obj.get("evidence_chunks")
                    or qa_obj.get("source_chunks")
                    or qa_obj.get("evidence")
                    or []
                )
                evidence = normalize_chunk_id_list(raw_evidence)
                evidence = [cid for cid in evidence if cid in allowed]
                if not evidence:
                    evidence = list(all_chunk_ids)

                context_refs = [make_source_ref(c) for c in context_group]
                evidence_set = set(evidence)
                evidence_refs = [r for r in context_refs if r.get("chunk_id") in evidence_set]

                runtime_cfg = cfg.get("runtime", {}) if isinstance(cfg, dict) else (getattr(cfg, "runtime", {}) or {})
                if runtime_cfg.get("grounding_drop_if_meta_leak", False):
                    if _contains_meta_leak(question) or _contains_meta_leak(answer):
                        continue

                anchor_doc_id = (
                    chunk.get("doc_id")
                    if isinstance(chunk.get("doc_id"), str) and chunk.get("doc_id")
                    else chunk_id.rsplit("_c", 1)[0]
                )
                language = (chunk.get("language") or get_semantic_field(chunk, "language") or "unknown")
                content_types = get_flat_list_field(chunk, "content_type")
                domains = get_flat_list_field(chunk, "domain")
                trust_level = (chunk.get("trust_level") or get_semantic_field(chunk, "trust_level") or "missing")

                out_record = {
                    "id": make_candidate_id(anchor_chunk_id=chunk_id, qa_index=qa_idx, payload=qa_obj),
                    "anchor_chunk_id": chunk_id,
                    "anchor_doc_id": anchor_doc_id,
                    "context_chunks": all_chunk_ids,
                    "source_chunks": evidence,
                    "source_refs": evidence_refs,
                    "context_refs": context_refs,
                    "doc_ids": list(
                        dict.fromkeys([c.get("doc_id") for c in context_group if isinstance(c.get("doc_id"), str)])
                    ),
                    "question": question,
                    "answer": answer,
                    "difficulty": difficulty,
                    "language": language,
                    "content_type": content_types,
                    "domain": domains,
                    "trust_level": trust_level,
                    "workspace_file": in_path.name,
                    "provenance": {
                        "faiss": {
                            "metric": metric_info.metric,
                            "index_type": metric_info.index_type,
                            "normalized": metric_info.normalized,
                            "neighbor_chunk_ids": faiss_neighbor_ids,
                            "neighbor_scores": faiss_neighbor_scores,
                        },
                        "local_neighbor_chunk_ids": local_neighbor_ids,
                        "config_hash": config_hash,
                        "prompts": {
                            "double_pass": True,
                            "plan_system_hash": plan_system_hash,
                            "plan_user_hash": plan_user_hash,
                            "gen_system_hash": gen_system_hash,
                            "gen_user_hash": gen_user_hash,
                        },
                        "system_prompt_hash": system_prompt_hash,
                        "user_template_hash": user_template_hash,
                        "llm": {
                            "backend": backend,
                            "model": model,
                            "temperature": temperature,
                            "top_p": top_p,
                            "num_ctx": num_ctx,
                            "max_tokens_generate": max_tokens,
                            "max_tokens_plan": plan_max_tokens,
                        },
                        "plan": {
                            "equations_present": bool(plan_obj.get("equations_present")),
                            "equation_quotes": plan_obj.get("equation_quotes", []),
                            "generator_checks": plan_obj.get("generator_checks", []),
                            "takeaways": plan_obj.get("takeaways", []),
                        },
                    },
                }

                out_f.write(json.dumps(out_record, ensure_ascii=False) + "\n")
                written_for_group += 1
                total_written += 1

                if remaining_qa_for_document is not None:
                    remaining_qa_for_document -= 1
                    if remaining_qa_for_document <= 0:
                        break

                if isinstance(global_state.get("remaining_global"), int):
                    global_state["remaining_global"] -= 1
                    if global_state["remaining_global"] <= 0:
                        break

            if written_for_group > 0:
                written_any_for_chunk += written_for_group

            if total_written and (total_written % max(1, log_every) == 0):
                logging.info(
                    "Zwischenstand %s: %d Q/A-Paare aus %d Gruppen (attempted).",
                    in_path.name,
                    total_written,
                    total_groups,
                )

        if written_any_for_chunk > 0:
            processed_set.add(chunk_id)

        if isinstance(global_state.get("remaining_global"), int) and global_state["remaining_global"] <= 0:
            break

    out_f.close()

    logging.info(
        "Fertig mit %s: %d Q/A-Paare aus %d Gruppen geschrieben.",
        in_path.name,
        total_written,
        total_groups,
    )
    return total_written

def build_context_groups(
    candidate: Dict[str, Any],
    local_neighbors: Sequence[Dict[str, Any]],
    faiss_neighbors: Sequence[Dict[str, Any]],
    cfg: QAConfig,
    max_groups_per_chunk: int,
) -> List[List[Dict[str, Any]]]:
    """
    Create MULTIPLE context groups per anchor chunk by slicing FAISS neighbors into
    batches that fit into grouping.max_group_size.

    Always includes:
      - candidate (anchor)
      - local neighbors (before/after)
    Then adds FAISS neighbors in windows.

    This makes max_groups_per_chunk actually meaningful.
    """
    grouping = cfg.grouping
    min_group_size = int(grouping.get("min_group_size", 2))
    max_group_size = int(grouping.get("max_group_size", 6))

    seen_ids: set[str] = set()

    def slim_chunk(ch: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        cid = str(ch.get("chunk_id"))
        if not cid or cid in seen_ids:
            return None
        seen_ids.add(cid)

        summary_short = get_semantic_field(ch, "summary_short")
        if not isinstance(summary_short, str):
            summary_short = None

        return {
            "chunk_id": cid,
            "doc_id": ch.get("doc_id"),
            "language": ch.get("language"),
            "trust_level": get_semantic_field(ch, "trust_level"),
            "content_type": get_flat_list_field(ch, "content_type"),
            "domain": get_flat_list_field(ch, "domain"),
            "summary_short": summary_short,
            "content": ch.get("content"),
        }

    # Base always included
    base: List[Dict[str, Any]] = []
    c0 = slim_chunk(candidate)
    if c0:
        base.append(c0)

    for ch in local_neighbors:
        s = slim_chunk(ch)
        if s:
            base.append(s)

    # Slim all FAISS neighbors (unique)
    faiss_slim: List[Dict[str, Any]] = []
    for ch in faiss_neighbors:
        s = slim_chunk(ch)
        if s:
            faiss_slim.append(s)

    # Ensure we can reach min_group_size
    if len(base) >= min_group_size:
        base_prefilled = list(base)
        start_idx = 0
    else:
        need = min_group_size - len(base)
        if len(faiss_slim) < need:
            return []
        base_prefilled = list(base) + faiss_slim[:need]
        start_idx = need

    # Cap base to max_group_size (edge case)
    if len(base_prefilled) > max_group_size:
        base_prefilled = base_prefilled[:max_group_size]

    remaining_slots = max_group_size - len(base_prefilled)

    groups: List[List[Dict[str, Any]]] = []

    if remaining_slots <= 0 or start_idx >= len(faiss_slim):
        groups.append(base_prefilled)
        if max_groups_per_chunk > 0:
            groups = groups[:max_groups_per_chunk]
        return groups

    # Create multiple groups by windowing remaining FAISS neighbors
    i = start_idx
    while i < len(faiss_slim):
        g = base_prefilled + faiss_slim[i : i + remaining_slots]
        if len(g) >= min_group_size:
            groups.append(g)
        i += remaining_slots

        if max_groups_per_chunk > 0 and len(groups) >= max_groups_per_chunk:
            break

    if not groups:
        groups = [base_prefilled]

    return groups


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
    return parser.parse_args(argv)


def setup_logging(level_name: str) -> None:
    level = getattr(logging, level_name.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def load_qa_config(config_path: Optional[str]) -> QAConfig:
    if config_path is not None:
        path = Path(config_path)
    else:
        path = REPO_ROOT / "config" / "qa" / "qa_generation.default.json"

    if not path.exists():
        raise FileNotFoundError(f"QA-Config-Datei nicht gefunden: {path}")

    raw = load_json(path)
    return QAConfig(raw=raw, config_path=path)

def iter_semantic_files(semantic_dir: Path, limit_num_files: int = 0) -> Iterator[Path]:
    """
    Yields *.jsonl files from semantic_dir (sorted for determinism).
    limit_num_files <= 0 means: no limit.
    """
    files = sorted(semantic_dir.glob("*.jsonl"))
    if limit_num_files and limit_num_files > 0:
        files = files[:limit_num_files]
    for p in files:
        yield p

def main(argv: Optional[Sequence[str]] = None) -> None:
    args = parse_args(argv)
    cfg = load_qa_config(args.config)

    log_level = args.log_level or cfg.runtime.get("log_level") or "INFO"
    setup_logging(log_level)

    logging.info("Starte generate_qa_candidates.py")
    logging.info("Verwendete Config: %s", cfg.config_path)

    workspace_root: Path
    if args.workspace_root:
        workspace_root = Path(args.workspace_root).expanduser().resolve()
    else:
        ws_cfg = cfg.paths.get("workspace_root")
        if ws_cfg:
            workspace_root = Path(ws_cfg).expanduser().resolve()
        elif get_path is not None:
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

    metric_info = load_faiss_metric_info(workspace_root)

    retriever = FaissRetriever(workspace_root=str(workspace_root))

    logging.info("Semantic-Verzeichnis: %s", semantic_dir)
    logging.info("QA-Candidates-Verzeichnis: %s", qa_candidates_dir)
    logging.info(
        "FAISS Metric: metric=%s index_type=%s normalized=%s higher_is_better=%s",
        metric_info.metric,
        metric_info.index_type,
        metric_info.normalized,
        metric_info.higher_is_better,
    )

    semantic_files = list(iter_semantic_files(semantic_dir, limit_num_files))

    # Sharding anwenden: einfacher Modulo-Split über den Index (analog zu annotate_semantics.py)
    if args.num_shards < 1:
        raise SystemExit("--num-shards muss >= 1 sein")
    if args.shard_id < 0 or args.shard_id >= args.num_shards:
        raise SystemExit("--shard-id muss in [0, num-shards) liegen")

    if args.num_shards == 1:
        semantic_files_sharded = semantic_files
    else:
        semantic_files_sharded = [
            f for idx, f in enumerate(semantic_files) if idx % args.num_shards == args.shard_id
        ]

    semantic_files = semantic_files_sharded

    logging.info(
        "Sharding: shard_id=%d / num_shards=%d -> %d semantic-Dateien",
        args.shard_id,
        args.num_shards,
        len(semantic_files),
    )

    if not semantic_files:
        logging.warning("Keine semantic/json-Dateien in %s gefunden.", semantic_dir)
        return

    global_qa_limit = int(cfg.sampling.get("global_qa_limit", 0))

    # Hinweis: Wenn wir per Sharding auf mehrere Jobs skalieren, ist ein "globales" Limit über alle Shards
    # ohne Koordination nicht sauber durchsetzbar. Daher teilen wir ein gesetztes global_qa_limit auf die Shards auf.
    if global_qa_limit > 0 and args.num_shards > 1:
        global_qa_limit = int(math.ceil(global_qa_limit / float(args.num_shards)))
        logging.info(
            "global_qa_limit wird auf Shards aufgeteilt -> pro Shard: %d",
            global_qa_limit,
        )

    global_state: Dict[str, Any] = {
        "remaining_global": global_qa_limit if global_qa_limit > 0 else None
    }

    total_written_global = 0
    t_start = time.time()

    for in_path in semantic_files:
        remaining_global = global_state.get("remaining_global")
        if isinstance(remaining_global, int) and remaining_global <= 0:
            break

        in_basename = in_path.stem
        pattern = cfg.output.get("output_file_pattern", "{input_basename}.qa_candidates.jsonl")
        out_name = pattern.format(input_basename=in_basename)
        out_path = qa_candidates_dir / out_name

        written = process_semantic_file(
            in_path=in_path,
            out_path=out_path,
            cfg=cfg,
            retriever=retriever,
            metric_info=metric_info,
            global_state=global_state,
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
