#!/usr/bin/env python
"""
semantic_quality_stats.py

Erweitert:
- berechnet Qualitätsstatistiken wie zuvor
- schreibt zusätzlich eine Datei mit Zeitstempel nach:
    <workspace_root>/logs/statistics/semantic_stats_<timestamp>.txt
- Pfade werden NICHT hardcodiert, sondern aus config/paths/paths_utils.py geladen
"""

from __future__ import annotations
import argparse
import json
from pathlib import Path
from collections import Counter
from datetime import datetime
import importlib.util
import sys


# --------------------------------------------------------------------
# Pfade & get_path aus config/paths/paths_utils.py laden
# --------------------------------------------------------------------

def load_paths_utils():
    """
    Lädt get_path() und REPO_ROOT dynamisch aus config/paths/paths_utils.py.
    """
    this_dir = Path(__file__).resolve().parent
    repo_root = this_dir.parent
    paths_utils_path = repo_root / "config" / "paths" / "paths_utils.py"

    if not paths_utils_path.is_file():
        raise RuntimeError(f"paths_utils.py nicht gefunden: {paths_utils_path}")

    spec = importlib.util.spec_from_file_location("dachs_paths_utils", paths_utils_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore

    return module.get_path, module.REPO_ROOT


get_path, REPO_ROOT = load_paths_utils()


# --------------------------------------------------------------------
# Hilfsfunktion JSONL iterieren
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
# Hauptlogik
# --------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Erzeugt Qualitätsstatistiken der semantischen Annotationen "
                    "und speichert sie zusätzlich in eine Datei mit Zeitstempel."
    )
    parser.add_argument(
        "--input-dir",
        type=str,
        default=None,
        help="Optional: semantic/json Verzeichnis. "
             "Standard: get_path('semantic_json')"
    )
    args = parser.parse_args()

    # semantic/json Pfad auflösen
    if args.input_dir is not None:
        input_dir = Path(args.input_dir).expanduser().resolve()
    else:
        input_dir = Path(get_path("semantic_json")).expanduser().resolve()

    if not input_dir.is_dir():
        raise SystemExit(f"Eingabeverzeichnis existiert nicht: {input_dir}")

    files = sorted(input_dir.glob("*.jsonl"))
    if not files:
        raise SystemExit(f"Keine JSONL-Dateien in {input_dir} gefunden.")

    print(f"[INFO] Analysiere {len(files)} Dateien in {input_dir}")

    # Gesamtzähler
    total_chunks = 0

    lang_counter = Counter()
    trust_counter = Counter()

    list_fields = ["content_type", "domain", "artifact_role", "chunk_role"]
    list_nonempty = Counter()
    list_empty = Counter()

    summary_len_bins = Counter()
    chunks_with_eq = 0
    total_eq = 0
    chunks_with_kq = 0
    total_kq = 0

    per_doc_missing_domain = Counter()
    per_doc_missing_ct = Counter()

    # Verarbeitung
    for fpath in files:
        for rec in iter_jsonl(fpath):
            total_chunks += 1

            doc_id = rec.get("doc_id") or rec.get("title") or fpath.name
            lang = str(rec.get("language", "unknown")).lower()
            lang_counter[lang] += 1

            sem = rec.get("semantic") or {}
            if not isinstance(sem, dict):
                sem = {}

            trust = str(sem.get("trust_level", "missing")).strip() or "missing"
            trust_counter[trust] += 1

            for fld in list_fields:
                val = sem.get(fld)
                if isinstance(val, list) and len(val) > 0:
                    list_nonempty[fld] += 1
                else:
                    list_empty[fld] += 1
                    if fld == "domain":
                        per_doc_missing_domain[doc_id] += 1
                    if fld == "content_type":
                        per_doc_missing_ct[doc_id] += 1

            summary = str(sem.get("summary_short", "") or "")
            L = len(summary)
            if L < 10:
                summary_len_bins["<10"] += 1
            elif L < 40:
                summary_len_bins["10-40"] += 1
            elif L < 120:
                summary_len_bins["40-120"] += 1
            else:
                summary_len_bins[">=120"] += 1

            eqs = sem.get("equations")
            if isinstance(eqs, list) and len(eqs) > 0:
                chunks_with_eq += 1
                total_eq += len(eqs)

            kq = sem.get("key_quantities")
            if isinstance(kq, list) and len(kq) > 0:
                chunks_with_kq += 1
                total_kq += len(kq)

    # ------------------------------------------------------------------------
    # Report erzeugen (Terminal + Datei)
    # ------------------------------------------------------------------------

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # workspace_root aus get_path() holen
    workspace_root = get_path("", default_relative="").resolve()

    out_dir = workspace_root / "logs" / "statistics"
    out_dir.mkdir(parents=True, exist_ok=True)

    out_file = out_dir / f"semantic_stats_{timestamp}.txt"

    # alles in dieses String-Buffer schreiben
    lines = []
    w = lines.append

    w(f"[INFO] Analysiere {len(files)} Dateien in {input_dir}\n")
    w("=== Gesamt ===")
    w(f"Total chunks: {total_chunks}\n")

    w("=== language-Verteilung ===")
    for lang, cnt in lang_counter.most_common():
        frac = cnt / total_chunks * 100
        w(f"  {lang:10s}: {cnt:8d}  ({frac:5.1f}%)")

    w("\n=== trust_level-Verteilung ===")
    for tl, cnt in trust_counter.most_common():
        frac = cnt / total_chunks * 100
        w(f"  {tl:10s}: {cnt:8d}  ({frac:5.1f}%)")

    w("\n=== Listenfelder ===")
    for fld in list_fields:
        ne = list_nonempty[fld]
        e = list_empty[fld]
        w(f"  {fld:12s}: nonempty={ne:8d}, empty={e:8d}")

    w("\n=== summary_short-Längen ===")
    for bin_name, cnt in summary_len_bins.most_common():
        frac = cnt / total_chunks * 100
        w(f"  {bin_name:7s}: {cnt:8d} ({frac:5.1f}%)")

    w("\n=== equations / key_quantities ===")
    if total_chunks:
        w(f"Chunks mit equations: {chunks_with_eq} ({chunks_with_eq/total_chunks*100:.1f}%)")
        w(f"Ø equations pro betroffenen Chunk: {total_eq / chunks_with_eq if chunks_with_eq else 0:.2f}")
        w(f"Chunks mit key_quantities: {chunks_with_kq} ({chunks_with_kq/total_chunks*100:.1f}%)")
        w(f"Ø key_quantities pro betroffenen Chunk: {total_kq / chunks_with_kq if chunks_with_kq else 0:.2f}")

    w("\n=== Top-Docs mit fehlender domain ===")
    for doc, cnt in per_doc_missing_domain.most_common(10):
        w(f"  {doc}: {cnt} Chunks ohne domain")

    w("\n=== Top-Docs mit fehlendem content_type ===")
    for doc, cnt in per_doc_missing_ct.most_common(10):
        w(f"  {doc}: {cnt} Chunks ohne content_type")

    # In Datei schreiben
    out_file.write_text("\n".join(lines), encoding="utf-8")

    # In Terminal ausgeben
    print("\n".join(lines))
    print(f"\n[INFO] Statistik gespeichert unter:\n  {out_file}")


if __name__ == "__main__":
    main()
