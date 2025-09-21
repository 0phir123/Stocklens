# adapters/rag/faiss_store.py
from __future__ import annotations

import json
import os
from typing import List, Dict, TypedDict
import faiss
import numpy as np


class FaissStore(TypedDict):
    """
    Flat Inner-Product FAISS index (cosine when vectors are L2-normalized).

    Persists alongside the index:
      - id_map.json   : List[str]         (row_index -> chunk_id)
      - meta_map.json : Dict[str, Dict]   (chunk_id -> metadata incl. text snippet)
      - config.json   : {"dim": int, "metric": "ip"}
    """

    def __init__(self, dim: int) -> None:
        self.dim = dim
        self.index = faiss.IndexFlatIP(dim)
        self.id_map: List[str] = []
        self.meta_map: Dict[str, Dict[str, str]] = {}

    # -------- core API (matches VectorStore protocol) --------
    def add(self, ids: List[str], vectors: List[list[float]], metas: List[Dict[str, str]]) -> None:
        if not (len(ids) == len(vectors) == len(metas)):
            raise ValueError("Length of ids, vectors, and metas must be the same.")
        if not ids:
            return

        arr = np.asarray(vectors, dtype="float32")
        if arr.ndim != 2 or arr.shape[1] != self.dim:
            raise ValueError(f"Vector dimension mismatch. Expected {self.dim}, got {arr.shape[1]}")
        # Defensive normalize: embedder already normalizes, but keep it safe.
        norms = np.linalg.norm(arr, axis=1, keepdims=True)
        norms[norms == 0.0] = 1.0
        arr = arr / norms

        self.index.add(arr)
        self.id_map.extend(ids)
        for i, chunk_id in enumerate(ids):
            self.meta_map[chunk_id] = metas[i]

    def search(self, query: list[float], top_k: int = 5) -> List[Dict]:
        if self.index.ntotal == 0:
            return []
        q = np.asarray([query], dtype="float32")
        # Defensive normalize (cosine via IP)
        n = np.linalg.norm(q, axis=1, keepdims=True)
        n[n == 0.0] = 1.0
        q = q / n

        scores, indices = self.index.search(q, min(top_k, max(1, self.index.ntotal)))
        out: List[Dict] = []
        for rank, idx in enumerate(indices[0]):
            if idx == -1:
                continue
            chunk_id = self.id_map[idx]
            out.append(
                {
                    "id": chunk_id,                          # ← matches VectorStore port
                    "score": float(scores[0][rank]),
                    "meta": self.meta_map.get(chunk_id, {}), # ← matches VectorStore port
                }
            )
        return out

    # -------- persistence --------
    def save(self, dir_path: str) -> None:
        os.makedirs(dir_path, exist_ok=True)
        faiss.write_index(self.index, os.path.join(dir_path, "index.faiss"))
        with open(os.path.join(dir_path, "id_map.json"), "w", encoding="utf-8") as f:
            json.dump(self.id_map, f, ensure_ascii=False, indent=2)
        with open(os.path.join(dir_path, "meta_map.json"), "w", encoding="utf-8") as f:
            json.dump(self.meta_map, f, ensure_ascii=False, indent=2)
        with open(os.path.join(dir_path, "config.json"), "w", encoding="utf-8") as f:
            json.dump({"dim": self.dim, "metric": "ip"}, f)

    @classmethod
    def load(cls, dir_path: str) -> "FaissStore":
        index = faiss.read_index(os.path.join(dir_path, "index.faiss"))
        with open(os.path.join(dir_path, "config.json"), "r", encoding="utf-8") as f:
            cfg = json.load(f)
        self = cls(dim=int(cfg["dim"]))
        self.index = index
        with open(os.path.join(dir_path, "id_map.json"), "r", encoding="utf-8") as f:
            self.id_map = list(json.load(f))
        with open(os.path.join(dir_path, "meta_map.json"), "r", encoding="utf-8") as f:
            self.meta_map = dict(json.load(f))
        return self
