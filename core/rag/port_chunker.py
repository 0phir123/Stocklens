# File: core/rag/port_chunker.py
from __future__ import annotations
from typing import Protocol, List
from core.rag.rag_types import DocChunk


class Chunker(Protocol):
    """
    Contract for all chunking strategies.

    A chunker takes a raw document (doc_id + text) and splits it into
    smaller DocChunk objects for embedding & indexing.

    Example strategies:
      - FixedWindowChunker: fixed character/token size
      - ParagraphChunker: break on double newlines
      - SentenceChunker: use NLP sentence boundaries
    """

    def split(self, doc_id: str, text: str) -> List[DocChunk]:
        """Split a document into a list of immutable DocChunks."""
        ...
