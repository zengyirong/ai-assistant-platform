"""LLM client factory."""

from __future__ import annotations

from app.ai.llm.base import LLMClient
from app.ai.llm.fake import FakeLLMClient
from app.ai.llm.openai_compatible import OpenAICompatibleLLMClient
from app.core.config import settings

_client: LLMClient | None = None


def get_llm_client() -> LLMClient:
    global _client
    if _client is not None:
        return _client

    provider = (settings.LLM_PROVIDER or "fake").strip().lower()
    if provider in {"fake", "local"}:
        _client = FakeLLMClient()
    elif provider in {"openai_compatible", "openai"}:
        _client = OpenAICompatibleLLMClient()
    else:
        _client = FakeLLMClient() if not settings.LLM_API_KEY else OpenAICompatibleLLMClient()
    return _client


def reset_llm_client() -> None:
    global _client
    _client = None


__all__ = ["LLMClient", "get_llm_client", "reset_llm_client"]
