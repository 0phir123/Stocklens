# File: core/rag/port_embedder.py
from __future__ import annotations

from typing import Protocol, Sequence, List


class Embedder(Protocol):
    """
    Contract for any text-embedding backend.

    Implementations must:
      - accept a sequence of texts
      - return a list of equal-length float vectors (embeddings)
      - preserve order (i-th vector corresponds to i-th text)
    """

    def encode(self, texts: Sequence[str]) -> List[list[float]]:
        """
        Batch-encode texts into embeddings.

        Args:
            texts: sequence of UTF-8 strings to embed.

        Returns:
            A 2D list of shape [N, D], where:
              - N == len(texts)
              - D is the embedding dimension (model-dependent).
        """
        ...
