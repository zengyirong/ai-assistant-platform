"""Filename mention helpers for retrieval preference."""

from __future__ import annotations


def mentioned_document_ids(
    question: str,
    docs: list[tuple[str, str]],
) -> list[str]:
    """If the question mentions a known file name, return matching document ids.

    Prefers longer / more specific names first to avoid short substring false hits.
    """
    q = (question or "").strip()
    if not q or not docs:
        return []
    ranked = sorted(docs, key=lambda item: len(item[1] or ""), reverse=True)
    matched: list[str] = []
    for doc_id, file_name in ranked:
        name = (file_name or "").strip()
        if len(name) < 3:
            continue
        if name in q:
            matched.append(doc_id)
    return matched
