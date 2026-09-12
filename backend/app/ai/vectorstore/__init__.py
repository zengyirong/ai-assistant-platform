"""Vector store factory."""

from __future__ import annotations

from app.ai.vectorstore.base import VectorStore
from app.ai.vectorstore.qdrant import QdrantVectorStore

_store: QdrantVectorStore | None = None


def get_vector_store() -> QdrantVectorStore:
    global _store
    if _store is None:
        _store = QdrantVectorStore()
    return _store


async def reset_vector_store() -> None:
    global _store
    if _store is not None:
        await _store.close()
        _store = None


__all__ = ["VectorStore", "QdrantVectorStore", "get_vector_store", "reset_vector_store"]
