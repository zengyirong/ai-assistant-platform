"""Retrieval package — keep imports lazy to avoid model circular imports in unit tests."""

from __future__ import annotations

from typing import Any

__all__ = [
    "RetrievedChunk",
    "mentioned_document_ids",
    "retrieve_chunks",
    "to_citation_dicts",
]


def __getattr__(name: str) -> Any:
    if name == "mentioned_document_ids":
        from app.ai.retrieval.filename import mentioned_document_ids

        return mentioned_document_ids
    if name in {"RetrievedChunk", "retrieve_chunks", "to_citation_dicts"}:
        from app.ai.retrieval import service as retrieval_service

        return getattr(retrieval_service, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
