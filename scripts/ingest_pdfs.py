#!/usr/bin/env python
"""
ingest_pdfs.py

CLI-Script zum Einlesen von PDF-Dateien aus einem Rohdaten-Verzeichnis
und Schreiben einer normalisierten JSONL-Repräsentation in ein
Ausgabe-Verzeichnis (normalized/json/).

Jede PDF-Datei wird in Text-Chunks zerlegt. Jeder Chunk ist ein JSON-Record
mit Metadaten (doc_id, chunk_id, Seitenbereich, Quelle, etc.), der sich
nahtlos in die weiteren Pipeline-Schritte (semantische Anreicherung,
Q/A-Generierung, RAG-Index) einfügt.

Aus Sicht des Masterplans ist das Schritt 1: "Ingestion & Normalisierung".
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Dict, Any


# ---------------------------------------------------------------------------
# Datenstrukturen
# ---------------------------------------------------------------------------

@dataclass
class Chunk:
    """Repräsentiert einen Text-Chunk einer PDF-Datei."""
    text: str
    page_start: int  # 0-basiert
    page_end: int    # inkl., 0-basiert


# ---------------------------------------------------------------------------
# Hilfsfunktionen
# ---------------------------------------------------------------------------

def setup_logging(verbose: bool) -> None:
    """Einfaches Logging-Setup für CLI-Ausführung."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="[%(levelname)s] %(message)s",
        stream=sys.stderr,
    )


def find_pdfs(input_dir: Path) -> List[Path]:
    """
    Finde alle PDF-Dateien im Eingabeverzeichnis (rekursiv).
    Gibt eine sortierte Liste zurück, um deterministische Reihenfolge zu haben.
    """
    pdfs = sorted(p for p in input_dir.rglob("*.pdf") if p.is_file())
    return pdfs


def load_pdf_pages(pdf_path: Path) -> List[str]:
    """
    Extrahiere Text aus einem PDF als Liste von Strings, einer pro Seite.

    Hinweis:
    - benötigt das Paket "pypdf" (siehe env/requirements.txt).
    - leere Seiten werden als leere Strings ("") zurückgegeben.
    """
    try:
        from pypdf import PdfReader
    except ImportError as exc:
        raise RuntimeError(
            "Das Paket 'pypdf' ist nicht installiert. "
            "Bitte in env/requirements.txt ergänzen und bootstrap_env.sh ausführen."
        ) from exc

    reader = PdfReader(str(pdf_path))

    page_texts: List[str] = []
    for page_index, page in enumerate(reader.pages):
        # extract_text kann None liefern, wenn kein Text erkannt wird
        text = page.extract_text() or ""
        # Normalize line breaks einheitlich auf '\n'
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        # Whitespace trimmen
        text = text.strip()
        page_texts.append(text)

    return page_texts


