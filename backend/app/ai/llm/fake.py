"""Fake LLM for offline RAG demos/tests."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any

from app.ai.llm.base import LLMClient


class FakeLLMClient(LLMClient):
    async def invoke(self, messages: list[dict[str, Any]]) -> str:
        parts: list[str] = []
        async for chunk in self.stream(messages):
            parts.append(chunk)
        return "".join(parts)

    async def stream(self, messages: list[dict[str, Any]]) -> AsyncIterator[str]:
        user = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user = str(msg.get("content") or "")
                break

        # Extract a short excerpt from knowledge block if present
        excerpt = ""
        if "【知识库摘录】" in user:
            body = user.split("【知识库摘录】", 1)[1]
            body = body.split("【用户问题】", 1)[0].strip()
            excerpt = body[:180].replace("\n", " ").strip()

        question = ""
        if "【用户问题】" in user:
            question = user.split("【用户问题】", 1)[1].strip()
            question = question.split("\n", 1)[0].strip()

        if excerpt:
            answer = (
                f"根据知识库内容，关于「{question or '该问题'}」的要点如下："
                f"{excerpt}"
            )
        else:
            answer = "未提供可用摘录，无法回答。"

        # Stream in small pieces
        step = 12
        for i in range(0, len(answer), step):
            yield answer[i : i + step]
