#!/usr/bin/env python
"""ingest_pdfs.py

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
import re
from collections import Counter
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
    block_types: List[str] | None = None  # z.B. ["paragraph", "formula", "table"]


@dataclass
class SentenceUnit:
    """Kleinstes semantisches Element im Chunking: ein Satz + Seitenindex + Blocktyp."""
    page_idx: int
    text: str
    block_type: str = "paragraph"  # "paragraph" | "heading" | "formula" | "table"


# Einfache, robuste Satzsegmentierung: Split nach . ! ? gefolgt von Whitespace.
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")


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


def remove_repeated_headers_footers(page_texts: List[str]) -> List[str]:
    """
    Erkenne wiederkehrende Kopf- und Fußzeilen über alle Seiten hinweg
    und entferne sie aus dem Seitentext.

    Heuristik:
    - Betrachtet jeweils die ersten und letzten bis zu 3 nicht-leeren Zeilen.
    - Zeilen, die auf >= 60% der Seiten vorkommen (mind. 2x) und nicht zu lang sind,
      werden als Header/Footer behandelt und entfernt.
    """
    n_pages = len(page_texts)
    if n_pages < 3:
        # Für sehr kleine Dokumente lohnt sich die Erkennung nicht.
        return page_texts

    header_counts: Counter[str] = Counter()
    footer_counts: Counter[str] = Counter()

    for page in page_texts:
        lines = [l.strip() for l in page.splitlines() if l.strip()]
        if not lines:
            continue
        top = lines[:3]
        bottom = lines[-3:]
        for l in top:
            header_counts[l] += 1
        for l in bottom:
            footer_counts[l] += 1

    threshold = max(2, int(0.6 * n_pages))
    header_candidates = {l for l, c in header_counts.items() if c >= threshold and len(l) <= 120}
    footer_candidates = {l for l, c in footer_counts.items() if c >= threshold and len(l) <= 120}

    cleaned: List[str] = []
    for page in page_texts:
        lines_orig = page.splitlines()
        filtered_lines: List[str] = []
        for l in lines_orig:
            ls = l.strip()
            if not ls:
                # Leere Zeilen beibehalten, damit Absätze nicht kollabieren
                filtered_lines.append(l)
                continue
            if ls in header_candidates or ls in footer_candidates:
                # Wiederkehrende Kopf-/Fußzeilen entfernen
                continue
            filtered_lines.append(l)
        cleaned.append("\n".join(filtered_lines).strip())
    return cleaned


def load_pdf_pages(pdf_path: Path) -> List[str]:
    """
    Extrahiere Text aus einem PDF als Liste von Strings, einer pro Seite.

    Hinweis:
    - benötigt das Paket "pypdf" (siehe env/requirements.txt).
    - leere Seiten werden als leere Strings ("") zurückgegeben.
    - wiederkehrende Kopf-/Fußzeilen werden heuristisch entfernt.
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

    # Wiederkehrende Kopf-/Fußzeilen entfernen
    page_texts = remove_repeated_headers_footers(page_texts)
    return page_texts


def _split_into_sentences(text: str) -> List[str]:
    """
    Zerlegt einen Text in Sätze.

    Aktuell: einfache Regex-Heuristik, die an '.', '!' oder '?' + Whitespace schneidet.
    Das vermeidet, dass mitten im Satz geschnitten wird, ohne von externen NLP-Paketen
    wie spaCy/NLTK abhängig zu sein.
    """
    text = text.strip()
    if not text:
        return []
    sentences = _SENTENCE_SPLIT_RE.split(text)
    # Nach dem Split kann der Trenn-Whitespace verloren gehen; die Interpunktion
    # bleibt wegen des Lookbehinds erhalten.
    return [s.strip() for s in sentences if s.strip()]


def looks_like_heading(line: str) -> bool:
    """
    Erkenne einfache Überschriften (Kapitel/Abschnittstitel).

    Heuristik:
    - kurz (< 80 Zeichen)
    - Nummerierung wie "1.2.3 Titel" oder
    - beginnt mit "Chapter/Section/Kapitel/Abschnitt" oder
    - überwiegend GROSSBUCHSTABEN.
    """
    s = line.strip()
    if not s:
        return False
    if len(s) < 80:
        if re.match(r"^\d+(\.\d+)*\s+\S+", s):
            return True
        if re.match(r"^(chapter|section|kapitel|abschnitt)\b", s, re.IGNORECASE):
            return True
        letters = [c for c in s if c.isalpha()]
        if letters and all(c.isupper() for c in letters) and len(letters) >= 3:
            return True
    return False


