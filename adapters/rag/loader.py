# File: adapters/rag/loader.py
from __future__ import annotations  # postpone type evaluation; avoids forward-ref issues

from dataclasses import dataclass           # small, typed record for loaded docs
from pathlib import Path                    # robust filesystem paths (cross-platform)
from typing import Iterator, Tuple, Dict    # precise iterator + tuple typing

@dataclass(frozen=True)
class LoadedDoc:
    """
    Immutable record representing a raw document prior to chunking/embedding.
    """
    doc_id: str              # stable identifier (e.g., "guides/setup" or "notes/intro")
    text: str                # full document text
    meta: Dict[str, str]     # loader metadata (e.g., {"path": "...", "ext": ".txt"})

class TextFolderLoader:
    """
    Load .txt/.md files from a folder tree as raw documents.

    Usage:
        loader = TextFolderLoader("data/corpus")
        for doc in loader.iter_docs():
            ...
    """
    def __init__(self, root: str | Path, exts: Tuple[str, ...] = (".txt", ".md")) -> None:
        self.root = Path(root)
        self.exts = tuple(exts)

    def iter_docs(self) -> Iterator[LoadedDoc]:
        """
        Depth-first traversal yielding LoadedDoc for each matching file.
        - doc_id: POSIX-style relative path without extension (stable across OS)
        - text: file contents read as UTF-8 (errors replaced)
        - meta: {"path": "<relative path with ext>", "ext": ".txt" | ".md", "loader": "text"}
        """
        root = self.root.resolve()
        for ext in self.exts:
            for fp in root.rglob(f"*{ext}"):
                if not fp.is_file():
                    continue
                rel = fp.relative_to(root)
                doc_id = rel.with_suffix("").as_posix()  # stable ID for citations
                try:
                    text = fp.read_text(encoding="utf-8", errors="replace")
                except Exception:
                    # Skip unreadable files but keep ingestion resilient
                    continue
                yield LoadedDoc(
                    doc_id=doc_id,
                    text=text,
                    meta={"path": rel.as_posix(), "ext": fp.suffix, "loader": "text"},
                )
