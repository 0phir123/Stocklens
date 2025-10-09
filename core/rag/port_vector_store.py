# # File: core/rag/port_vector_store.py
# from __future__ import annotations

# from typing import Protocol, List, Dict


# class VectorStore(Protocol):
#     """
#     Contract for any vector database / ANN index.

#     Responsibilities:
#       - Add embeddings with IDs + optional metadata
#       - Search by vector query, return top-k matches with scores
#     """

#     def add(self, ids: List[str], vectors: List[list[float]], metas: List[Dict[str, str]]) -> None:
#         """
#         Insert new vectors into the store.

#         Args:
#             ids: unique chunk IDs (len == N)
#             vectors: list of vectors (len == N, each = list[float] of dim D)
#             metas: list of metadata dicts (len == N)
#         """
#         ...

#     def search(self, query: list[float], top_k: int = 5) -> List[Dict]:
#         """
#         Find nearest neighbors for a query vector.

#         Args:
#             query: single embedding vector (dim D)
#             top_k: number of results to return

#         Returns:
#             List of dicts with at least:
#               {
#                 "id": <chunk_id>,
#                 "score": <similarity/distance>,
#                 "meta": {...}
#               }
#         """
#         ...
