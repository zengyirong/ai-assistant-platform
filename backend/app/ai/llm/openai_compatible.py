"""OpenAI-compatible chat completions streaming client."""

from __future__ import annotations

import json
from collections.abc import AsyncIterator
from typing import Any

import httpx

from app.ai.llm.base import LLMClient
from app.core.config import settings
from app.core.errors import AppError


class OpenAICompatibleLLMClient(LLMClient):
    def __init__(
        self,
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        model: str | None = None,
        timeout: float = 120.0,
    ) -> None:
        self.base_url = (base_url or settings.LLM_BASE_URL).rstrip("/")
        self.api_key = api_key if api_key is not None else settings.LLM_API_KEY
        self.model = model or settings.LLM_MODEL
        self.timeout = timeout
        if not self.api_key:
            raise AppError("INTERNAL_ERROR", "LLM_API_KEY 未配置", http_status=500)

    async def invoke(self, messages: list[dict[str, Any]]) -> str:
        parts: list[str] = []
        async for chunk in self.stream(messages):
            parts.append(chunk)
        return "".join(parts)

    async def stream(self, messages: list[dict[str, Any]]) -> AsyncIterator[str]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": True,
            "temperature": 0.2,
        }
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                async with client.stream(
                    "POST",
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload,
                ) as resp:
                    if resp.status_code >= 400:
                        body = (await resp.aread()).decode("utf-8", errors="ignore")
                        if resp.status_code == 429:
                            raise AppError(
                                "LLM_RATE_LIMIT",
                                "模型限流",
                                http_status=429,
                                details=body[:500],
                            )
                        raise AppError(
                            "INTERNAL_ERROR",
                            f"LLM API 失败: HTTP {resp.status_code}",
                            http_status=502,
                            details=body[:500],
                        )
                    async for line in resp.aiter_lines():
                        if not line:
                            continue
                        if line.startswith(":"):
                            continue
                        if not line.startswith("data:"):
                            continue
                        data = line[5:].strip()
                        if data == "[DONE]":
                            break
                        try:
                            obj = json.loads(data)
                        except json.JSONDecodeError:
                            continue
                        choices = obj.get("choices") or []
                        if not choices:
                            continue
                        delta = choices[0].get("delta") or {}
                        content = delta.get("content")
                        if content:
                            yield content
        except AppError:
            raise
        except httpx.TimeoutException as exc:
            raise AppError("LLM_TIMEOUT", "模型调用超时", http_status=504) from exc
        except Exception as exc:
            raise AppError(
                "INTERNAL_ERROR",
                f"LLM 调用失败: {exc}",
                http_status=502,
            ) from exc
