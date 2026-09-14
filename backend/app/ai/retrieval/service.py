"""RAG retriever: Qdrant search → MySQL chunk content."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.embedding import get_embedding_client
from app.ai.retrieval.filename import mentioned_document_ids
from app.ai.vectorstore import get_vector_store
from app.core.config import settings
from app.models.document import Document, DocumentChunk


@dataclass
class RetrievedChunk:
    chunk_id: str
    document_id: str
    document_name: str | None
    kb_id: str
    org_id: str
    content: str
    page: int | None
    section: str | None
    score: float


async def retrieve_chunks(
    db: AsyncSession,
    *,
    org_id: str,
    kb_ids: list[str],
    question: str,
    top_k: int | None = None,
    score_threshold: float | None = None,
) -> list[RetrievedChunk]:
    if not kb_ids:
        return []

    limit = top_k or settings.RAG_TOP_K
    threshold = (
        score_threshold
        if score_threshold is not None
        else settings.RAG_SCORE_THRESHOLD
    )

    # Prefer documents whose file names are explicitly mentioned in the question.
    doc_rows = await db.execute(
        select(Document.id, Document.file_name).where(
            Document.org_id == org_id,
            Document.kb_id.in_(kb_ids),
            Document.status != "DELETED",
        )
    )
    kb_docs = [(row[0], row[1] or "") for row in doc_rows.all()]
    mentioned_ids = mentioned_document_ids(question, kb_docs)

    embedding = get_embedding_client()
    store = get_vector_store()
    query_vector = await embedding.embed_query(question)
    filters: dict[str, Any] = {"org_id": org_id, "kb_ids": kb_ids}
    if mentioned_ids:
        filters["document_ids"] = mentioned_ids

    hits = await store.search(
        query_vector,
        filters=filters,
        top_k=limit,
    )

    # If filename filter yields nothing, fall back to normal KB search.
    if mentioned_ids and not hits:
        hits = await store.search(
            query_vector,
            filters={"org_id": org_id, "kb_ids": kb_ids},
            top_k=limit,
        )

    if not hits:
        return []

    if threshold is not None:
        hits = [h for h in hits if (h.get("score") or 0) >= threshold]
    if not hits:
        return []

    chunk_ids = [h["chunk_id"] for h in hits]
    result = await db.execute(
        select(DocumentChunk, Document.file_name)
        .join(Document, Document.id == DocumentChunk.document_id)
        .where(DocumentChunk.id.in_(chunk_ids))
    )
    rows = {chunk.id: (chunk, file_name) for chunk, file_name in result.all()}
    # Fallback map by document_id if chunk id lookup misses due to id format drift
    name_by_doc = {doc_id: name for doc_id, name in kb_docs if name}

    retrieved: list[RetrievedChunk] = []
    for hit in hits:
        pair = rows.get(hit["chunk_id"])
        if not pair:
            # try normalized id match
            hit_cid = str(hit.get("chunk_id") or "")
            pair = next(
                (
                    rows[cid]
                    for cid in rows
                    if cid == hit_cid or cid.replace("-", "") == hit_cid.replace("-", "")
                ),
                None,
            )
        if not pair:
            continue
        chunk, file_name = pair
        retrieved.append(
            RetrievedChunk(
                chunk_id=chunk.id,
                document_id=chunk.document_id,
                document_name=file_name or name_by_doc.get(chunk.document_id),
                kb_id=chunk.kb_id,
                org_id=chunk.org_id,
                content=chunk.content,
                page=chunk.page if chunk.page is not None else hit.get("page"),
                section=chunk.section if chunk.section is not None else hit.get("section"),
                score=float(hit.get("score") or 0),
            )
        )
    return retrieved


def to_citation_dicts(chunks: list[RetrievedChunk]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for i, chunk in enumerate(chunks):
        snippet = chunk.content.strip().replace("\n", " ")
        if len(snippet) > 240:
            snippet = snippet[:237] + "..."
        items.append(
            {
                "document_id": chunk.document_id,
                "document_name": chunk.document_name,
                "chunk_id": chunk.chunk_id,
                "page": chunk.page,
                "section": chunk.section,
                "score": chunk.score,
                "snippet": snippet,
                "sort_order": i,
            }
        )
    return items
