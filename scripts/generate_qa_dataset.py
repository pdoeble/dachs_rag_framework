#!/usr/bin/env python3
"""
generate_qa_dataset.py

Schritt 6 (Masterplan): Filterung & Qualitätssicherung
  qa_candidates/jsonl/  ->  qa_final/jsonl/

Aufgaben:
- Kandidaten (JSONL) laden und validieren
- Heuristische Filter anwenden (Längen, Pflichtfelder, Quellen, erlaubte Labels)
- Dubletten entfernen (exact)
- Finales Instruction-Tuning-JSONL erzeugen (Schema nach Masterplan)
- Versionierung (auto vN) + CHANGELOG.md
- Optional: Rejects-Datei mit Drop-Gründen

Design-Prinzip:
- Pfade kommen aus config/paths/paths.json ("single source of truth").
- Dieses Script benötigt KEINE LLM- oder FAISS-Konfiguration.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional, Set, Tuple


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[1] if (Path(__file__).resolve().parents[1] / "config").exists() else Path(__file__).resolve().parent


def load_json_file(path: Path) -> Any:
    if not path.is_file():
        raise FileNotFoundError(f"JSON-Datei nicht gefunden: {path}")
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def read_jsonl(path: Path) -> Iterator[Tuple[int, Dict[str, Any]]]:
    """Yield (line_no, obj) for valid JSON objects. Invalid lines are skipped with log warning."""
    with path.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            s = line.strip()
            if not s:
                continue
            try:
                obj = json.loads(s)
            except Exception:
                logging.warning("Invalid JSON in %s line %d - skipping.", path.name, i)
                continue
            if not isinstance(obj, dict):
                logging.warning("Non-dict JSON in %s line %d - skipping.", path.name, i)
                continue
            yield i, obj


def safe_slug(s: str, max_len: int = 40) -> str:
    s = s.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s[:max_len] if len(s) > max_len else s


def detect_lang_simple(text: str) -> str:
    """
    Sehr grobe Heuristik (kein externes Paket):
    - viele Umlaute/ß => de
    - viele typische englische Funktionswörter => en
    - sonst unknown
    """
    t = text.lower()
    de_mark = sum(t.count(ch) for ch in "äöüß")
    en_words = len(re.findall(r"\b(the|and|or|of|to|in|for|with|is|are)\b", t))
    de_words = len(re.findall(r"\b(der|die|das|und|oder|mit|für|ist|sind)\b", t))
    if de_mark >= 2 or de_words > en_words + 2:
        return "de"
    if en_words > de_words + 2:
        return "en"
    return "unknown"


def sha1_16(s: str) -> str:
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Path resolution (single source of truth)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class ResolvedPaths:
    workspace_root: Path
    qa_candidates_dir: Path
    qa_final_dir: Path


def resolve_paths(paths_file: Path) -> ResolvedPaths:
    cfg = load_json_file(paths_file)
    if not isinstance(cfg, dict):
        raise ValueError(f"paths.json must be an object: {paths_file}")

    workspace_root = cfg.get("workspace_root")
    paths = cfg.get("paths")

    if not isinstance(workspace_root, str) or not workspace_root.strip():
        raise ValueError(f"paths.json missing 'workspace_root' string: {paths_file}")
    if not isinstance(paths, dict):
        raise ValueError(f"paths.json missing 'paths' object: {paths_file}")

    def need(key: str) -> Path:
        v = paths.get(key)
        if not isinstance(v, str) or not v.strip():
            raise ValueError(f"paths.json missing paths.{key}: {paths_file}")
        return Path(workspace_root) / v

    return ResolvedPaths(
        workspace_root=Path(workspace_root),
        qa_candidates_dir=need("qa_candidates"),
        qa_final_dir=need("qa_final"),
    )


# ---------------------------------------------------------------------------
# Config model
# ---------------------------------------------------------------------------

@dataclass
class DatasetConfig:
    # paths
    paths_file: Path

    # input
    file_glob: str = "*.jsonl"

    # mapping
    instruction_from: str = "question"
    output_from: str = "answer"
    input_value: str = ""

    # filters
    require_fields: Tuple[str, ...] = ("question", "answer")
    require_nonempty_sources: bool = True
    min_question_chars: int = 20
    max_question_chars: int = 600
    min_answer_chars: int = 30
    max_answer_chars: int = 2000
    languages_allowed: Tuple[str, ...] = ("de", "en")
    trust_levels_allowed: Tuple[str, ...] = ("high", "medium")
    content_types_allowed: Tuple[str, ...] = ("textbook", "handbook", "paper", "simulation_report", "api_doc", "software_manual")
    drop_if_language_mismatch: bool = False

    # dedup
    dedup_mode: str = "exact"          # exact only for now
    dedup_keys: Tuple[str, ...] = ("question", "answer")
    dedup_keep: str = "first"          # first only for now

    # output
    dataset_name: str = "qa_final"
    qa_schema_version: str = "v1"
    version: str = "auto"              # auto or vN
    output_file_pattern: str = "{dataset_name}_{version}.jsonl"
    write_changelog: bool = True
    changelog_filename: str = "CHANGELOG.md"

    # id strategy
    workspace_abbr: str = "ws"
    id_strategy: str = "sequential"    # sequential | candidate | hash
    id_zero_pad: int = 5

    # runtime
    resume_mode: str = "overwrite"     # overwrite|resume|append
    dry_run: bool = False
    log_every_n: int = 2000

    # debug
    limit_num_files: int = 0
    limit_num_examples: int = 0
    write_rejects_jsonl: bool = True
    rejects_filename: str = "qa_rejects_{version}.jsonl"


def load_dataset_config(config_path: Path) -> DatasetConfig:
    raw = load_json_file(config_path)
    if not isinstance(raw, dict):
        raise ValueError(f"Config must be a JSON object: {config_path}")

    paths = raw.get("paths", {})
    if not isinstance(paths, dict):
        raise ValueError("config.paths must be an object")

    paths_file = paths.get("paths_file", "config/paths/paths.json")
    paths_file_p = Path(paths_file)
    if not paths_file_p.is_absolute():
        paths_file_p = (REPO_ROOT / paths_file_p).resolve()

    input_cfg = raw.get("input", {})
    mapping = raw.get("mapping", {})
    filters = raw.get("filters", {})
    dedup = raw.get("dedup", {})
    output = raw.get("output", {})
    runtime = raw.get("runtime", {})
    debug = raw.get("debug", {})
    ids = raw.get("id", {}) or raw.get("ids", {})  # allow either key

    def ttuple(v: Any) -> Tuple[str, ...]:
        if v is None:
            return tuple()
        if isinstance(v, list):
            return tuple(str(x) for x in v)
        return (str(v),)

    cfg = DatasetConfig(paths_file=paths_file_p)

    # input
    if isinstance(input_cfg, dict):
        cfg.file_glob = str(input_cfg.get("file_glob", cfg.file_glob))

    # mapping
    if isinstance(mapping, dict):
        cfg.instruction_from = str(mapping.get("instruction_from", cfg.instruction_from))
        cfg.output_from = str(mapping.get("output_from", cfg.output_from))
        cfg.input_value = str(mapping.get("input_value", cfg.input_value))

    # filters
    if isinstance(filters, dict):
        cfg.require_fields = ttuple(filters.get("require_fields", list(cfg.require_fields)))
        cfg.require_nonempty_sources = bool(filters.get("require_nonempty_sources", cfg.require_nonempty_sources))
        cfg.min_question_chars = int(filters.get("min_question_chars", cfg.min_question_chars))
        cfg.max_question_chars = int(filters.get("max_question_chars", cfg.max_question_chars))
        cfg.min_answer_chars = int(filters.get("min_answer_chars", cfg.min_answer_chars))
        cfg.max_answer_chars = int(filters.get("max_answer_chars", cfg.max_answer_chars))
        cfg.languages_allowed = ttuple(filters.get("languages_allowed", list(cfg.languages_allowed)))
        cfg.trust_levels_allowed = ttuple(filters.get("trust_levels_allowed", list(cfg.trust_levels_allowed)))
        cfg.content_types_allowed = ttuple(filters.get("content_types_allowed", list(cfg.content_types_allowed)))
        cfg.drop_if_language_mismatch = bool(filters.get("drop_if_language_mismatch", cfg.drop_if_language_mismatch))

    # dedup
    if isinstance(dedup, dict):
        cfg.dedup_mode = str(dedup.get("mode", cfg.dedup_mode))
        cfg.dedup_keys = ttuple(dedup.get("keys", list(cfg.dedup_keys)))
        cfg.dedup_keep = str(dedup.get("keep", cfg.dedup_keep))

    # output
    if isinstance(output, dict):
        cfg.dataset_name = str(output.get("dataset_name", cfg.dataset_name))
        cfg.qa_schema_version = str(output.get("qa_schema_version", cfg.qa_schema_version))
        cfg.version = str(output.get("version", cfg.version))
        cfg.output_file_pattern = str(output.get("output_file_pattern", cfg.output_file_pattern))
        cfg.write_changelog = bool(output.get("write_changelog", cfg.write_changelog))
        cfg.changelog_filename = str(output.get("changelog_filename", cfg.changelog_filename))

    # id
    if isinstance(ids, dict):
        cfg.workspace_abbr = str(ids.get("workspace_abbr", cfg.workspace_abbr))
        cfg.id_strategy = str(ids.get("strategy", cfg.id_strategy))
        cfg.id_zero_pad = int(ids.get("zero_pad", cfg.id_zero_pad))

    # runtime
    if isinstance(runtime, dict):
        cfg.resume_mode = str(runtime.get("resume_mode", cfg.resume_mode))
        cfg.dry_run = bool(runtime.get("dry_run", cfg.dry_run))
        cfg.log_every_n = int(runtime.get("log_every_n", cfg.log_every_n))

    # debug
    if isinstance(debug, dict):
        cfg.limit_num_files = int(debug.get("limit_num_files", cfg.limit_num_files))
        cfg.limit_num_examples = int(debug.get("limit_num_examples", cfg.limit_num_examples))
        cfg.write_rejects_jsonl = bool(debug.get("write_rejects_jsonl", cfg.write_rejects_jsonl))
        cfg.rejects_filename = str(debug.get("rejects_filename", cfg.rejects_filename))

    return cfg


# ---------------------------------------------------------------------------
# Versioning
# ---------------------------------------------------------------------------

_VERSION_RE = re.compile(r"_v(\d+)\.jsonl$", re.IGNORECASE)


def infer_next_version(qa_final_dir: Path, dataset_name: str) -> str:
    """
    Finds highest existing {dataset_name}_vN.jsonl and returns v(N+1).
    """
    if not qa_final_dir.exists():
        return "v1"
    max_n = 0
    for p in qa_final_dir.glob(f"{dataset_name}_v*.jsonl"):
        m = _VERSION_RE.search(p.name)
        if not m:
            continue
        try:
            n = int(m.group(1))
            max_n = max(max_n, n)
        except Exception:
            continue
    return f"v{max_n + 1}"


# ---------------------------------------------------------------------------
# Core build
# ---------------------------------------------------------------------------

@dataclass
class Counters:
    read: int = 0
    kept: int = 0
    dropped: int = 0
    duped: int = 0


def _get_list(x: Any) -> List[Any]:
    if x is None:
        return []
    if isinstance(x, list):
        return x
    return [x]


def _first_nonempty_str(*vals: Any) -> Optional[str]:
    for v in vals:
        if isinstance(v, str) and v.strip():
            return v.strip()
    return None


def validate_and_map_candidate(
    cand: Dict[str, Any],
    cfg: DatasetConfig,
    version: str,
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Returns (final_sample, reject_reason).
    """
    # required fields
    for k in cfg.require_fields:
        v = cand.get(k)
        if not isinstance(v, str) or not v.strip():
            return None, f"missing_or_empty:{k}"

    q = str(cand.get(cfg.instruction_from, "")).strip()
    a = str(cand.get(cfg.output_from, "")).strip()

    if len(q) < cfg.min_question_chars:
        return None, "question_too_short"
    if len(q) > cfg.max_question_chars:
        return None, "question_too_long"
    if len(a) < cfg.min_answer_chars:
        return None, "answer_too_short"
    if len(a) > cfg.max_answer_chars:
        return None, "answer_too_long"

    # allowed labels (if present)
    lang = _first_nonempty_str(cand.get("language"))
    if lang and cfg.languages_allowed and lang not in cfg.languages_allowed:
        return None, "language_not_allowed"

    trust = _first_nonempty_str(cand.get("trust_level"))
    if trust and cfg.trust_levels_allowed and trust not in cfg.trust_levels_allowed:
        return None, "trust_level_not_allowed"

    ctype = cand.get("content_type")
    if ctype is not None:
        ctypes = [str(x) for x in _get_list(ctype) if str(x).strip()]
        if ctypes and cfg.content_types_allowed:
            if not any(ct in cfg.content_types_allowed for ct in ctypes):
                return None, "content_type_not_allowed"
    else:
        ctypes = []

    # sources
    source_chunks = cand.get("source_chunks")
    if cfg.require_nonempty_sources:
        if not isinstance(source_chunks, list) or len(source_chunks) == 0:
            return None, "missing_sources"

    # optional language mismatch heuristic
    if cfg.drop_if_language_mismatch and lang in ("de", "en"):
        detected = detect_lang_simple(q + " " + a)
        if detected in ("de", "en") and detected != lang:
            return None, "language_mismatch"

    # Build final schema (Masterplan 4.3)
    source_ids: List[str] = []
    if isinstance(source_chunks, list):
        for cid in source_chunks:
            if isinstance(cid, str) and cid.strip():
                source_ids.append(f"chunk:{cid.strip()}")
    elif isinstance(cand.get("anchor_chunk_id"), str):
        source_ids.append(f"chunk:{cand['anchor_chunk_id']}")

    out: Dict[str, Any] = {
        # id filled later
        "id": None,
        "instruction": q,
        "input": cfg.input_value,
        "output": a,
        "language": lang or "unknown",
        "content_type": [str(x) for x in _get_list(cand.get("content_type")) if str(x).strip()],
        "domain": [str(x) for x in _get_list(cand.get("domain")) if str(x).strip()],
        "trust_level": trust or "unknown",
        "source_ids": source_ids,
        "created_by": "llm_auto",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "version": version,
        # provenance kept for auditability
        "provenance": cand.get("provenance", {}),
        # links back to candidate
        "candidate_id": cand.get("id"),
        "anchor_chunk_id": cand.get("anchor_chunk_id"),
        "anchor_doc_id": cand.get("anchor_doc_id"),
        "difficulty": cand.get("difficulty"),
    }

    # optional workspace/topic (best effort)
    out["workspace"] = _first_nonempty_str(cand.get("workspace"), cand.get("workspace_name")) or ""

    topic = _first_nonempty_str(cand.get("topic"))
    if not topic:
        # crude default: first domain if present
        doms = out.get("domain") or []
        if doms:
            topic = safe_slug(str(doms[0]))
    out["topic"] = topic or ""

    return out, None