def looks_like_table(line: str) -> bool:
    """
    Erkenne einfache Tabellenzeilen.

    Heuristik:
    - Enthält '|' oder
    - Mindestens 3 "Spalten" mit >=2 Spaces dazwischen.
    """
    s = line.strip()
    if not s:
        return False
    if "|" in s:
        return True
    if re.search(r"\S+\s{2,}\S+\s{2,}\S+", s):
        return True
    return False


def looks_like_formula(line: str) -> bool:
    """
    Erkenne einfache Formeln / Gleichungen im Text.

    Heuristik:
    - Enthält typische mathematische Zeichen (inkl. '=') und mindestens einen Buchstaben
      ODER
    - enthält 'Eq.' / 'Equation'.
    """
    s = line.strip()
    if not s:
        return False
    math_chars = "=±+−∑∫√∞≡≤≥≈≠⋅∙°∆∂λμσπφθ^/"
    if any(ch in s for ch in math_chars) and any(c.isalpha() for c in s):
        return True
    if re.search(r"\b(eq\.?|equation)\b", s, re.IGNORECASE):
        return True
    return False


def classify_block_type(line: str) -> str:
    """
    Klassifiziere eine Zeile grob als heading / table / formula / paragraph.
    """
    if looks_like_heading(line):
        return "heading"
    if looks_like_table(line):
        return "table"
    if looks_like_formula(line):
        return "formula"
    return "paragraph"


