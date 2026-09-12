"""Embedding client factory."""

from __future__ import annotations

from app.ai.embedding.base import EmbeddingClient
from app.ai.embedding.fake import FakeEmbeddingClient
from app.ai.embedding.openai_compatible import OpenAICompatibleEmbeddingClient
from app.core.config import settings

_client: EmbeddingClient | None = None


def get_embedding_client() -> EmbeddingClient:
    global _client
    if _client is not None:
        return _client

    provider = (settings.EMBEDDING_PROVIDER or "fake").strip().lower()
    if provider in {"fake", "local", "hash"}:
        _client = FakeEmbeddingClient()
    elif provider in {"openai_compatible", "openai"}:
        _client = OpenAICompatibleEmbeddingClient()
    else:
        # Safe default for local/dev when misconfigured
        if not settings.EMBEDDING_API_KEY:
            _client = FakeEmbeddingClient()
        else:
            _client = OpenAICompatibleEmbeddingClient()
    return _client


def reset_embedding_client() -> None:
    global _client
    _client = None
