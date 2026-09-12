"""Local filesystem storage (Phase 1)."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import BinaryIO

from app.ai.storage.base import FileStorage
from app.core.config import settings


class LocalFileStorage(FileStorage):
    def __init__(self, root: str | None = None) -> None:
        self.root = Path(root or settings.FILE_STORAGE_PATH).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def _abs(self, key: str) -> Path:
        path = (self.root / key).resolve()
        if not str(path).startswith(str(self.root)):
            raise ValueError("invalid storage key")
        return path

    async def save(self, file: BinaryIO, *, key: str) -> str:
        path = self._abs(key)
        path.parent.mkdir(parents=True, exist_ok=True)

        def _write() -> None:
            data = file.read()
            path.write_bytes(data if isinstance(data, bytes) else bytes(data))

        await asyncio.to_thread(_write)
        return key

    async def save_bytes(self, data: bytes, *, key: str) -> str:
        path = self._abs(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        await asyncio.to_thread(path.write_bytes, data)
        return key

    async def delete(self, path: str) -> None:
        target = self._abs(path)
        if target.exists():
            await asyncio.to_thread(target.unlink)

    async def open(self, path: str) -> BinaryIO:
        target = self._abs(path)
        return await asyncio.to_thread(target.open, "rb")

    async def read_bytes(self, path: str) -> bytes:
        target = self._abs(path)
        return await asyncio.to_thread(target.read_bytes)


_storage: LocalFileStorage | None = None


def get_file_storage() -> LocalFileStorage:
    global _storage
    if _storage is None:
        _storage = LocalFileStorage()
    return _storage
