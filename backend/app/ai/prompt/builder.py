"""Prompt builder for Phase 1 RAG."""

from __future__ import annotations

from typing import Any

from app.ai.retrieval.service import RetrievedChunk
from app.core.config import settings

DEFAULT_SYSTEM = (
    "你是企业知识库助手。只能依据提供的【知识库摘录】回答用户问题；"
    "不得编造摘录中不存在的事实。若摘录不足以回答，请明确说明未找到可靠依据。"
)


def build_rag_messages(
    *,
    question: str,
    chunks: list[RetrievedChunk],
    system_prompt: str | None = None,
    history: list[dict[str, str]] | None = None,
) -> list[dict[str, Any]]:
    system = (system_prompt or DEFAULT_SYSTEM).strip()
    context_blocks: list[str] = []
    for i, chunk in enumerate(chunks, start=1):
        meta = f"[{i}] doc={chunk.document_name or chunk.document_id}"
        if chunk.page is not None:
            meta += f" page={chunk.page}"
        if chunk.section:
            meta += f" section={chunk.section}"
        context_blocks.append(f"{meta}\n{chunk.content}")

    context = "\n\n".join(context_blocks) if context_blocks else "（无摘录）"
    user_content = (
        f"【知识库摘录】\n{context}\n\n"
        f"【用户问题】\n{question}\n\n"
        "请基于摘录作答；必要时可简要引用摘录编号。"
    )

    messages: list[dict[str, Any]] = [{"role": "system", "content": system}]
    if history:
        for item in history:
            role = item.get("role")
            content = item.get("content")
            if role in {"user", "assistant"} and content:
                messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": user_content})
    return messages


def refuse_message() -> str:
    return settings.RAG_REFUSE_MESSAGE
