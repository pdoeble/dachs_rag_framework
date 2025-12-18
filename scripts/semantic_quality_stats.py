#!/usr/bin/env python
"""
semantic_quality_stats.py

Diagnostik-Version:
- klassische Stats (language, trust_level, list fields, summary, equations, key_quantities)
- zusätzliche Diagnose:
  1) text quality metrics (falls Textfeld vorhanden)
  2) heuristische "suspect_structural" Klassifikation (ohne artifact_role-hint)
  3) Cross-Stats: unknown vs empty fields vs suspect_structural
  4) Per-Doc Health: unknown-rate, empty-text-rate, suspect-rate (Top-Listen)
  5) Optional: Beispiel-Dumps als JSONL

Outputs:
- TXT:  <workspace_root>/logs/statistics/semantic_stats_<timestamp>.txt
- JSON: <workspace_root>/logs/statistics/semantic_stats_<timestamp>.json
- optional examples: <workspace_root>/logs/statistics/examples_<timestamp>.jsonl

Pfade:
- get_path() dynamisch aus config/paths/paths_utils.py
"""

from __future__ import annotations

import argparse
import json
import random
import statistics
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
import importlib.util


# --------------------------------------------------------------------
# Pfade & get_path aus config/paths/paths_utils.py laden
# --------------------------------------------------------------------

def load_paths_utils():
    this_dir = Path(__file__).resolve().parent
    repo_root = this_dir.parent
    paths_utils_path = repo_root / "config" / "paths" / "paths_utils.py"
    if not paths_utils_path.is_file():
        raise RuntimeError(f"paths_utils.py nicht gefunden: {paths_utils_path}")

    spec = importlib.util.spec_from_file_location("dachs_paths_utils", paths_utils_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)  # type: ignore
    return module.get_path, module.REPO_ROOT


get_path, REPO_ROOT = load_paths_utils()


# --------------------------------------------------------------------
# JSONL iterator
# --------------------------------------------------------------------

def iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            t = line.strip()
            if not t:
                continue
            try:
                yield json.loads(t)
            except json.JSONDecodeError:
                continue


# --------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------

TEXT_FIELD_CANDIDATES = [
    "text",
    "chunk_text",
    "content",
    "normalized_text",
    "raw_text",
    "body",
    "page_text",
    "md",
]

def extract_text(rec: dict) -> str:
    """
    Versucht, einen plausiblen Textstring im Record zu finden.
    """
    for k in TEXT_FIELD_CANDIDATES:
        v = rec.get(k)
        if isinstance(v, str) and v.strip():
            return v
    # manchmal steckt Text verschachtelt
    for k in ["chunk", "data", "payload"]:
        v = rec.get(k)
        if isinstance(v, dict):
            for kk in TEXT_FIELD_CANDIDATES:
                vv = v.get(kk)
                if isinstance(vv, str) and vv.strip():
                    return vv
    return ""


def safe_list(val):
    return val if isinstance(val, list) else []


def percentile(data, p: float) -> float:
    if not data:
        return 0.0
    if p <= 0:
        return float(min(data))
    if p >= 100:
        return float(max(data))
    s = sorted(data)
    k = (len(s) - 1) * (p / 100.0)
    f = int(k)
    c = min(f + 1, len(s) - 1)
    if f == c:
        return float(s[f])
    d0 = s[f] * (c - k)
    d1 = s[c] * (k - f)
    return float(d0 + d1)


def text_quality_metrics(s: str) -> dict:
    """
    Grobe, robuste Textqualitätsmetriken:
    - len_chars
    - alnum_ratio
    - whitespace_ratio
    - non_ascii_ratio
    """
    if not s:
        return {"len_chars": 0, "alnum_ratio": 0.0, "whitespace_ratio": 0.0, "non_ascii_ratio": 0.0}

    n = len(s)
    alnum = sum(1 for ch in s if ch.isalnum())
    ws = sum(1 for ch in s if ch.isspace())
    non_ascii = sum(1 for ch in s if ord(ch) > 127)

    return {
        "len_chars": n,
        "alnum_ratio": alnum / n,
        "whitespace_ratio": ws / n,
        "non_ascii_ratio": non_ascii / n,
    }


