"""LLM client interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any


class LLMClient(ABC):
    @abstractmethod
    async def invoke(self, messages: list[dict[str, Any]]) -> str: ...

    @abstractmethod
    async def stream(self, messages: list[dict[str, Any]]) -> AsyncIterator[str]: ...
