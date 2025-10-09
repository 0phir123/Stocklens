# RAG Pipeline (This Repo)
- **Loader**: `TextFolderLoader` reads `.txt`/`.md`, emits `LoadedDoc(doc_id, text, meta)`.
- **Chunker**: `FixedWindowChunker(window=1200, overlap=150)` → `DocChunk(chunk_id, text, meta)`.
- **Embedder**: `SBertEmbedder("sentence-transformers/all-MiniLM-L6-v2")` (dim=384, normalized).
- **Vector store**: `FaissStore(IndexFlatIP)`, cosine via inner product on unit vectors.
- **Persistence** under `var/index/<name>/`:
  - `index.faiss`, `id_map.json` (row→chunk_id), `meta_map.json` (chunk_id→meta incl. snippet), `config.json` (dim/metric).
- **Retrieve**: tool embeds the query, searches top-k, returns `[path] + snippet + score`.
