#!/usr/bin/env python3
"""
qa_candidate_stats.py

Statistik für QA-Candidates:
- Wie viele Q/A wurden pro anchor_chunk_id erzeugt?
- Wie ungleich ist die Verteilung (Gini, Pareto-Anteile)?
- Top-Listen (Chunks / Docs)

Input:
  <workspace_root>/qa_candidates/jsonl/*.jsonl

Outputs:
  <workspace_root>/logs/statistics/
    qa_candidate_stats_<timestamp>.txt
    qa_candidate_stats_<timestamp>.json
    qa_candidate_counts_per_chunk_<timestamp>.csv

Robustheit:
- kaputte JSONL-Zeilen werden gezählt und übersprungen
- Feld-Fallbacks, falls sich Keys unterscheiden
- workspace_root wird bevorzugt via:
  1) --workspace-root
  2) ENV: DACHS_WORKSPACE_ROOT
  3) config/paths/paths.json (top-level "workspace_root")
  4) paths_utils.get_path("workspace_root") (falls bei euch doch vorhanden)
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import os
import statistics
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
import importlib.util
from typing import Any, Dict, Iterator, List, Optional, Tuple


# ----------------------------
# Paths: optional paths_utils
# ----------------------------

def load_paths_utils(repo_root: Path):
    """
    Lädt config/paths/paths_utils.py dynamisch.
    Gibt (get_path_func, paths_config_path) zurück oder (None, paths_json_path).
    """
    paths_dir = repo_root / "config" / "paths"
    pu = paths_dir / "paths_utils.py"
    pj = paths_dir / "paths.json"

    if not pu.is_file():
        return None, pj

    spec = importlib.util.spec_from_file_location("dachs_paths_utils", pu)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)  # type: ignore

    # paths_utils definiert bei euch vermutlich PATHS_CONFIG_PATH,
    # aber wir sind tolerant und geben notfalls repo-relative paths.json zurück.
    paths_config_path = Path(getattr(mod, "PATHS_CONFIG_PATH", pj)).expanduser()
    return getattr(mod, "get_path", None), paths_config_path


def find_repo_root(start: Path) -> Path:
    """
    Heuristik: gehe nach oben, bis ein 'config' Ordner existiert.
    """
    p = start.resolve()
    for _ in range(8):
        if (p / "config").is_dir():
            return p
        p = p.parent
    return start.resolve()


def read_workspace_root_from_paths_json(paths_json: Path) -> Optional[Path]:
    """
    Erwartet paths.json im Format:
    {
      "workspace_root": "/beegfs/scratch/workspace/...",
      "paths": { ... }
    }
    """
    try:
        data = json.loads(paths_json.read_text(encoding="utf-8"))
    except Exception:
        return None

    wr = data.get("workspace_root")
    if isinstance(wr, str) and wr.strip():
        return Path(wr).expanduser().resolve()
    return None


# ----------------------------
# JSONL iterator
# ----------------------------

def iter_jsonl(path: Path) -> Iterator[Tuple[int, Dict[str, Any]]]:
    with path.open("r", encoding="utf-8") as f:
        for i, line in enumerate(f, start=1):
            s = line.strip()
            if not s:
                continue
            try:
                obj = json.loads(s)
            except Exception:
                yield i, {"__parse_error__": True, "__raw__": s[:200]}
                continue
            if not isinstance(obj, dict):
                yield i, {"__parse_error__": True, "__raw__": str(type(obj))}
                continue
            yield i, obj


# ----------------------------
# Stats helpers
# ----------------------------

def gini(values: List[int]) -> float:
    """
    Gini-Koeffizient für nichtnegative Integer.
    0 = perfekt gleich, 1 = maximal ungleich.
    """
    if not values:
        return 0.0
    vals = sorted(v for v in values if v >= 0)
    n = len(vals)
    s = sum(vals)
    if s == 0:
        return 0.0
    cum = 0
    for i, x in enumerate(vals, start=1):
        cum += i * x
    return (2.0 * cum) / (n * s) - (n + 1) / n


def pareto_shares(values: List[int], top_fracs: List[float]) -> Dict[str, float]:
    """
    Anteil der Gesamt-QA, der von den Top-X% Chunks kommt.
    """
    out: Dict[str, float] = {}
    if not values:
        for f in top_fracs:
            out[f"top_{int(f*100)}pct_share"] = 0.0
        return out

    vals = sorted(values, reverse=True)
    total = sum(vals)
    if total <= 0:
        for f in top_fracs:
            out[f"top_{int(f*100)}pct_share"] = 0.0
        return out

    n = len(vals)
    for f in top_fracs:
        k = max(1, int(math.ceil(n * f)))
        out[f"top_{int(f*100)}pct_share"] = sum(vals[:k]) / total
    return out


def pctl(values: List[int], q: float) -> float:
    if not values:
        return 0.0
    vals = sorted(values)
    if q <= 0:
        return float(vals[0])
    if q >= 1:
        return float(vals[-1])
    idx = int(round(q * (len(vals) - 1)))
    return float(vals[idx])


def first_str(*cands: Any) -> Optional[str]:
    for c in cands:
        if isinstance(c, str) and c.strip():
            return c.strip()
    return None


# ----------------------------
# Core
# ----------------------------

@dataclass
class RunStats:
    files: int = 0
    lines_total: int = 0
    lines_bad: int = 0
    qa_total: int = 0
    unique_chunks: int = 0
    unique_docs: int = 0


def resolve_workspace_root(args_workspace_root: Optional[str], repo_root: Path) -> Path:
    """
    Resolve workspace_root robustly.
    Priority:
      1) CLI --workspace-root
      2) ENV DACHS_WORKSPACE_ROOT
      3) config/paths/paths.json top-level workspace_root
      4) paths_utils.get_path("workspace_root") if exists
    """
    if args_workspace_root:
        return Path(args_workspace_root).expanduser().resolve()

    env_wr = os.environ.get("DACHS_WORKSPACE_ROOT", "").strip()
    if env_wr:
        return Path(env_wr).expanduser().resolve()

    get_path, paths_json = load_paths_utils(repo_root)

    # 3) direct read of paths.json (top-level "workspace_root")
    wr = read_workspace_root_from_paths_json(paths_json)
    if wr is not None:
        return wr

    # 4) last resort: ask paths_utils (only works if your paths.json contains it the way get_path expects)
    if get_path is not None:
        try:
            return Path(get_path("workspace_root")).expanduser().resolve()
        except Exception:
            pass

    raise SystemExit(
        "workspace_root konnte nicht ermittelt werden.\n"
        "Nutze entweder:\n"
        "  - --workspace-root /beegfs/scratch/workspace/<workspace>\n"
        "oder setze ENV:\n"
        "  - export DACHS_WORKSPACE_ROOT=/beegfs/scratch/workspace/<workspace>\n"
        "oder trage in config/paths/paths.json ein top-level Feld 'workspace_root' ein."
    )


def main() -> None:
    ap = argparse.ArgumentParser(description="QA candidates stats: how many questions per chunk?")
    ap.add_argument("--workspace-root", type=str, default=None, help="Workspace root (contains qa_candidates/).")
    ap.add_argument("--qa-dir", type=str, default=None, help="Override QA candidates dir (points to .../qa_candidates/jsonl).")
    ap.add_argument("--pattern", type=str, default="*.jsonl", help="File glob inside qa dir.")
    ap.add_argument("--top-n", type=int, default=50, help="Top-N chunks to list.")
    ap.add_argument("--min-qa", type=int, default=1, help="Only include chunks with >= min-qa (default 1).")
    args = ap.parse_args()

    repo_root = find_repo_root(Path(__file__).resolve())
    workspace_root = resolve_workspace_root(args.workspace_root, repo_root)

    # resolve qa dir
    if args.qa_dir:
        qa_dir = Path(args.qa_dir).expanduser().resolve()
    else:
        qa_dir = workspace_root / "qa_candidates" / "jsonl"

    if not qa_dir.is_dir():
        raise SystemExit(f"QA candidates dir not found: {qa_dir}")

    out_dir = workspace_root / "logs" / "statistics"
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    out_txt = out_dir / f"qa_candidate_stats_{ts}.txt"
    out_json = out_dir / f"qa_candidate_stats_{ts}.json"
    out_csv = out_dir / f"qa_candidate_counts_per_chunk_{ts}.csv"

    # counters
    per_chunk = Counter()
    per_doc = Counter()
    per_chunk_difficulty = defaultdict(Counter)  # chunk_id -> Counter(difficulty)
    per_chunk_lang = defaultdict(Counter)

    # optional metadata per chunk
    chunk_meta: Dict[str, Dict[str, Any]] = {}

    rs = RunStats()

    files = sorted(qa_dir.glob(args.pattern))
    rs.files = len(files)
    if not files:
        raise SystemExit(f"No files in {qa_dir} matching {args.pattern}")

    for fp in files:
        for _line_no, obj in iter_jsonl(fp):
            rs.lines_total += 1
            if obj.get("__parse_error__"):
                rs.lines_bad += 1
                continue

            anchor_chunk = first_str(
                obj.get("anchor_chunk_id"),
                obj.get("chunk_id"),
                obj.get("anchor_chunk"),
            )
            if not anchor_chunk:
                continue

            anchor_doc = first_str(obj.get("anchor_doc_id"), obj.get("doc_id"))
            difficulty = first_str(obj.get("difficulty"))
            language = first_str(obj.get("language"))

            per_chunk[anchor_chunk] += 1
            rs.qa_total += 1

            if anchor_doc:
                per_doc[anchor_doc] += 1

            if difficulty:
                per_chunk_difficulty[anchor_chunk][difficulty] += 1
            if language:
                per_chunk_lang[anchor_chunk][language] += 1

            if anchor_chunk not in chunk_meta:
                chunk_meta[anchor_chunk] = {
                    "anchor_doc_id": anchor_doc,
                    "workspace_file": obj.get("workspace_file"),
                }

    # apply min-qa filter
    if args.min_qa > 1:
        per_chunk = Counter({k: v for k, v in per_chunk.items() if v >= args.min_qa})

    rs.unique_chunks = len(per_chunk)
    rs.unique_docs = len(per_doc)

    values = list(per_chunk.values())

    summary: Dict[str, Any] = {
        "run": {
            "workspace_root": str(workspace_root),
            "qa_dir": str(qa_dir),
            "pattern": args.pattern,
            "timestamp": ts,
        },
        "io": {
            "files": rs.files,
            "lines_total": rs.lines_total,
            "lines_bad": rs.lines_bad,
            "qa_total_counted": rs.qa_total,
            "unique_anchor_chunks": rs.unique_chunks,
            "unique_anchor_docs": rs.unique_docs,
        },
        "per_chunk_distribution": {
            "min": int(min(values)) if values else 0,
            "max": int(max(values)) if values else 0,
            "mean": float(statistics.mean(values)) if values else 0.0,
            "median": float(statistics.median(values)) if values else 0.0,
            "p90": pctl(values, 0.90),
            "p95": pctl(values, 0.95),
            "p99": pctl(values, 0.99),
            "gini": gini(values),
            **pareto_shares(values, top_fracs=[0.01, 0.05, 0.10, 0.20]),
        },
        "top_chunks": [],
        "top_docs": [],
    }

    top_chunks = per_chunk.most_common(max(1, args.top_n))
    for chunk_id, cnt in top_chunks:
        md = chunk_meta.get(chunk_id, {})
        summary["top_chunks"].append(
            {
                "anchor_chunk_id": chunk_id,
                "qa_count": int(cnt),
                "anchor_doc_id": md.get("anchor_doc_id"),
                "workspace_file": md.get("workspace_file"),
                "difficulty_counts": dict(per_chunk_difficulty.get(chunk_id, {})),
                "language_counts": dict(per_chunk_lang.get(chunk_id, {})),
            }
        )

    for doc_id, cnt in per_doc.most_common(50):
        summary["top_docs"].append({"anchor_doc_id": doc_id, "qa_count": int(cnt)})

    out_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    with out_csv.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["anchor_chunk_id", "qa_count", "anchor_doc_id", "workspace_file", "difficulty_counts", "language_counts"])
        for chunk_id, cnt in per_chunk.most_common():
            md = chunk_meta.get(chunk_id, {})
            w.writerow(
                [
                    chunk_id,
                    int(cnt),
                    md.get("anchor_doc_id") or "",
                    md.get("workspace_file") or "",
                    json.dumps(dict(per_chunk_difficulty.get(chunk_id, {})), ensure_ascii=False),
                    json.dumps(dict(per_chunk_lang.get(chunk_id, {})), ensure_ascii=False),
                ]
            )

    lines: List[str] = []
    lines.append("QA Candidate Stats")
    lines.append(f"- workspace_root: {workspace_root}")
    lines.append(f"- qa_dir: {qa_dir}")
    lines.append(f"- files: {rs.files}")
    lines.append(f"- lines_total: {rs.lines_total}")
    lines.append(f"- lines_bad: {rs.lines_bad}")
    lines.append(f"- qa_total_counted: {rs.qa_total}")
    lines.append(f"- unique_anchor_chunks: {rs.unique_chunks}")
    lines.append(f"- unique_anchor_docs: {rs.unique_docs}")
    lines.append("")
    dist = summary["per_chunk_distribution"]
    lines.append("Per-chunk QA distribution (counts per anchor_chunk_id):")
    for k in ["min", "max", "mean", "median", "p90", "p95", "p99", "gini", "top_1pct_share", "top_5pct_share", "top_10pct_share", "top_20pct_share"]:
        if k in dist:
            lines.append(f"- {k}: {dist[k]}")
    lines.append("")
    lines.append(f"Top {min(args.top_n, len(top_chunks))} chunks:")
    for row in summary["top_chunks"][: min(args.top_n, len(summary["top_chunks"]))]:
        lines.append(f"- {row['qa_count']:>4}  {row['anchor_chunk_id']}  doc={row.get('anchor_doc_id')}")
    lines.append("")
    lines.append("Outputs:")
    lines.append(f"- {out_txt}")
    lines.append(f"- {out_json}")
    lines.append(f"- {out_csv}")
    out_txt.write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"[OK] Wrote:\n- {out_txt}\n- {out_json}\n- {out_csv}")


if __name__ == "__main__":
    main()