def chunk_pages(
    page_texts: List[str],
    max_chars: int = 6000,
    min_chars: int = 400,
    sentence_overlap: int = 2,
) -> List[Chunk]:
    """
    Erzeuge inhalts-sensitive Text-Chunks aus einer Liste von Seiten-Strings.

    Strategie:
    - Alle Seiten werden in Zeilen, diese Zeilen in Sätze zerlegt (SentenceUnits mit Seitenindex + Blocktyp).
    - Chunks werden aus aufeinanderfolgenden Sätzen aufgebaut, bis max_chars erreicht ist.
    - Schnitte erfolgen nur an Satzgrenzen, damit jeder Chunk in sich kohärent bleibt.
    - sentence_overlap steuert die Anzahl der Sätze, die zwischen zwei aufeinanderfolgenden
      Chunks überlappen (z.B. 1–2 Sätze), um Informationsverlust am Chunk-Rand zu reduzieren.
    - Sehr lange Einzelsätze (> max_chars) werden als eigener Chunk abgelegt.
    - min_chars dient dazu, sehr kleine Rest-Chunks am Ende ggf. mit dem vorherigen Chunk
      zu mergen.
    - Überschriften (heading) erzwingen nach Möglichkeit eine Chunk-Grenze davor.

    Zusätzlich werden pro Chunk die vorkommenden Blocktypen (paragraph/heading/formula/table)
    gesammelt und als Metadaten bereitgestellt.
    """
    # 1) Seiten in Zeilen, dann in Sätze zerlegen und lineare Sequenz von SentenceUnits aufbauen.
    units: List[SentenceUnit] = []
    for page_idx, page_text in enumerate(page_texts):
        if not page_text:
            continue
        for line in page_text.splitlines():
            block_type = classify_block_type(line)
            sentences = _split_into_sentences(line)
            for s in sentences:
                units.append(SentenceUnit(page_idx=page_idx, text=s, block_type=block_type))

    if not units:
        return []

    chunks: List[Chunk] = []

    def _current_len(sentences: List[SentenceUnit]) -> int:
        """Approx. Zeichenanzahl eines Chunks (inkl. einfacher Leerzeichen zwischen Sätzen)."""
        if not sentences:
            return 0
        total = sum(len(s.text) for s in sentences)
        total += max(0, len(sentences) - 1)
        return total

    def _finish_chunk(sentences: List[SentenceUnit]) -> None:
        """Hilfsfunktion: aus SentenceUnits einen Chunk bauen und anhängen."""
        if not sentences:
            return
        text = " ".join(s.text.strip() for s in sentences if s.text.strip()).strip()
        if not text:
            return
        page_start = min(s.page_idx for s in sentences)
        page_end = max(s.page_idx for s in sentences)
        block_types = sorted({s.block_type for s in sentences if s.block_type})
        chunks.append(
            Chunk(
                text=text,
                page_start=page_start,
                page_end=page_end,
                block_types=block_types,
            )
        )

    current: List[SentenceUnit] = []

    for unit in units:
        sent_text = unit.text.strip()
        if not sent_text:
            continue
        sent_len = len(sent_text)

        # Harte Grenze an Überschriften: bestehender Chunk wird abgeschlossen,
        # Überschrift eröffnet neuen Chunk.
        if unit.block_type == "heading" and current:
            _finish_chunk(current)
            current = [unit]
            continue

        # Fall: Ein einzelner Satz ist länger als max_chars → eigener Chunk.
        if sent_len >= max_chars:
            if current:
                _finish_chunk(current)
                current = []
            chunks.append(
                Chunk(
                    text=sent_text,
                    page_start=unit.page_idx,
                    page_end=unit.page_idx,
                    block_types=[unit.block_type],
                )
            )
            continue

        if not current:
            # Neuer Chunk startet mit diesem Satz
            current = [unit]
            continue

        # Prüfen, ob der Satz noch in den aktuellen Chunk passt
        tentative = current + [unit]
        if _current_len(tentative) <= max_chars:
            current = tentative
            continue

        # Aktueller Chunk wäre mit diesem Satz zu groß:
        # → Chunk abschließen, mit Overlap neuen Chunk starten.
        tail: List[SentenceUnit] = []
        if sentence_overlap > 0:
            tail = current[-sentence_overlap:]
        _finish_chunk(current)

        # Overlap als Start für den neuen Chunk verwenden
        current = list(tail) if tail else []
        if _current_len(current) > max_chars:
            # Falls der Overlap alleine schon zu groß ist, verwerfen
            current = []

        # Jetzt den neuen Satz anhängen (ggf. als alleinigen Chunk)
        if not current:
            current = [unit]
        else:
            tentative = current + [unit]
            if _current_len(tentative) <= max_chars:
                current = tentative
            else:
                # Overlap + Satz wäre zu groß → Overlap wurde bereits als Chunk geschrieben,
                # daher Satz alleine als neuer Chunk starten.
                _finish_chunk(current)
                current = [unit]

    # Letzten Chunk abschließen
    if current:
        _finish_chunk(current)

    # Optional: letzte zwei Chunks zusammenführen, wenn der letzte sehr klein ist
    if len(chunks) >= 2 and len(chunks[-1].text) < min_chars:
        last = chunks.pop()
        prev = chunks.pop()
        merged_text = (prev.text + " " + last.text).strip()
        merged_block_types = sorted(set((prev.block_types or []) + (last.block_types or [])))
        chunks.append(
            Chunk(
                text=merged_text,
                page_start=prev.page_start,
                page_end=last.page_end,
                block_types=merged_block_types,
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
    - block_types/has_table/has_formula/has_heading helfen späteren
      Q&A-Generatoren und Retrieval-Heuristiken.
    """
    chunk_id = f"{doc_id}_c{chunk_index:04d}"

    block_types = chunk.block_types or []
    meta: Dict[str, Any] = {
        "page_start": chunk.page_start,
        "page_end": chunk.page_end,
        "num_pages": total_pages,
        "block_types": block_types,
        "has_table": "table" in block_types,
        "has_formula": "formula" in block_types,
        "has_heading": "heading" in block_types,
    }

    record: Dict[str, Any] = {
        "doc_id": doc_id,
        "chunk_id": chunk_id,
        "source_type": "pdf",
        "source_path": rel_source_path.as_posix(),
        "title": rel_source_path.stem,
        "language": "unknown",
        "content": chunk.text,
        "meta": meta,
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
    sentence_overlap: int,
) -> None:
    """
    Verarbeite eine einzelne PDF-Datei:
    - Text extrahieren (inkl. Header/Footer-Bereinigung)
    - in inhalts-sensitive Chunks aufteilen
    - JSONL-Datei mit Chunk-Records schreiben
    """
    rel_source_path = pdf_path.relative_to(input_root)
    logging.info("Verarbeite PDF: %s", rel_source_path)

    page_texts = load_pdf_pages(pdf_path)
    total_pages = len(page_texts)

    if total_pages == 0:
        logging.warning("Keine Seiten in PDF gefunden (oder extrahierbar): %s", rel_source_path)
        return

    chunks = chunk_pages(
        page_texts,
        max_chars=max_chars,
        min_chars=min_chars,
        sentence_overlap=sentence_overlap,
    )
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
        default=6000,
        help="Max. Zeichen pro Chunk (Default: 6000).",
    )
    parser.add_argument(
        "--min-chars",
        type=int,
        default=400,
        help="Min. Zeichen für den letzten Chunk; "
             "falls kleiner, wird er mit dem vorherigen Chunk gemergt (Default: 400).",
    )
    parser.add_argument(
        "--sentence-overlap",
        type=int,
        default=2,
        help="Anzahl überlappender Sätze zwischen zwei Chunks (Default: 2).",
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
                sentence_overlap=args.sentence_overlap,
            )
        except Exception as exc:  # bewusst breit, um nicht den ganzen Lauf abzubrechen
            logging.exception("Fehler bei Verarbeitung von %s: %s", pdf_path, exc)

    logging.info("Ingestion abgeschlossen.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
