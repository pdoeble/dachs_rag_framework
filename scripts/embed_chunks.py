#!/usr/bin/env python3
"""
embed_chunks.py

Erstellt Dense-Embeddings für alle normalisierten Chunks in einem Workspace
und baut daraus einen FAISS-Vektorindex.

Annahmen:
- Workspace-Struktur wie im Masterplan beschrieben:
  <workspace_root>/
    normalized/json/     # Eingabe (Chunks)
    indices/faiss/       # Ausgabe (Index + Metadaten)
    logs/                # Logfiles

Verwendung (Beispiel):
  python embed_chunks.py \
      --workspace-root /beegfs/scratch/workspace/es_phdoeble-rag_pipeline \
      --model-name sentence-transformers/all-mpnet-base-v2 \
      --batch-size 64 \
      --device cuda

Hinweis:
- Dieses Skript baut den Index *neu* auf und überschreibt vorhandene Dateien.
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, Generator, List, Tuple

import numpy as np

try:
    import faiss  # type: ignore
except ImportError as e:
    print("Fehler: Das Python-Paket 'faiss' ist nicht installiert.", file=sys.stderr)
    print("Installiere z.B. mit: pip install faiss-cpu  oder  faiss-gpu", file=sys.stderr)
    raise e

try:
    from sentence_transformers import SentenceTransformer
except ImportError as e:
    print("Fehler: Das Python-Paket 'sentence-transformers' ist nicht installiert.", file=sys.stderr)
    print("Installiere z.B. mit: pip install sentence-transformers", file=sys.stderr)
    raise e


def setup_logging(workspace_root: str) -> logging.Logger:
    """
    Setzt Logging auf:
    - Konsole (INFO-Level)
    - Logfile unter <workspace_root>/logs/indices/embed_chunks_YYYYmmdd-HHMMSS.log
    """
    logs_root = os.path.join(workspace_root, "logs", "indices")
    os.makedirs(logs_root, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    logfile = os.path.join(logs_root, f"embed_chunks_{timestamp}.log")

    logger = logging.getLogger("embed_chunks")
    logger.setLevel(logging.DEBUG)
    logger.handlers.clear()

    # File-Handler (DEBUG)
    fh = logging.FileHandler(logfile, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    ffmt = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    fh.setFormatter(ffmt)
    logger.addHandler(fh)

    # Console-Handler (INFO)
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    cfmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%H:%M:%S")
    ch.setFormatter(cfmt)
    logger.addHandler(ch)

    logger.info("Logging initialisiert. Logfile: %s", logfile)
    return logger


def iter_normalized_json_files(normalized_root: str, logger: logging.Logger) -> Generator[str, None, None]:
    """
    Liefert Pfade zu allen .json-Dateien unter normalized_root,
    außer unterordnern namens 'archive'.
    """
    if not os.path.isdir(normalized_root):
        logger.error("Verzeichnis für normalisierte JSONs existiert nicht: %s", normalized_root)
        return

    for root, dirs, files in os.walk(normalized_root):
        # 'archive' Unterordner überspringen
        dirs[:] = [d for d in dirs if d.lower() != "archive"]

        for fname in files:
            if not fname.lower().endswith(".json"):
                continue
            yield os.path.join(root, fname)


def extract_chunks_from_doc(
    doc: Any,
    source_path: str,
    logger: logging.Logger,
) -> Generator[Tuple[Dict[str, Any], str], None, None]:
    """
    Extrahiert Chunks aus einem geladenen JSON-Dokument.

    Unterstützte Formen:
    - Ein einzelnes Chunk-Objekt (dict mit 'content' etc.)
    - Eine Liste von Chunk-Objekten (list[dict])

    Gibt Tupel (chunk_dict, source_path) zurück.
    """
    if isinstance(doc, dict):
        # Einzelner Chunk (oder Dokument mit 'chunks'-Liste)
        if "content" in doc:
            yield doc, source_path
        elif "chunks" in doc and isinstance(doc["chunks"], list):
            for chunk in doc["chunks"]:
                if isinstance(chunk, dict) and "content" in chunk:
                    yield chunk, source_path
                else:
                    logger.debug(
                        "Überspringe ungültigen Chunk-Eintrag in %s: %r",
                        source_path,
                        type(chunk),
                    )
        else:
            logger.debug(
                "JSON in %s hat kein 'content' oder 'chunks'-Feld. Typ=%s",
                source_path,
                type(doc),
            )
    elif isinstance(doc, list):
        # Liste von Chunks
        for chunk in doc:
            if isinstance(chunk, dict) and "content" in chunk:
                yield chunk, source_path
            else:
                logger.debug(
                    "Überspringe ungültigen Chunk in %s: %r",
                    source_path,
                    type(chunk),
                )
    else:
        logger.debug(
            "JSON-Wurzel in %s ist weder dict noch list (Typ=%s) – überspringe.",
            source_path,
            type(doc),
        )


def build_text_from_chunk(chunk: Dict[str, Any]) -> str:
    """
    Erzeugt den Text, der in den Embedding-Encoder geht.

    Einfache Heuristik:
    - Falls 'title' vorhanden: title + zwei Zeilenumbrüche + content
    - Sonst nur content
    """
    title = chunk.get("title")
    content = chunk.get("content", "")

    if not isinstance(content, str):
        # Sicherstellen, dass wir immer einen String haben
        content = str(content)

    if title and isinstance(title, str):
        return f"{title}\n\n{content}"
    return content


def collect_chunks(
    normalized_root: str,
    logger: logging.Logger,
    max_chunks: int | None = None,
) -> Tuple[List[str], List[Dict[str, Any]], List[str]]:
    """
    Lädt alle Chunks aus normalized/json und sammelt:
    - Texte (für Embeddings)
    - Metadaten pro Chunk (doc_id, chunk_id, source_path, etc.)
    - Chunk-IDs (separat für bequemeren Zugriff)

    max_chunks: wenn gesetzt, begrenzt die Anzahl der geladenen Chunks.
    """
    texts: List[str] = []
    metas: List[Dict[str, Any]] = []
    chunk_ids: List[str] = []

    num_files = 0
    num_chunks = 0

    for fpath in iter_normalized_json_files(normalized_root, logger):
        num_files += 1
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                doc = json.load(f)
        except Exception as exc:
            logger.warning("Konnte Datei nicht laden (%s): %s", fpath, exc)
            continue

        for chunk, source_path in extract_chunks_from_doc(doc, fpath, logger):
            # Sicherheitschecks
            doc_id = chunk.get("doc_id")
            c_id = chunk.get("chunk_id")

            if not doc_id or not c_id:
                # Ohne IDs ist der Chunk in der Pipeline praktisch nutzlos
                logger.debug(
                    "Chunk ohne doc_id/chunk_id in %s – überspringe.",
                    source_path,
                )
                continue

            text = build_text_from_chunk(chunk)
            if not text.strip():
                # Leere Chunks brauchen wir nicht
                continue

            meta: Dict[str, Any] = {
                "doc_id": doc_id,
                "chunk_id": c_id,
                "source_path": source_path,
                # Optionale Felder aus dem Chunk übernehmen, wenn vorhanden
                "source_type": chunk.get("source_type"),
                "language": chunk.get("language"),
                "meta": chunk.get("meta", {}),
                "semantic": chunk.get("semantic", {}),
            }

            texts.append(text)
            metas.append(meta)
            chunk_ids.append(c_id)
            num_chunks += 1

            if max_chunks is not None and num_chunks >= max_chunks:
                logger.info(
                    "Maximale Anzahl Chunks erreicht (%d) – Abbruch der Sammlung.",
                    max_chunks,
                )
                logger.info(
                    "Geladene Dateien: %d, gesammelte Chunks: %d",
                    num_files,
                    num_chunks,
                )
                return texts, metas, chunk_ids

    logger.info(
        "Sammlung abgeschlossen. Dateien: %d, Chunks: %d",
        num_files,
        num_chunks,
    )
    return texts, metas, chunk_ids


def build_faiss_index(
    embeddings: np.ndarray,
    use_inner_product: bool,
    logger: logging.Logger,
) -> faiss.Index:
    """
    Erstellt einen FAISS-Index vom Typ IndexFlatIP (Inner Product) oder IndexFlatL2.

    embeddings: numpy-Array der Form (N, D)
    use_inner_product: True => IndexFlatIP, False => IndexFlatL2
    """
    if embeddings.ndim != 2:
        raise ValueError(f"Embeddings müssen 2D sein, erhalten: {embeddings.shape}")

    num_vecs, dim = embeddings.shape
    logger.info("Erzeuge FAISS-Index mit %d Vektoren, Dimension %d", num_vecs, dim)

    if use_inner_product:
        index = faiss.IndexFlatIP(dim)
        logger.info("FAISS Index-Typ: IndexFlatIP (inner product)")
    else:
        index = faiss.IndexFlatL2(dim)
        logger.info("FAISS Index-Typ: IndexFlatL2 (L2-Distanz)")

    # Sicherheit: auf float32 casten
    vecs32 = embeddings.astype("float32")
    index.add(vecs32)

    logger.info("FAISS-Index aufgebaut (ntotal = %d)", index.ntotal)
    return index


def save_meta_lines(meta_path: str, metas: List[Dict[str, Any]], logger: logging.Logger) -> None:
    """
    Speichert die Metadaten zu jedem Vektor als JSON-Lines-Datei.

    Jede Zeile entspricht einem Vektor im Index (gleiche Reihenfolge!).
    """
    os.makedirs(os.path.dirname(meta_path), exist_ok=True)
    with open(meta_path, "w", encoding="utf-8") as f:
        for idx, meta in enumerate(metas):
            record = {
                "vector_id": idx,
                **meta,
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    logger.info("Metadaten nach %s geschrieben (%d Zeilen).", meta_path, len(metas))


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    """
    Parsed die Kommandozeilenargumente.
    """
    parser = argparse.ArgumentParser(
        description="Erzeuge FAISS-Index aus normalisierten Chunks (Embeddings)."
    )

    parser.add_argument(
        "--workspace-root",
        required=True,
        help="Pfad zum Workspace-Root (z.B. /beegfs/scratch/workspace/es_phdoeble-rag_pipeline).",
    )
    parser.add_argument(
        "--model-name",
        default="sentence-transformers/all-mpnet-base-v2",
        help="Name des Sentence-Transformer-Modells.",
    )
    parser.add_argument(
        "--device",
        default="cuda",
        help="Gerät für das Modell (z.B. 'cuda' oder 'cpu').",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=64,
        help="Batchgröße für Embedding-Berechnung.",
    )
    parser.add_argument(
        "--normalize",
        action="store_true",
        help="Embeddings L2-normalisieren und IndexFlatIP (Cosine-Suche) verwenden.",
    )
    parser.add_argument(
        "--max-chunks",
        type=int,
        default=None,
        help="Optional: Anzahl Chunks begrenzen (für Tests).",
    )
    parser.add_argument(
        "--index-name",
        default="contextual.index",
        help="Dateiname für den FAISS-Index unter indices/faiss/.",
    )
    parser.add_argument(
        "--meta-name",
        default="contextual_meta.jsonl",
        help="Dateiname für die Metadaten-JSONL unter indices/faiss/.",
    )

    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv)

    workspace_root = os.path.abspath(args.workspace_root)
    normalized_root = os.path.join(workspace_root, "normalized", "json")
    indices_root = os.path.join(workspace_root, "indices", "faiss")
    index_path = os.path.join(indices_root, args.index_name)
    meta_path = os.path.join(indices_root, args.meta_name)

    logger = setup_logging(workspace_root)
    logger.info("Workspace-Root: %s", workspace_root)
    logger.info("Normalized JSON Root: %s", normalized_root)
    logger.info("Index wird geschrieben nach: %s", index_path)
    logger.info("Metadaten werden geschrieben nach: %s", meta_path)

    # Chunks einsammeln
    texts, metas, chunk_ids = collect_chunks(
        normalized_root=normalized_root,
        logger=logger,
        max_chunks=args.max_chunks,
    )

    if not texts:
        logger.error("Keine Chunks gefunden – Abbruch.")
        return 1

    logger.info("Starte Embedding-Berechnung mit Modell '%s' auf Gerät '%s'.", args.model_name, args.device)
    try:
        model = SentenceTransformer(args.model_name, device=args.device)
    except Exception as exc:
        logger.error("Konnte SentenceTransformer-Modell nicht laden: %s", exc)
        return 1

    # Embeddings erzeugen
    try:
        embeddings = model.encode(
            texts,
            batch_size=args.batch_size,
            convert_to_numpy=True,
            show_progress_bar=True,
            normalize_embeddings=args.normalize,
        )
    except TypeError:
        # Fallback für ältere sentence-transformers-Versionen ohne normalize_embeddings-Argument
        logger.warning(
            "SentenceTransformer.encode unterstützt 'normalize_embeddings' nicht, "
            "normalisiere manuell."
        )
        embeddings = model.encode(
            texts,
            batch_size=args.batch_size,
            convert_to_numpy=True,
            show_progress_bar=True,
        )
        if args.normalize:
            # L2-Normalisierung
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-12
            embeddings = embeddings / norms

    logger.info("Embeddings erstellt: Shape = %s", embeddings.shape)

    # Index bauen
    use_ip = bool(args.normalize)
    index = build_faiss_index(embeddings, use_inner_product=use_ip, logger=logger)

    # Index speichern
    os.makedirs(indices_root, exist_ok=True)
    faiss.write_index(index, index_path)
    logger.info("FAISS-Index in %s gespeichert.", index_path)

    # Metadaten speichern
    save_meta_lines(meta_path, metas, logger)

    logger.info("Fertig. Vektoren: %d, Index: %s, Meta: %s", len(metas), index_path, meta_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
