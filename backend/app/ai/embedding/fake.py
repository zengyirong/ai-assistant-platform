"""Deterministic local embedding for offline / test pipelines."""

from __future__ import annotations

import hashlib
import math

from app.ai.embedding.base import EmbeddingClient
from app.core.config import settings


class FakeEmbeddingClient(EmbeddingClient):
    """Hash-based unit vectors; same text → same vector, no network."""

    def __init__(self, dimension: int | None = None) -> None:
        self.dimension = dimension or settings.EMBEDDING_DIMENSION

    def _embed_one(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        values: list[float] = []
        seed = digest
        while len(values) < self.dimension:
            for b in seed:
                # map byte to [-1, 1]
                values.append((b / 127.5) - 1.0)
                if len(values) >= self.dimension:
                    break
            seed = hashlib.sha256(seed).digest()
        # L2 normalize
        norm = math.sqrt(sum(v * v for v in values)) or 1.0
        return [v / norm for v in values]

    async def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(t) for t in texts]

    async def embed_query(self, query: str) -> list[float]:
        return self._embed_one(query)
