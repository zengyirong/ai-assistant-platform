"""File storage interface — local path first, MinIO later."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import BinaryIO


class FileStorage(ABC):
    @abstractmethod
    async def save(self, file: BinaryIO, *, key: str) -> str: ...

    @abstractmethod
    async def delete(self, path: str) -> None: ...

    @abstractmethod
    async def open(self, path: str) -> BinaryIO: ...
