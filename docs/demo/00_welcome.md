# StockLens Demo Corpus (RAG v0)
This mini corpus exists to exercise the retrieval tool. The loader reads `.txt` and `.md` recursively from a folder, the chunker splits by characters with overlap, the embedder is SBERT (all-MiniLM-L6-v2), and the vector store is FAISS (IndexFlatIP with L2-normalized vectors).
