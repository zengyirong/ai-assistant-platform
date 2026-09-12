"""VectorStore interface — Qdrant adapter in Phase 1."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class VectorStore(ABC):
    @abstractmethod
    async def add_chunks(self, chunks: list[dict[str, Any]]) -> None: ...

    @abstractmethod
    async def delete_by_document(self, document_id: str) -> None: ...

    @abstractmethod
    async def search(
        self,
        query_vector: list[float],
        filters: dict[str, Any],
        top_k: int,
    ) -> list[dict[str, Any]]: ...
