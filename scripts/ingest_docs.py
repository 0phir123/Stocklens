# scripts/ingest_docs.py
from __future__ import annotations
import os, json
from typing import List, Dict
import typer

from adapters.embeddings.sbert_embedder import SBertEmbedder
from adapters.rag.faiss_store import FaissStore
from adapters.rag.loader import TextFolderLoader
from core.rag.chunker_fixed import FixedWindowChunker

app = typer.Typer(add_completion=False)

@app.command()
def folder(
    src: str = typer.Argument(..., help="Root folder containing .txt/.md files"),
    name: str = typer.Option("default", "--name", "-n", help="Index name under var/index/<name>"),
    window: int = typer.Option(1200, "--window", "-w", help="Chunk window (chars)"),
    overlap: int = typer.Option(150, "--overlap", "-o", help="Chunk overlap (chars)"),
    model: str = typer.Option("sentence-transformers/all-MiniLM-L6-v2", "--model", "-m"),
):
    """
    Load text files → chunk → SBERT embed → add to FAISS → save under var/index/<name>/
    """
    loader = TextFolderLoader(src)
    chunker = FixedWindowChunker(window=window, overlap=overlap)
    embedder = SBertEmbedder(model_name=model)

    ids: List[str] = []
    texts: List[str] = []
    metas: List[Dict[str, str]] = []

    for doc in loader.iter_docs():
        for ch in chunker.split(doc.doc_id, doc.text):
            ids.append(ch.chunk_id)
            texts.append(ch.text)
            metas.append({
                **doc.meta,           # path, ext, loader
                **ch.meta,            # strategy, window, overlap
                "doc_id": ch.doc_id,
                "chunk_id": ch.chunk_id,
                "text": ch.text,      # stash snippet for retrieval
            })

    vectors = embedder.encode(texts)
    store = FaissStore(dim=embedder.dim)
    store.add(ids, vectors, metas)

    out_dir = os.path.join("var", "index", name)
    store.save(out_dir)

    typer.echo(json.dumps({
        "indexed_docs": len({m["doc_id"] for m in metas}),
        "indexed_chunks": len(ids),
        "index_dir": out_dir
    }, indent=2))

if __name__ == "__main__":
    app()
