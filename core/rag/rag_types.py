# File: core/rag/rag_types.py
from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class DocChunk:
    """
    Immutable record representing a chunked piece of a document,
    ready for embedding and indexing.
    """

    doc_id: str
    chunk_id: str
    text: str
    meta: Dict[str, str]