def chunk_pages(
    page_texts: List[str],
    max_chars: int = 2000,
    min_chars: int = 200,
) -> List[Chunk]:
    """
    Erzeuge Text-Chunks aus einer Liste von Seiten-Strings.

    Strategie:
    - Seiten in Reihenfolge durchgehen.
    - So lange an einen Chunk anhängen, bis max_chars überschritten würde.
    - Falls eine einzelne Seite > max_chars ist, wird sie als eigener Chunk abgelegt
      (und ggf. > max_chars), aber wir erzeugen keinen weiteren Split.
    - min_chars dient nur dazu, sehr kleine Reste am Ende ggf. mit dem vorherigen
      Chunk zusammenzumergen (wenn möglich).

    Diese Heuristik ist bewusst einfach gehalten, aber robust und reproduzierbar.
    """
    chunks: List[Chunk] = []
    current_lines: List[str] = []
    current_len = 0
    current_start_page = 0
    current_page_start_idx = 0

    def finalize_chunk(end_page: int) -> None:
        """Innerer Helper zum Abschließen des aktuellen Chunks."""
        nonlocal current_lines, current_len, current_start_page, current_page_start_idx
        if not current_lines:
            return
        text = "\n\n".join(current_lines).strip()
        if not text:
            current_lines = []
            current_len = 0
            return
        chunks.append(Chunk(text=text, page_start=current_start_page, page_end=end_page))
        current_lines = []
        current_len = 0

    for page_idx, page_text in enumerate(page_texts):
        if not page_text:
            # Leere Seite einfach überspringen, aber Seitenzählung behalten
            continue

        page_len = len(page_text)
        # Falls Chunk leer ist, setzen wir den Start auf diese Seite
        if not current_lines:
            current_start_page = page_idx
            current_page_start_idx = page_idx

        # Wenn Seite alleine schon größer als max_chars ist, eigenen Chunk bauen
        if page_len > max_chars and not current_lines:
            chunks.append(Chunk(text=page_text, page_start=page_idx, page_end=page_idx))
            continue

        # Prüfen, ob diese Seite noch in den aktuellen Chunk passt
        if current_len + page_len + (2 if current_lines else 0) <= max_chars:
            current_lines.append(page_text)
            current_len += page_len + (2 if current_lines else 0)
        else:
            # Aktuellen Chunk abschließen
            finalize_chunk(page_idx - 1)
            # Neuer Chunk beginnt mit dieser Seite
            current_start_page = page_idx
            current_page_start_idx = page_idx
            current_lines = [page_text]
            current_len = page_len

    # Letzten Chunk abschließen
    if current_lines:
        finalize_chunk(len(page_texts) - 1)

    # Optional: letzte zwei Chunks zusammenführen, wenn der letzte sehr klein ist
    if len(chunks) >= 2 and len(chunks[-1].text) < min_chars:
        last = chunks.pop()
        prev = chunks.pop()
        merged_text = prev.text + "\n\n" + last.text
        chunks.append(
            Chunk(
                text=merged_text,
                page_start=prev.page_start,
                page_end=last.page_end,
            )
        )

    return chunks


def make_doc_id(input_root: Path, pdf_path: Path) -> str:
    """
    Erzeuge eine stabile doc_id aus dem relativen Pfad und einem Hash.

    Beispiel:
    - input_root = /beegfs/.../raw
    - pdf_path   = /beegfs/.../raw/GT/Workshop1/slides.pdf
    => rel       = GT/Workshop1/slides.pdf
    => doc_id    = pdf_GT__Workshop1__slides_<hash8>
    """
    rel = pdf_path.relative_to(input_root)
    rel_no_suffix = rel.with_suffix("")  # GT/Workshop1/slides
    rel_str = rel_no_suffix.as_posix()   # "GT/Workshop1/slides"
    slug = rel_str.replace("/", "__")

    h = hashlib.sha1(rel_str.encode("utf-8")).hexdigest()[:8]
    return f"pdf_{slug}_{h}"


def build_chunk_record(
    *,
    doc_id: str,
    chunk_index: int,
    rel_source_path: Path,
    total_pages: int,
    chunk: Chunk,
) -> Dict[str, Any]:
    """
    Baue den JSON-Record für einen Chunk entsprechend der geplanten Normalform.

    Beachte:
    - "semantic" bleibt hier leer; wird in späteren Pipeline-Schritten gefüllt.
    - "language" ist zunächst "unknown"; Language Detection folgt später.
    - "source_path" ist relativ zum Input-Root; absolute Pfade sollen im
      Normalisierungs-Layer vermieden werden.
    """
    chunk_id = f"{doc_id}_c{chunk_index:04d}"

    record: Dict[str, Any] = {
        "doc_id": doc_id,
        "chunk_id": chunk_id,
        "source_type": "pdf",
        "source_path": rel_source_path.as_posix(),
        "title": rel_source_path.stem,
        "language": "unknown",
        "content": chunk.text,
        "meta": {
            "page_start": chunk.page_start,
            "page_end": chunk.page_end,
            "num_pages": total_pages,
        },
        "semantic": {},  # wird von Schritt 2 der Pipeline ergänzt
    }
    return record