def make_id(cfg: DatasetConfig, seq: int, sample: Dict[str, Any]) -> str:
    if cfg.id_strategy == "candidate":
        cid = sample.get("candidate_id")
        if isinstance(cid, str) and cid.strip():
            return cid.strip()
    if cfg.id_strategy == "hash":
        base = sample.get("anchor_chunk_id") or ""
        base += "\n" + sample.get("instruction", "")
        base += "\n" + sample.get("output", "")
        h = sha1_16(base)
        return f"{cfg.workspace_abbr}_{h}_q1"
    # default: sequential
    n = str(seq).zfill(cfg.id_zero_pad)
    return f"{cfg.workspace_abbr}_{n}_q1"


def dedup_key(sample: Dict[str, Any], keys: Tuple[str, ...]) -> str:
    parts: List[str] = []
    for k in keys:
        v = sample.get(k)
        if isinstance(v, str):
            parts.append(v.strip())
        else:
            parts.append(str(v))
    return "\n".join(parts)


def write_changelog(changelog_path: Path, version: str, stats: Dict[str, Any], out_file: str) -> None:
    ts = datetime.now(timezone.utc).isoformat()
    lines = [
        f"## {version} - {ts}",
        "",
        f"- output: `{out_file}`",
        f"- kept: {stats.get('kept')}",
        f"- read: {stats.get('read')}",
        f"- dropped: {stats.get('dropped')}",
        f"- duplicates_removed: {stats.get('duped')}",
        "",
        f"- filters: {json.dumps(stats.get('filters', {}), ensure_ascii=False)}",
        "",
    ]
    if changelog_path.exists():
        old = changelog_path.read_text(encoding="utf-8")
        changelog_path.write_text("\n".join(lines) + "\n" + old, encoding="utf-8")
    else:
        changelog_path.write_text("# QA Dataset Changelog\n\n" + "\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Generate final QA dataset from QA candidates (merge/filter/dedup/version).")
    p.add_argument("--config", type=str, default="config/qa/qa_dataset.default.json", help="Path to dataset config JSON.")
    p.add_argument("--log-level", type=str, default=None, help="Override log level (DEBUG/INFO/...).")
    p.add_argument("--version", type=str, default=None, help="Override output version (auto|vN).")
    p.add_argument("--resume-mode", type=str, default=None, help="Override resume mode (overwrite|resume|append).")
    p.add_argument("--dry-run", action="store_true", help="Do not write output files.")
    p.add_argument("--limit-num-files", type=int, default=None, help="Debug: limit number of input files.")
    p.add_argument("--limit-num-examples", type=int, default=None, help="Debug: limit number of kept examples.")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = (REPO_ROOT / config_path).resolve()

    cfg = load_dataset_config(config_path)

    # overrides
    if args.log_level:
        logging.basicConfig(level=getattr(logging, args.log_level.upper(), logging.INFO), format="%(asctime)s [%(levelname)s] %(message)s")
    else:
        logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    if args.version is not None:
        cfg.version = args.version
    if args.resume_mode is not None:
        cfg.resume_mode = args.resume_mode
    if args.dry_run:
        cfg.dry_run = True
    if args.limit_num_files is not None:
        cfg.limit_num_files = args.limit_num_files
    if args.limit_num_examples is not None:
        cfg.limit_num_examples = args.limit_num_examples

    paths = resolve_paths(cfg.paths_file)

    qa_candidates_dir = paths.qa_candidates_dir
    qa_final_dir = paths.qa_final_dir

    if not qa_candidates_dir.exists():
        raise FileNotFoundError(f"qa_candidates_dir does not exist: {qa_candidates_dir}")

    qa_final_dir.mkdir(parents=True, exist_ok=True)

    # determine version
    version = cfg.version
    if version.lower() == "auto":
        version = infer_next_version(qa_final_dir, cfg.dataset_name)

    out_name = cfg.output_file_pattern.format(dataset_name=cfg.dataset_name, version=version)
    out_path = qa_final_dir / out_name

    rejects_path = qa_final_dir / cfg.rejects_filename.format(version=version)
    changelog_path = qa_final_dir / cfg.changelog_filename

    # resume handling
    existing_ids: Set[str] = set()
    if cfg.resume_mode in ("resume", "append") and out_path.exists():
        for _, obj in read_jsonl(out_path):
            oid = obj.get("id")
            if isinstance(oid, str) and oid.strip():
                existing_ids.add(oid.strip())
        logging.info("Resume enabled: loaded %d existing ids from %s", len(existing_ids), out_path.name)

    # gather input files
    in_files = sorted(qa_candidates_dir.glob(cfg.file_glob))
    if cfg.limit_num_files and cfg.limit_num_files > 0:
        in_files = in_files[: cfg.limit_num_files]

    logging.info("Input: %d files from %s", len(in_files), qa_candidates_dir)
    logging.info("Output: %s", out_path)

    counters = Counters()
    dedup_seen: Set[str] = set()

    kept_samples: List[Dict[str, Any]] = []
    rejects: List[Dict[str, Any]] = []

    seq = 0
    for fp in in_files:
        for line_no, cand in read_jsonl(fp):
            counters.read += 1

            sample, reason = validate_and_map_candidate(cand, cfg, version)
            if reason:
                counters.dropped += 1
                if cfg.write_rejects_jsonl:
                    rejects.append(
                        {
                            "reason": reason,
                            "file": fp.name,
                            "line": line_no,
                            "candidate_id": cand.get("id"),
                            "anchor_chunk_id": cand.get("anchor_chunk_id"),
                        }
                    )
                continue

            assert sample is not None

            # dedup
            if cfg.dedup_mode == "exact":
                k = dedup_key(sample, cfg.dedup_keys)
                if k in dedup_seen:
                    counters.duped += 1
                    continue
                dedup_seen.add(k)

            # assign id
            seq += 1
            sample_id = make_id(cfg, seq, sample)
            sample["id"] = sample_id

            if cfg.resume_mode in ("resume", "append") and sample_id in existing_ids:
                continue

            kept_samples.append(sample)
            counters.kept += 1

            if cfg.log_every_n > 0 and counters.kept % cfg.log_every_n == 0:
                logging.info("Progress kept=%d read=%d dropped=%d duped=%d", counters.kept, counters.read, counters.dropped, counters.duped)

            if cfg.limit_num_examples and cfg.limit_num_examples > 0 and counters.kept >= cfg.limit_num_examples:
                break
        if cfg.limit_num_examples and cfg.limit_num_examples > 0 and counters.kept >= cfg.limit_num_examples:
            break

    stats = {
        "read": counters.read,
        "kept": counters.kept,
        "dropped": counters.dropped,
        "duped": counters.duped,
        "filters": {
            "min_question_chars": cfg.min_question_chars,
            "max_question_chars": cfg.max_question_chars,
            "min_answer_chars": cfg.min_answer_chars,
            "max_answer_chars": cfg.max_answer_chars,
            "languages_allowed": list(cfg.languages_allowed),
            "trust_levels_allowed": list(cfg.trust_levels_allowed),
            "content_types_allowed": list(cfg.content_types_allowed),
            "require_nonempty_sources": cfg.require_nonempty_sources,
            "drop_if_language_mismatch": cfg.drop_if_language_mismatch,
            "dedup": {"mode": cfg.dedup_mode, "keys": list(cfg.dedup_keys)},
            "id": {"strategy": cfg.id_strategy, "workspace_abbr": cfg.workspace_abbr, "zero_pad": cfg.id_zero_pad},
        },
    }

    logging.info("Done: kept=%d read=%d dropped=%d duped=%d", counters.kept, counters.read, counters.dropped, counters.duped)

    if cfg.dry_run:
        logging.info("Dry-run enabled: not writing output files.")
        return

    # write output
    write_mode = "w"
    if cfg.resume_mode == "append" and out_path.exists():
        write_mode = "a"

    with out_path.open(write_mode, encoding="utf-8") as f:
        for s in kept_samples:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")

    if cfg.write_rejects_jsonl and rejects:
        with rejects_path.open("w", encoding="utf-8") as f:
            for r in rejects:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    if cfg.write_changelog:
        write_changelog(changelog_path, version, stats, out_path.name)

    logging.info("Wrote %d samples to %s", counters.kept, out_path)
    if cfg.write_rejects_jsonl:
        logging.info("Wrote %d rejects to %s", len(rejects), rejects_path)


if __name__ == "__main__":
    main()
