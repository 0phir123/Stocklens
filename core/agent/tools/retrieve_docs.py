# core/agent/tools/retrieve_docs.py
from __future__ import annotations
import os
from typing import List

from adapters.embeddings.sbert_embedder import SBertEmbedder
from adapters.rag.faiss_store import FaissStore

class RetrieveDocsTool:
    name = "retrieve_docs"
    description = "Semantic search over a persisted FAISS index; returns top-k snippets with citations."

    def __init__(self, index_name: str = "default", model_name: str = "sentence-transformers/all-MiniLM-L6-v2", top_k: int = 5) -> None:
        self.index_dir = os.path.join("var", "index", index_name)
        self.top_k = top_k
        self._emb = SBertEmbedder(model_name=model_name)
        self._store: FaissStore | None = None

    def _store_lazy(self) -> FaissStore:
        if self._store is None:
            self._store = FaissStore.load(self.index_dir)
        return self._store

    def execute(self, q: str) -> str:
        store = self._store_lazy()
        if store is None:
            return f"Index not found for '{self.index_dir}'. Run: python -m scripts.ingest_docs folder ./docs --name default"
        qvec = self._emb.encode([q])[0]
        hits = store.search(qvec, top_k=self.top_k)
        if not hits:
            return f"No matches for: {q}"

        # Build a concise, human-readable answer with citations + snippets
        lines: List[str] = [f"Top {len(hits)} results for: {q}"]
        for i, h in enumerate(hits, 1):
            meta = h.get("meta", {})
            path = meta.get("path") or meta.get("doc_id") or h["id"]
            snippet = (meta.get("text") or "")[:240].replace("\n", " ")
            lines.append(f"{i}. [{path}] (score={h['score']:.3f})")
            if snippet:
                lines.append(f"   └─ {snippet}")
        return "\n".join(lines)