def write_jsonl(
    output_path: Path,
    records: Iterable[Dict[str, Any]],
    ensure_ascii: bool = False,
) -> None:
    """
    Schreibe eine Folge von JSON-Records als JSONL-Datei.

    - Jeder Record ist eine Zeile.
    - ensure_ascii=False lässt UTF-8 durch (wichtig für Umlaute, Formelnamen etc.).
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=ensure_ascii))
            f.write("\n")


# ---------------------------------------------------------------------------
# Hauptlogik pro PDF
# ---------------------------------------------------------------------------

def process_single_pdf(
    input_root: Path,
    output_root: Path,
    pdf_path: Path,
    max_chars: int,
    min_chars: int,
) -> None:
    """
    Verarbeite eine einzelne PDF-Datei:
    - Text extrahieren
    - in Chunks aufteilen
    - JSONL-Datei mit Chunk-Records schreiben
    """
    rel_source_path = pdf_path.relative_to(input_root)
    logging.info("Verarbeite PDF: %s", rel_source_path)

    page_texts = load_pdf_pages(pdf_path)
    total_pages = len(page_texts)

    if total_pages == 0:
        logging.warning("Keine Seiten in PDF gefunden (oder extrahierbar): %s", rel_source_path)
        return

    chunks = chunk_pages(page_texts, max_chars=max_chars, min_chars=min_chars)
    if not chunks:
        logging.warning("Keine Chunks erzeugt für %s (evtl. leerer Text).", rel_source_path)
        return

    doc_id = make_doc_id(input_root, pdf_path)

    records: List[Dict[str, Any]] = []
    for idx, chunk in enumerate(chunks):
        rec = build_chunk_record(
            doc_id=doc_id,
            chunk_index=idx,
            rel_source_path=rel_source_path,
            total_pages=total_pages,
            chunk=chunk,
        )
        records.append(rec)

    # Ausgabepfad: ein JSONL-File pro PDF
    # Beispiel: normalized/json/GT__Workshop1__slides_<hash8>.jsonl
    out_filename = f"{doc_id}.jsonl"
    output_path = output_root / out_filename
    write_jsonl(output_path, records)

    logging.info(
        "Fertig: %s → %s (Seiten: %d, Chunks: %d)",
        rel_source_path,
        output_path.relative_to(output_root.parent),
        total_pages,
        len(records),
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """CLI-Argumente definieren und parsen."""
    parser = argparse.ArgumentParser(
        description="PDF-Dateien in normalisierte JSONL-Chunks konvertieren."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        required=True,
        help="Wurzelverzeichnis der Rohdaten (PDFs).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Zielverzeichnis für normalisierte JSONL-Dateien.",
    )
    parser.add_argument(
        "--max-chars",
        type=int,
        default=2000,
        help="Max. Zeichen pro Chunk (Default: 2000).",
    )
    parser.add_argument(
        "--min-chars",
        type=int,
        default=200,
        help="Min. Zeichen für den letzten Chunk; "
             "falls kleiner, wird er mit dem vorherigen Chunk gemergt (Default: 200).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Ausführlichere Logging-Ausgabe aktivieren.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    setup_logging(verbose=args.verbose)

    input_root: Path = args.input_dir.resolve()
    output_root: Path = args.output_dir.resolve()

    if not input_root.is_dir():
        logging.error("Input-Verzeichnis existiert nicht: %s", input_root)
        return 1

    output_root.mkdir(parents=True, exist_ok=True)

    pdfs = find_pdfs(input_root)
    if not pdfs:
        logging.warning("Keine PDF-Dateien in %s gefunden.", input_root)
        return 0

    logging.info("Gefundene PDFs: %d", len(pdfs))

    for pdf_path in pdfs:
        try:
            process_single_pdf(
                input_root=input_root,
                output_root=output_root,
                pdf_path=pdf_path,
                max_chars=args.max_chars,
                min_chars=args.min_chars,
            )
        except Exception as exc:  # bewusst breit, um nicht den ganzen Lauf abzubrechen
            logging.exception("Fehler bei Verarbeitung von %s: %s", pdf_path, exc)

    logging.info("Ingestion abgeschlossen.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
