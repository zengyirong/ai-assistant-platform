"""Embedding client interface — platform-level model only."""

from __future__ import annotations

from abc import ABC, abstractmethod


class EmbeddingClient(ABC):
    @abstractmethod
    async def embed_documents(self, texts: list[str]) -> list[list[float]]: ...

    @abstractmethod
    async def embed_query(self, query: str) -> list[float]: ...
