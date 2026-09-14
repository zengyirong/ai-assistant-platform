from __future__ import annotations

import os
from collections.abc import AsyncIterator
from pathlib import Path

import pytest

# Force free/local providers for all tests regardless of developer .env.
# Must run before test modules import app.core.config.settings.
os.environ["LLM_PROVIDER"] = "fake"
os.environ["EMBEDDING_PROVIDER"] = "fake"

ROOT = Path(__file__).resolve().parent


@pytest.fixture(autouse=True)
async def _dispose_db_engine() -> AsyncIterator[None]:
    """Avoid aiomysql pool reuse across closed asyncio loops in pytest."""
    from app.core import config as config_mod

    config_mod.get_settings.cache_clear()
    config_mod.settings = config_mod.get_settings()
    config_mod.settings.LLM_PROVIDER = "fake"
    config_mod.settings.EMBEDDING_PROVIDER = "fake"

    yield
    from app.ai.embedding import reset_embedding_client
    from app.ai.llm import reset_llm_client
    from app.ai.vectorstore import reset_vector_store
    from app.db.session import dispose_engine

    reset_embedding_client()
    reset_llm_client()
    await reset_vector_store()
    await dispose_engine()