def is_suspect_structural(
    lang: str,
    sem: dict,
    text_len: int,
    summary_len: int,
) -> bool:
    """
    Heuristik: "suspect_structural/garbage" wenn mehrere Indikatoren gleichzeitig:
    - language unknown
    - domain/content_type leer
    - summary leer/ultrakurz
    - chunk_role leer
    - keine equations und keine key_quantities
    - Text sehr kurz ODER extrem wenig Alnum (über separate Metriken)
    """
    dom = sem.get("domain")
    ct = sem.get("content_type")
    cr = sem.get("chunk_role")

    dom_ok = isinstance(dom, list) and len(dom) > 0
    ct_ok = isinstance(ct, list) and len(ct) > 0
    cr_ok = isinstance(cr, list) and len(cr) > 0

    eqs = sem.get("equations")
    kq = sem.get("key_quantities")
    has_eq = isinstance(eqs, list) and len(eqs) > 0
    has_kq = isinstance(kq, list) and len(kq) > 0

    very_short_text = text_len > 0 and text_len < 80

    return (
        (lang == "unknown")
        and (not dom_ok)
        and (not ct_ok)
        and (summary_len < 10)
        and (not cr_ok)
        and (not has_eq)
        and (not has_kq)
        and (very_short_text or text_len == 0)
    )


