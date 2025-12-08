#!/usr/bin/env python3
"""
embed_chunks.py

Erstellt Dense-Embeddings für alle semantisch annotierten Chunks in einem Workspace
und baut daraus einen FAISS-Vektorindex.

Unterstützt:
- .json (ein Dokument oder Liste von Chunks)
- .jsonl (JSON Lines: jede Zeile ein Dokument/Chunk)

Workspace-Struktur:
  <workspace_root>/
    semantic/json/       # Eingabe (semantisch annotierte Chunks)
    indices/faiss/       # Ausgabe (Index + Metadaten + Config)
    logs/                # Logfiles

Beispiel:
  python embed_chunks.py \
      --workspace-root /beegfs/scratch/workspace/es_phdoeble-rag_pipeline \
      --model-name sentence-transformers/all-mpnet-base-v2 \
      --batch-size 64 \
      --device cuda \
      --normalize
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

    fh = logging.FileHandler(logfile, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    ffmt = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    fh.setFormatter(ffmt)
    logger.addHandler(fh)

    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    cfmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%H:%M:%S")
    ch.setFormatter(cfmt)
    logger.addHandler(ch)

    logger.info("Logging initialisiert. Logfile: %s", logfile)
    return logger


def iter_normalized_files(normalized_root: str, logger: logging.Logger) -> Generator[str, None, None]:
    """
    Liefert Pfade zu allen .json- und .jsonl-Dateien unter normalized_root,
    außer Unterordnern namens 'archive'.
    """
    if not os.path.isdir(normalized_root):
        logger.error("Verzeichnis für semantische Dateien existiert nicht: %s", normalized_root)
        return

    for root, dirs, files in os.walk(normalized_root):
        dirs[:] = [d for d in dirs if d.lower() != "archive"]
        for fname in files:
            lower = fname.lower()
            if lower.endswith(".json") or lower.endswith(".jsonl"):
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
    - Ein Dokument mit Feld 'chunks': list[dict]
    """
    if isinstance(doc, dict):
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
    """
    title = chunk.get("title")
    content = chunk.get("content", "")

    if not isinstance(content, str):
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
    Lädt alle Chunks aus semantic/json (inkl. .jsonl) und sammelt:
    - Texte (für Embeddings)
    - Metadaten pro Chunk
    - Chunk-IDs

    max_chunks: wenn gesetzt, begrenzt die Anzahl der geladenen Chunks.
    """
    texts: List[str] = []
    metas: List[Dict[str, Any]] = []
    chunk_ids: List[str] = []

    num_files = 0
    num_chunks = 0

    file_paths = sorted(iter_normalized_files(normalized_root, logger))

    for fpath in file_paths:
        num_files += 1
        lower = fpath.lower()

        if lower.endswith(".json"):
            # ganze Datei als JSON laden
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    doc = json.load(f)
            except Exception as exc:
                logger.warning("Konnte JSON-Datei nicht laden (%s): %s", fpath, exc)
                continue

            for chunk, source_path in extract_chunks_from_doc(doc, fpath, logger):
                doc_id = chunk.get("doc_id")
                c_id = chunk.get("chunk_id")
                if not doc_id or not c_id:
                    logger.debug(
                        "Chunk ohne doc_id/chunk_id in %s – überspringe.",
                        source_path,
                    )
                    continue

                text = build_text_from_chunk(chunk)
                if not text.strip():
                    continue

                semantic = chunk.get("semantic", {}) or {}

                meta: Dict[str, Any] = {
                    "doc_id": doc_id,
                    "chunk_id": c_id,
                    "source_path": source_path,
                    "source_type": chunk.get("source_type"),
                    "language": chunk.get("language"),
                    "meta": chunk.get("meta", {}),
                    "semantic": semantic,
                    # flache Convenience-Felder für Filter:
                    "trust_level": semantic.get("trust_level"),
                    "content_type": semantic.get("content_type"),
                    "domain": semantic.get("domain"),
                }

                texts.append(text)
                metas.append(meta)
                chunk_ids.append(str(c_id))
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

        elif lower.endswith(".jsonl"):
            # JSON Lines: jede Zeile ein Dokument / Chunk
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    for line_no, line in enumerate(f, start=1):
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            doc = json.loads(line)
                        except Exception as exc:
                            logger.warning(
                                "Fehler beim Parsen von JSONL (%s:%d): %s",
                                fpath,
                                line_no,
                                exc,
                            )
                            continue

                        source_path = f"{fpath}:{line_no}"
                        for chunk, _ in extract_chunks_from_doc(doc, source_path, logger):
                            doc_id = chunk.get("doc_id")
                            c_id = chunk.get("chunk_id")
                            if not doc_id or not c_id:
                                logger.debug(
                                    "Chunk ohne doc_id/chunk_id in %s – überspringe.",
                                    source_path,
                                )
                                continue

                            text = build_text_from_chunk(chunk)
                            if not text.strip():
                                continue

                            semantic = chunk.get("semantic", {}) or {}

                            meta = {
                                "doc_id": doc_id,
                                "chunk_id": c_id,
                                "source_path": source_path,
                                "source_type": chunk.get("source_type"),
                                "language": chunk.get("language"),
                                "meta": chunk.get("meta", {}),
                                "semantic": semantic,
                                # flache Convenience-Felder für Filter:
                                "trust_level": semantic.get("trust_level"),
                                "content_type": semantic.get("content_type"),
                                "domain": semantic.get("domain"),
                            }

                            texts.append(text)
                            metas.append(meta)
                            chunk_ids.append(str(c_id))
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

            except Exception as exc:
                logger.warning("Konnte JSONL-Datei nicht lesen (%s): %s", fpath, exc)
                continue

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
    Erstellt einen FAISS-Index vom Typ IndexFlatIP oder IndexFlatL2.
    """
    if embeddings.ndim != 2:
        raise ValueError(f"Embeddings müssen 2D sein, erhalten: %s", embeddings.shape)

    num_vecs, dim = embeddings.shape
    logger.info("Erzeuge FAISS-Index mit %d Vektoren, Dimension %d", num_vecs, dim)

    if use_inner_product:
        index = faiss.IndexFlatIP(dim)
        logger.info("FAISS Index-Typ: IndexFlatIP (inner product / Cosine bei Normalisierung)")
    else:
        index = faiss.IndexFlatL2(dim)
        logger.info("FAISS Index-Typ: IndexFlatL2 (L2-Distanz)")

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
                "faiss_id": idx,
                **meta,
            }
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    logger.info("Metadaten nach %s geschrieben (%d Zeilen).", meta_path, len(metas))


def save_index_config(
    config_path: str,
    workspace_root: str,
    index_path: str,
    meta_path: str,
    args: argparse.Namespace,
    embeddings: np.ndarray,
    use_inner_product: bool,
    logger: logging.Logger,
) -> None:
    """
    Speichert eine JSON-Konfigurationsdatei für den Index mit Modell- und Indexparametern.
    """
    num_vecs, dim = embeddings.shape

    cfg: Dict[str, Any] = {
        "workspace_root": workspace_root,
        "index_path": os.path.abspath(index_path),
        "meta_path": os.path.abspath(meta_path),
        "model_name": args.model_name,
        "device": args.device,
        "embedding_dim": int(dim),
        "num_vectors": int(num_vecs),
        "metric": "IP" if use_inner_product else "L2",
        "normalized": bool(args.normalize),
        "index_type": "IndexFlatIP" if use_inner_product else "IndexFlatL2",
        "build_timestamp": datetime.now().isoformat(timespec="seconds"),
        "script": "embed_chunks.py",
    }

    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)

    logger.info("Index-Konfiguration nach %s geschrieben.", config_path)


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Erzeuge FAISS-Index aus semantisch annotierten Chunks (Embeddings)."
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
    parser.add_argument(
        "--config-name",
        default="contextual_config.json",
        help="Dateiname für die Index-Konfiguration unter indices/faiss/.",
    )
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv)

    workspace_root = os.path.abspath(args.workspace_root)
    normalized_root = os.path.join(workspace_root, "semantic", "json")
    indices_root = os.path.join(workspace_root, "indices", "faiss")
    index_path = os.path.join(indices_root, args.index_name)
    meta_path = os.path.join(indices_root, args.meta_name)
    config_path = os.path.join(indices_root, args.config_name)

    logger = setup_logging(workspace_root)
    logger.info("Workspace-Root: %s", workspace_root)
    logger.info("Semantic Root: %s", normalized_root)
    logger.info("Index wird geschrieben nach: %s", index_path)
    logger.info("Metadaten werden geschrieben nach: %s", meta_path)
    logger.info("Config wird geschrieben nach: %s", config_path)

    texts, metas, chunk_ids = collect_chunks(
        normalized_root=normalized_root,
        logger=logger,
        max_chunks=args.max_chunks,
    )

    if not texts:
        logger.error("Keine Chunks gefunden – Abbruch.")
        return 1

    # Check auf doppelte chunk_id
    unique_chunk_ids = len(set(chunk_ids))
    if unique_chunk_ids != len(chunk_ids):
        logger.warning(
            "Es gibt doppelte chunk_id-Werte: %d unique von %d Gesamt.",
            unique_chunk_ids,
            len(chunk_ids),
        )

    logger.info(
        "Starte Embedding-Berechnung mit Modell '%s' auf Gerät '%s'.",
        args.model_name,
        args.device,
    )
    try:
        model = SentenceTransformer(args.model_name, device=args.device)
    except Exception as exc:
        logger.error("Konnte SentenceTransformer-Modell nicht laden: %s", exc)
        return 1

    try:
        embeddings = model.encode(
            texts,
            batch_size=args.batch_size,
            convert_to_numpy=True,
            show_progress_bar=True,
            normalize_embeddings=args.normalize,
        )
    except TypeError:
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
            norms = np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-12
            embeddings = embeddings / norms

    logger.info("Embeddings erstellt: Shape = %s", embeddings.shape)

    use_ip = bool(args.normalize)
    index = build_faiss_index(embeddings, use_inner_product=use_ip, logger=logger)

    if index.ntotal != len(metas):
        logger.error(
            "Inkonsistenz: Index-Vektoren (%d) != Anzahl Metadatensätze (%d).",
            index.ntotal,
            len(metas),
        )
        return 1

    os.makedirs(indices_root, exist_ok=True)
    faiss.write_index(index, index_path)
    logger.info("FAISS-Index in %s gespeichert.", index_path)

    save_meta_lines(meta_path, metas, logger)
    save_index_config(
        config_path=config_path,
        workspace_root=workspace_root,
        index_path=index_path,
        meta_path=meta_path,
        args=args,
        embeddings=embeddings,
        use_inner_product=use_ip,
        logger=logger,
    )

    logger.info(
        "Fertig. Vektoren: %d, Index: %s, Meta: %s, Config: %s",
        len(metas),
        index_path,
        meta_path,
        config_path,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
