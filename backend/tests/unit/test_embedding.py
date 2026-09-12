"""Unit tests for fake embedding + chunking helpers."""

from __future__ import annotations

import pytest

from app.ai.embedding.fake import FakeEmbeddingClient
from app.core.config import settings
from app.modules.job.pipeline import simple_chunk_text


@pytest.mark.asyncio
async def test_fake_embedding_deterministic_and_normalized() -> None:
    client = FakeEmbeddingClient(dimension=32)
    a = await client.embed_query("hello")
    b = await client.embed_query("hello")
    c = await client.embed_query("world")
    assert a == b
    assert a != c
    assert len(a) == 32
    norm = sum(x * x for x in a) ** 0.5
    assert abs(norm - 1.0) < 1e-6


def test_simple_chunk_text_overlap() -> None:
    text = "abcdefghijklmnopqrstuvwxyz"
    chunks = simple_chunk_text(text, chunk_size=10, chunk_overlap=3)
    assert chunks
    assert chunks[0].startswith("abcdefghij")
    assert len(chunks) >= 3


def test_default_embedding_dimension_matches_settings() -> None:
    client = FakeEmbeddingClient()
    assert client.dimension == settings.EMBEDDING_DIMENSION