# --------------------------------------------------------------------
# Main
# --------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Semantic quality stats + deeper diagnostics.")
    parser.add_argument(
        "--input-dir",
        type=str,
        default=None,
        help="Optional: semantic/json Verzeichnis. Standard: get_path('semantic_json')",
    )
    parser.add_argument(
        "--min-doc-chunks",
        type=int,
        default=500,
        help="Mindestanzahl Chunks pro Doc für Rate-Listen.",
    )
    parser.add_argument(
        "--dump-examples",
        action="store_true",
        help="Wenn gesetzt: schreibe Beispiele 'bad chunks' als JSONL.",
    )
    parser.add_argument(
        "--max-examples",
        type=int,
        default=300,
        help="Max Anzahl Beispiele (Reservoir Sampling).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Seed für Beispiele.",
    )
    args = parser.parse_args()

    # Input dir
    if args.input_dir is not None:
        input_dir = Path(args.input_dir).expanduser().resolve()
    else:
        input_dir = Path(get_path("semantic_json")).expanduser().resolve()

    if not input_dir.is_dir():
        raise SystemExit(f"Eingabeverzeichnis existiert nicht: {input_dir}")

    files = sorted(input_dir.glob("*.jsonl"))
    if not files:
        raise SystemExit(f"Keine JSONL-Dateien in {input_dir} gefunden.")

    # workspace root
    workspace_root_raw = get_path("", default_relative="")
    workspace_root = Path(workspace_root_raw).expanduser().resolve()

    out_dir = workspace_root / "logs" / "statistics"
    out_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_txt = out_dir / f"semantic_stats_{timestamp}.txt"
    out_json = out_dir / f"semantic_stats_{timestamp}.json"
    out_examples = out_dir / f"examples_{timestamp}.jsonl"

    rnd = random.Random(args.seed)

    # ----------------------------------------------------------------
    # Counters / stats
    # ----------------------------------------------------------------
    total_chunks = 0

    lang_counter = Counter()
    trust_counter = Counter()

    list_fields = ["content_type", "domain", "artifact_role", "chunk_role"]
    list_nonempty = Counter()
    list_empty = Counter()
    list_malformed = Counter()

    # Summary stats
    summary_len_bins = Counter()
    summary_lens = []
    summary_empty = 0
    summary_too_long = 0  # >=300 chars heuristic

    # equations / key_quantities
    chunks_with_eq = 0
    total_eq = 0
    chunks_with_kq = 0
    total_kq = 0

    # Text quality
    text_lens = []
    text_empty = 0
    alnum_ratios = []
    non_ascii_ratios = []
    whitespace_ratios = []

    # Suspect structural heuristic
    suspect_total = 0
    suspect_by_lang = Counter()
    suspect_by_doc = Counter()

    # Cross unknown vs empty fields
    unknown_total = 0
    unknown_domain_empty = 0
    unknown_ct_empty = 0
    unknown_suspect = 0

    # Per-doc rates
    per_doc_total = Counter()
    per_doc_unknown = Counter()
    per_doc_text_empty = Counter()
    per_doc_domain_empty = Counter()
    per_doc_ct_empty = Counter()

    # Integrity
    missing_semantic = 0
    malformed_semantic = 0

    # Top IDs
    top_domain_ids = Counter()
    top_ct_ids = Counter()
    top_ar_ids = Counter()
    top_cr_ids = Counter()

    # Examples
    examples = []

    def maybe_add_example(rec: dict, reason: str) -> None:
        if not args.dump_examples:
            return
        if args.max_examples <= 0:
            return
        nonlocal examples
        r = dict(rec)
        r["_example_reason"] = reason
        # add snippet for quick viewing
        txt = extract_text(rec)
        if txt:
            r["_text_snippet"] = txt[:300]
        if len(examples) < args.max_examples:
            examples.append(r)
        else:
            j = rnd.randrange(0, total_chunks + 1)
            if j < args.max_examples:
                examples[j] = r

    # ----------------------------------------------------------------
    # Process
    # ----------------------------------------------------------------
    for fpath in files:
        for rec in iter_jsonl(fpath):
            total_chunks += 1

            doc_id = rec.get("doc_id") or rec.get("title") or fpath.name
            per_doc_total[doc_id] += 1

            lang = str(rec.get("language", "unknown")).lower().strip() or "unknown"
            lang_counter[lang] += 1
            if lang == "unknown":
                unknown_total += 1
                per_doc_unknown[doc_id] += 1

            sem = rec.get("semantic", None)
            if sem is None:
                missing_semantic += 1
                sem = {}
            if not isinstance(sem, dict):
                malformed_semantic += 1
                sem = {}

            trust = str(sem.get("trust_level", "missing")).strip() or "missing"
            trust_counter[trust] += 1

            # List fields + top IDs
            for fld in list_fields:
                val = sem.get(fld, None)
                if val is None:
                    list_empty[fld] += 1
                    if fld == "domain":
                        per_doc_domain_empty[doc_id] += 1
                        if lang == "unknown":
                            unknown_domain_empty += 1
                    if fld == "content_type":
                        per_doc_ct_empty[doc_id] += 1
                        if lang == "unknown":
                            unknown_ct_empty += 1
                    continue

                if isinstance(val, list):
                    if len(val) > 0:
                        list_nonempty[fld] += 1
                        for x in val:
                            if not isinstance(x, str):
                                continue
                            xs = x.strip()
                            if not xs:
                                continue
                            if fld == "domain":
                                top_domain_ids[xs] += 1
                            elif fld == "content_type":
                                top_ct_ids[xs] += 1
                            elif fld == "artifact_role":
                                top_ar_ids[xs] += 1
                            elif fld == "chunk_role":
                                top_cr_ids[xs] += 1
                    else:
                        list_empty[fld] += 1
                        if fld == "domain":
                            per_doc_domain_empty[doc_id] += 1
                            if lang == "unknown":
                                unknown_domain_empty += 1
                        if fld == "content_type":
                            per_doc_ct_empty[doc_id] += 1
                            if lang == "unknown":
                                unknown_ct_empty += 1
                else:
                    list_malformed[fld] += 1
                    list_empty[fld] += 1
                    if fld == "domain":
                        per_doc_domain_empty[doc_id] += 1
                        if lang == "unknown":
                            unknown_domain_empty += 1
                    if fld == "content_type":
                        per_doc_ct_empty[doc_id] += 1
                        if lang == "unknown":
                            unknown_ct_empty += 1

            # Summary
            summary = str(sem.get("summary_short", "") or "")
            sL = len(summary)
            summary_lens.append(sL)
            if sL == 0:
                summary_empty += 1
            if sL >= 300:
                summary_too_long += 1

            if sL < 10:
                summary_len_bins["<10"] += 1
            elif sL < 40:
                summary_len_bins["10-40"] += 1
            elif sL < 120:
                summary_len_bins["40-120"] += 1
            else:
                summary_len_bins[">=120"] += 1

            # Equations / key_quantities
            eqs = sem.get("equations")
            if isinstance(eqs, list) and len(eqs) > 0:
                chunks_with_eq += 1
                total_eq += len(eqs)

            kq = sem.get("key_quantities")
            if isinstance(kq, list) and len(kq) > 0:
                chunks_with_kq += 1
                total_kq += len(kq)

            # Text quality
            txt = extract_text(rec)
            qm = text_quality_metrics(txt)
            tl = int(qm["len_chars"])
            text_lens.append(tl)
            if tl == 0:
                text_empty += 1
                per_doc_text_empty[doc_id] += 1

            alnum_ratios.append(float(qm["alnum_ratio"]))
            non_ascii_ratios.append(float(qm["non_ascii_ratio"]))
            whitespace_ratios.append(float(qm["whitespace_ratio"]))

            # Suspect heuristic (structural/garbage proxy)
            suspect = is_suspect_structural(lang=lang, sem=sem, text_len=tl, summary_len=sL)
            if suspect:
                suspect_total += 1
                suspect_by_lang[lang] += 1
                suspect_by_doc[doc_id] += 1
                if lang == "unknown":
                    unknown_suspect += 1
                maybe_add_example(rec, "suspect_structural_heuristic")

            # Additional examples: extreme unknown + empty domain/ct
            dom = sem.get("domain")
            ct = sem.get("content_type")
            dom_empty = not (isinstance(dom, list) and len(dom) > 0)
            ct_empty = not (isinstance(ct, list) and len(ct) > 0)
            if lang == "unknown" and (dom_empty or ct_empty):
                maybe_add_example(rec, "unknown_and_domain_or_ct_empty")

            if tl == 0:
                maybe_add_example(rec, "empty_text")

    # ----------------------------------------------------------------
    # Report
    # ----------------------------------------------------------------
    def pct(x: int, denom: int) -> float:
        return (x / denom * 100.0) if denom else 0.0

    lines = []
    w = lines.append

    w(f"[INFO] Analysiere {len(files)} Dateien in {input_dir}\n")

    w("=== Gesamt ===")
    w(f"Total chunks: {total_chunks}")
    w(f"Semantic missing (semantic=None): {missing_semantic} ({pct(missing_semantic, total_chunks):.2f}%)")
    w(f"Semantic malformed (semantic not dict): {malformed_semantic} ({pct(malformed_semantic, total_chunks):.2f}%)")
    w("")

    w("=== language-Verteilung ===")
    for k, v in lang_counter.most_common():
        w(f"  {k:10s}: {v:8d} ({pct(v, total_chunks):5.1f}%)")
    w("")

    w("=== trust_level-Verteilung ===")
    for k, v in trust_counter.most_common():
        w(f"  {k:10s}: {v:8d} ({pct(v, total_chunks):5.1f}%)")
    w("")

    w("=== Listenfelder (gesamt) ===")
    for fld in list_fields:
        w(f"  {fld:12s}: nonempty={list_nonempty[fld]:8d}, empty={list_empty[fld]:8d}, malformed={list_malformed[fld]:6d}")
    w("")

    w("=== unknown-language Cross ===")
    w(f"unknown total: {unknown_total} ({pct(unknown_total, total_chunks):.1f}%)")
    w(f"domain empty WHEN language=unknown:       {unknown_domain_empty} ({pct(unknown_domain_empty, unknown_total):.1f}% of unknown)")
    w(f"content_type empty WHEN language=unknown: {unknown_ct_empty} ({pct(unknown_ct_empty, unknown_total):.1f}% of unknown)")
    w(f"suspect_structural WHEN language=unknown: {unknown_suspect} ({pct(unknown_suspect, unknown_total):.1f}% of unknown)")
    w("")

    w("=== suspect_structural (heuristic) ===")
    w(f"Total suspect_structural: {suspect_total} ({pct(suspect_total, total_chunks):.1f}%)")
    for k, v in suspect_by_lang.most_common():
        w(f"  {k:10s}: {v:8d} ({pct(v, total_chunks):5.1f}%)")
    w("")

    w("=== summary_short-Längen (Bins) ===")
    for bin_name, cnt in summary_len_bins.most_common():
        w(f"  {bin_name:7s}: {cnt:8d} ({pct(cnt, total_chunks):5.1f}%)")
    w("")

    w("=== summary_short-Statistik (chars) ===")
    mean_len = statistics.mean(summary_lens) if summary_lens else 0.0
    med_len = statistics.median(summary_lens) if summary_lens else 0.0
    p90 = percentile(summary_lens, 90.0)
    p99 = percentile(summary_lens, 99.0)
    w(f"mean: {mean_len:.1f} | median: {med_len:.1f} | p90: {p90:.1f} | p99: {p99:.1f}")
    w(f"empty: {summary_empty} ({pct(summary_empty, total_chunks):.1f}%)")
    w(f">=300 chars: {summary_too_long} ({pct(summary_too_long, total_chunks):.1f}%)")
    w("")

    w("=== equations / key_quantities ===")
    w(f"Chunks mit equations: {chunks_with_eq} ({pct(chunks_with_eq, total_chunks):.1f}%)")
    w(f"Ø equations pro betroffenen Chunk: {total_eq / chunks_with_eq if chunks_with_eq else 0:.2f}")
    w(f"Chunks mit key_quantities: {chunks_with_kq} ({pct(chunks_with_kq, total_chunks):.1f}%)")
    w(f"Ø key_quantities pro betroffenen Chunk: {total_kq / chunks_with_kq if chunks_with_kq else 0:.2f}")
    w("")

    w("=== Textqualität (falls Textfeld gefunden) ===")
    w(f"empty text: {text_empty} ({pct(text_empty, total_chunks):.1f}%)")
    w(f"text len mean: {statistics.mean(text_lens) if text_lens else 0.0:.1f} | "
      f"median: {statistics.median(text_lens) if text_lens else 0.0:.1f} | "
      f"p90: {percentile(text_lens, 90.0):.1f} | p99: {percentile(text_lens, 99.0):.1f}")
    w(f"alnum_ratio mean: {statistics.mean(alnum_ratios) if alnum_ratios else 0.0:.3f}")
    w(f"whitespace_ratio mean: {statistics.mean(whitespace_ratios) if whitespace_ratios else 0.0:.3f}")
    w(f"non_ascii_ratio mean: {statistics.mean(non_ascii_ratios) if non_ascii_ratios else 0.0:.3f}")
    w("")

    # Per-doc rate tables
    def top_by_rate(title: str, num_fn, denom_fn, min_chunks: int, topn: int = 10):
        items = []
        for doc, tot in per_doc_total.items():
            if tot < min_chunks:
                continue
            num = num_fn(doc)
            rate = num / tot if tot else 0.0
            items.append((rate, num, tot, doc))
        items.sort(reverse=True)
        w(title)
        for rate, num, tot, doc in items[:topn]:
            w(f"  {doc}: {num}/{tot} ({rate*100:.1f}%)")
        w("")

    top_by_rate(
        f"=== Top-Docs unknown-language (Rate, min_chunks={args.min_doc_chunks}) ===",
        lambda d: per_doc_unknown[d],
        lambda d: per_doc_total[d],
        args.min_doc_chunks,
    )
    top_by_rate(
        f"=== Top-Docs empty text (Rate, min_chunks={args.min_doc_chunks}) ===",
        lambda d: per_doc_text_empty[d],
        lambda d: per_doc_total[d],
        args.min_doc_chunks,
    )
    top_by_rate(
        f"=== Top-Docs domain missing (Rate, min_chunks={args.min_doc_chunks}) ===",
        lambda d: per_doc_domain_empty[d],
        lambda d: per_doc_total[d],
        args.min_doc_chunks,
    )
    top_by_rate(
        f"=== Top-Docs content_type missing (Rate, min_chunks={args.min_doc_chunks}) ===",
        lambda d: per_doc_ct_empty[d],
        lambda d: per_doc_total[d],
        args.min_doc_chunks,
    )
    top_by_rate(
        f"=== Top-Docs suspect_structural (Rate, min_chunks={args.min_doc_chunks}) ===",
        lambda d: suspect_by_doc[d],
        lambda d: per_doc_total[d],
        args.min_doc_chunks,
    )

    # Top IDs
    def write_top(counter: Counter, title: str, n: int = 15):
        w(title)
        for k, v in counter.most_common(n):
            w(f"  {k}: {v} ({pct(v, total_chunks):.1f}%)")
        w("")

    write_top(top_ct_ids, "=== Top content_type IDs ===")
    write_top(top_domain_ids, "=== Top domain IDs ===")
    write_top(top_ar_ids, "=== Top artifact_role IDs ===")
    write_top(top_cr_ids, "=== Top chunk_role IDs ===")

    out_txt.write_text("\n".join(lines), encoding="utf-8")

    summary = {
        "timestamp": timestamp,
        "input_dir": str(input_dir),
        "files": len(files),
        "total_chunks": total_chunks,
        "language": dict(lang_counter),
        "trust_level": dict(trust_counter),
        "list_fields": {
            "nonempty": dict(list_nonempty),
            "empty": dict(list_empty),
            "malformed": dict(list_malformed),
        },
        "unknown_cross": {
            "unknown_total": unknown_total,
            "unknown_domain_empty": unknown_domain_empty,
            "unknown_content_type_empty": unknown_ct_empty,
            "unknown_suspect_structural": unknown_suspect,
        },
        "suspect_structural": {
            "total": suspect_total,
            "by_language": dict(suspect_by_lang),
        },
        "summary_short": {
            "bins": dict(summary_len_bins),
            "mean": float(mean_len),
            "median": float(med_len),
            "p90": float(p90),
            "p99": float(p99),
            "empty": summary_empty,
            "too_long_ge_300": summary_too_long,
        },
        "equations": {
            "chunks_with_equations": chunks_with_eq,
            "total_equations": total_eq,
            "avg_per_affected_chunk": (total_eq / chunks_with_eq) if chunks_with_eq else 0.0,
        },
        "key_quantities": {
            "chunks_with_key_quantities": chunks_with_kq,
            "total_key_quantities": total_kq,
            "avg_per_affected_chunk": (total_kq / chunks_with_kq) if chunks_with_kq else 0.0,
        },
        "text_quality": {
            "empty_text": text_empty,
            "len_mean": float(statistics.mean(text_lens) if text_lens else 0.0),
            "len_median": float(statistics.median(text_lens) if text_lens else 0.0),
            "len_p90": float(percentile(text_lens, 90.0)),
            "len_p99": float(percentile(text_lens, 99.0)),
            "alnum_ratio_mean": float(statistics.mean(alnum_ratios) if alnum_ratios else 0.0),
            "whitespace_ratio_mean": float(statistics.mean(whitespace_ratios) if whitespace_ratios else 0.0),
            "non_ascii_ratio_mean": float(statistics.mean(non_ascii_ratios) if non_ascii_ratios else 0.0),
        },
        "semantic_integrity": {
            "missing_semantic": missing_semantic,
            "malformed_semantic": malformed_semantic,
        },
        "top_ids": {
            "content_type": top_ct_ids.most_common(25),
            "domain": top_domain_ids.most_common(25),
            "artifact_role": top_ar_ids.most_common(25),
            "chunk_role": top_cr_ids.most_common(25),
        },
    }
    out_json.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.dump_examples:
        with out_examples.open("w", encoding="utf-8") as f:
            for r in examples:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print("\n".join(lines))
    print(f"\n[INFO] TXT gespeichert unter:\n  {out_txt}")
    print(f"[INFO] JSON gespeichert unter:\n  {out_json}")
    if args.dump_examples:
        print(f"[INFO] Beispiele gespeichert unter:\n  {out_examples}")


if __name__ == "__main__":
    main()
