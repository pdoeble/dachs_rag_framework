#!/usr/bin/env python3
"""
faiss_retriever.py

Hilfsmodul zum Laden des FAISS-Index aus dem Workspace und
Retrieval von Nachbar-Chunks auf Basis von chunk_id.

Wird später aus annotate_semantics.py / generate_qa_candidates.py verwendet,
um ähnliche Chunks für Kontext hinzuzuziehen.

Beispiel (CLI-Test):

  python scripts/faiss_retriever.py \
      --workspace-root /beegfs/scratch/workspace/es_phdoeble-rag_pipeline \
      --chunk-id SOME_CHUNK_ID \
      --top-k 5
"""

import argparse
import json
import os
import sys
from typing import Any, Dict, List, Tuple

import numpy as np

try:
    import faiss  # type: ignore
except ImportError as e:
    print("Fehler: 'faiss' ist nicht installiert. (pip install faiss-cpu oder faiss-gpu)", file=sys.stderr)
    raise e


class FaissRetriever:
    """
    Kapselt:
    - Laden des FAISS-Index
    - Laden der JSONL-Metadaten
    - Mapping chunk_id -> vector_id
    - Nachbarschaftssuche pro Chunk
    """

    def __init__(
        self,
        workspace_root: str,
        index_name: str = "contextual.index",
        meta_name: str = "contextual_meta.jsonl",
    ) -> None:
        self.workspace_root = os.path.abspath(workspace_root)
        self.indices_root = os.path.join(self.workspace_root, "indices", "faiss")
        self.index_path = os.path.join(self.indices_root, index_name)
        self.meta_path = os.path.join(self.indices_root, meta_name)

        if not os.path.isfile(self.index_path):
            raise FileNotFoundError(f"FAISS-Index nicht gefunden: {self.index_path}")
        if not os.path.isfile(self.meta_path):
            raise FileNotFoundError(f"Metadaten-Datei nicht gefunden: {self.meta_path}")

        # Index laden
        self.index = faiss.read_index(self.index_path)

        # Metadaten laden
        self.meta: List[Dict[str, Any]] = []
        self.chunkid_to_vectorid: Dict[str, int] = {}

        with open(self.meta_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                vec_id = rec.get("vector_id")
                chunk_id = rec.get("chunk_id")
                if vec_id is None or chunk_id is None:
                    continue
                self.meta.append(rec)
                self.chunkid_to_vectorid[str(chunk_id)] = int(vec_id)

        if len(self.meta) != self.index.ntotal:
            raise RuntimeError(
                f"Anzahl Metadaten ({len(self.meta)}) ungleich Index-Vektoren ({self.index.ntotal})."
            )

    def get_vector_id_for_chunk(self, chunk_id: str) -> int:
        """
        Gibt die vector_id (Indexposition) für eine gegebene chunk_id zurück.
        """
        try:
            return self.chunkid_to_vectorid[chunk_id]
        except KeyError as exc:
            raise KeyError(f"chunk_id nicht im Index gefunden: {chunk_id}") from exc

    def reconstruct_vector(self, vector_id: int) -> np.ndarray:
        """
        Rekonstruiert den Vektor zu einer gegebenen vector_id aus dem Index.

        Funktioniert für FLAT-Indizes (IndexFlatIP / IndexFlatL2), wie in embed_chunks.py verwendet.
        """
        if vector_id < 0 or vector_id >= self.index.ntotal:
            raise IndexError(f"Ungültige vector_id: {vector_id}")

        vec = self.index.reconstruct(vector_id)
        return np.asarray(vec, dtype="float32").reshape(1, -1)

    def get_neighbors_for_chunk(
        self,
        chunk_id: str,
        top_k: int = 5,
        include_self: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Liefert die Top-k Nachbar-Chunks für eine gegebene chunk_id.

        Rückgabe: Liste von Dicts mit:
          - 'score'  (Ähnlichkeit oder Distanz, je nach Index)
          - 'vector_id'
          - alle Metadaten aus contextual_meta.jsonl

        Wenn include_self=False, wird der Chunk selbst aus den Ergebnissen entfernt.
        """
        vector_id = self.get_vector_id_for_chunk(chunk_id)
        query_vec = self.reconstruct_vector(vector_id)

        # Wir holen bewusst etwas mehr und filtern ggf. uns selbst raus
        k_search = top_k + (0 if include_self else 1)
        distances, indices = self.index.search(query_vec, k_search)

        result: List[Dict[str, Any]] = []

        for dist, idx in zip(distances[0], indices[0]):
            if idx < 0:
                continue
            if not include_self and idx == vector_id:
                continue

            if idx >= len(self.meta):
                # Sollte nicht passieren, aber wir sind lieber defensiv
                continue

            rec = dict(self.meta[idx])  # Kopie
            rec["score"] = float(dist)
            rec["vector_id"] = int(idx)
            result.append(rec)

            if len(result) >= top_k:
                break

        return result


def _cli_print_neighbors(
    workspace_root: str,
    chunk_id: str,
    top_k: int,
) -> None:
    """
    Hilfsfunktion für den CLI-Modus: lädt den Retriever und druckt Nachbarn.
    """
    retriever = FaissRetriever(workspace_root=workspace_root)

    neighbors = retriever.get_neighbors_for_chunk(
        chunk_id=chunk_id,
        top_k=top_k,
        include_self=False,
    )

    print(f"Top-{top_k} Nachbarn für chunk_id={chunk_id}:")
    for i, rec in enumerate(neighbors, start=1):
        doc_id = rec.get("doc_id")
        nid = rec.get("chunk_id")
        score = rec.get("score")
        source_path = rec.get("source_path")
        print(f"{i:2d}. score={score:.4f}  doc_id={doc_id}  chunk_id={nid}")
        print(f"    source_path={source_path}")


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="FAISS-Retriever für Nachbar-Chunks (auf Basis von chunk_id)."
    )
    parser.add_argument(
        "--workspace-root",
        required=True,
        help="Pfad zum Workspace-Root (z.B. /beegfs/scratch/workspace/es_phdoeble-rag_pipeline).",
    )
    parser.add_argument(
        "--chunk-id",
        help="chunk_id, für die Nachbarn gesucht werden sollen (CLI-Test).",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Anzahl der zurückzugebenden Nachbarn.",
    )
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> int:
    args = parse_args(argv)

    if args.chunk_id:
        _cli_print_neighbors(
            workspace_root=args.workspace_root,
            chunk_id=args.chunk_id,
            top_k=args.top_k,
        )
    else:
        print(
            "Hinweis: Für einen schnellen Test bitte --chunk-id <ID> angeben.",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
