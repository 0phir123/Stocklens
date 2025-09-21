# File: core/rag/chunker_fixed.py
from __future__ import annotations

from typing import List
from core.rag.port_chunker import Chunker
from core.rag.rag_types import DocChunk

class FixedWindowChunker:
    """
    Split text into fixed-size character windows with optional overlap.

    Example:
        chunker = FixedWindowChunker(window=1200, overlap=200)
        chunks = chunker.split("docs/guide", text)
    Notes:
        - Character-based (fast, deterministic); sentence/token strategies can come later.
        - Overlap helps preserve context across boundaries.
    """
    def __init__(self, window: int = 1200, overlap: int = 150) -> None:
        if window <= 0:
            raise ValueError("window must be positive")
        if overlap < 0 or overlap >= window:
            raise ValueError("overlap must be non-negative and less than window")
        self.window = window
        self.overlap = overlap   # fixed: consistent naming

    def split(self, doc_id: str, text: str) -> List[DocChunk]:
        chunks: List[DocChunk] = []
        n = len(text)
        if n == 0:
            return chunks

        start = 0
        idx = 0
        step = self.window - self.overlap

        while start < n:
            end = min(start + self.window, n)
            segment = text[start:end].strip()
            if segment:
                chunk_id = f"{doc_id}::w{idx}"
                meta = {
                    "strategy": "fixed_window",
                    "window": str(self.window),
                    "overlap": str(self.overlap),
                }
                chunks.append(
                    DocChunk(doc_id=doc_id, chunk_id=chunk_id, text=segment, meta=meta)
                )
                idx += 1
            start += step

        return chunks
