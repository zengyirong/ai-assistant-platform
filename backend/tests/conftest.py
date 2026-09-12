from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent


@pytest.fixture(autouse=True)
async def _dispose_db_engine() -> AsyncIterator[None]:
    """Avoid aiomysql pool reuse across closed asyncio loops in pytest."""
    yield
    from app.ai.embedding import reset_embedding_client
    from app.ai.llm import reset_llm_client
    from app.ai.vectorstore import reset_vector_store
    from app.db.session import dispose_engine

    reset_embedding_client()
    reset_llm_client()
    await reset_vector_store()
    await dispose_engine()
