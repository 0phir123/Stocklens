# # File: adapters/embeddings/sbert_embedder.py
# from __future__ import annotations

# from typing import Sequence, List
# from sentence_transformers import SentenceTransformer


# class SBertEmbedder:
#     """
#     Adapter for sentence-transformers (SBERT).

#     Responsibilities:
#       - Load a pretrained model (default: all-MiniLM-L6-v2, dim=384)
#       - Encode a batch of texts into dense vectors
#       - Return results as plain lists of floats (JSON-friendly)
#     """

#     def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
#         # Load the SBERT model once when creating the adapter
#         self.model = SentenceTransformer(model_name)
#         self.dim = int(self.model.get_sentence_embedding_dimension())  # ← expose dimension

#     def encode(self, texts: Sequence[str]) -> List[list[float]]:
#         # Ensure we pass a real list (Sequence could be tuple)
#         texts_list = list(texts)

#         # Run model → outputs numpy.ndarray of shape [N, D]
#         embeddings = self.model.encode(
#             texts_list,
#             batch_size=32,
#             convert_to_numpy=True,      # numpy for efficiency
#             normalize_embeddings=True,  # L2 normalize (good for cosine similarity)
#         )

#         # Convert to JSON-friendly Python lists of floats
#         return [vec.tolist() for vec in embeddings]
