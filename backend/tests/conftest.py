from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent


@pytest.fixture(autouse=True)
async def _dispose_db_engine() -> AsyncIterator[None]:
    """Avoid aiomysql pool reuse across closed asyncio loops in pytest."""
    yield
    from app.db.session import dispose_engine

    await dispose_engine()
