"""Document parse/index job pipeline."""

from __future__ import annotations

import hashlib
import logging
from datetime import UTC, datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import selectinload

from app.ai.embedding import get_embedding_client
from app.ai.parser import parse_document_bytes
from app.ai.parser.errors import DocumentParseError
from app.ai.storage import get_file_storage
from app.ai.vectorstore import get_vector_store
from app.core.errors import AppError
from app.db.session import AsyncSessionLocal
from app.models.document import DocumentChunk, DocumentJob
from app.models.knowledge import RagConfig
from app.modules.job.errors import ParseError, PipelineError

logger = logging.getLogger(__name__)

JOB_STEPS = ("PARSING", "CHUNKING", "EMBEDDING", "INDEXING")
TEXT_TYPES = {"txt", "md", "markdown"}
ALLOWED_TYPES = TEXT_TYPES | {"pdf", "docx"}

__all__ = [
    "ALLOWED_TYPES",
    "JOB_STEPS",
    "ParseError",
    "PipelineError",
    "run_parse_index_job",
    "sha256_hex",
    "simple_chunk_text",
]


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def simple_chunk_text(
    text: str,
    *,
    chunk_size: int = 800,
    chunk_overlap: int = 120,
) -> list[str]:
    cleaned = text.replace("\r\n", "\n").strip()
    if not cleaned:
        return []
    if chunk_size <= 0:
        return [cleaned]
    overlap = max(0, min(chunk_overlap, chunk_size - 1))
    chunks: list[str] = []
    start = 0
    length = len(cleaned)
    while start < length:
        end = min(start + chunk_size, length)
        piece = cleaned[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= length:
            break
        start = max(end - overlap, start + 1)
    return chunks


def chunk_parse_result(
    parse_result,
    *,
    chunk_size: int = 800,
    chunk_overlap: int = 120,
) -> list[tuple[str, int | None, str | None]]:
    """Return (content, page, section) rows preserving segment metadata."""
    rows: list[tuple[str, int | None, str | None]] = []
    for segment in parse_result.segments:
        pieces = simple_chunk_text(
            segment.text,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )
        for piece in pieces:
            rows.append((piece, segment.page, segment.section))
    return rows


async def run_parse_index_job(job_id: str) -> None:
    """Background worker: PENDING → … → SUCCESS/FAILED."""
    storage = get_file_storage()
    embedding = get_embedding_client()
    vectors = get_vector_store()

    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(
                select(DocumentJob)
                .where(DocumentJob.id == job_id)
                .options(selectinload(DocumentJob.document))
            )
            job = result.scalar_one_or_none()
            if job is None or job.document is None:
                return
            doc = job.document
            if doc.status == "DELETED":
                job.status = "CANCELLED"
                job.finished_at = _utcnow()
                await db.commit()
                return

            job.status = "PARSING"
            job.progress = 10
            job.started_at = _utcnow()
            job.error_code = None
            job.error_message = None
            doc.status = "PROCESSING"
            await db.commit()

            raw = await storage.read_bytes(doc.storage_path)
            try:
                parsed = parse_document_bytes(raw, file_type=doc.file_type)
            except DocumentParseError as exc:
                raise PipelineError(exc.code, exc.message) from exc
            if not parsed.has_text:
                raise PipelineError("DOCUMENT_PARSE_FAILED", "文档内容为空，无法分块")

            job.status = "CHUNKING"
            job.progress = 40
            await db.commit()

            rag = await db.scalar(select(RagConfig).where(RagConfig.kb_id == doc.kb_id))
            chunk_size = rag.chunk_size if rag else 800
            chunk_overlap = rag.chunk_overlap if rag else 120
            pieces = chunk_parse_result(
                parsed,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
            )
            if not pieces:
                raise PipelineError("DOCUMENT_PARSE_FAILED", "文档内容为空，无法分块")

            # Replace previous vectors/chunks on re-index
            try:
                await vectors.delete_by_document(doc.id)
            except AppError:
                pass

            await db.execute(
                delete(DocumentChunk).where(DocumentChunk.document_id == doc.id)
            )
            chunk_rows: list[DocumentChunk] = []
            for index, (content, page, section) in enumerate(pieces):
                row = DocumentChunk(
                    org_id=doc.org_id,
                    kb_id=doc.kb_id,
                    document_id=doc.id,
                    chunk_index=index,
                    content=content,
                    content_hash=sha256_hex(content.encode("utf-8")),
                    page=page,
                    section=section,
                    token_count=len(content),
                )
                db.add(row)
                chunk_rows.append(row)
            await db.flush()
            await db.commit()

            job.status = "EMBEDDING"
            job.progress = 70
            await db.commit()

            texts = [c.content for c in chunk_rows]
            try:
                embeddings = await embedding.embed_documents(texts)
            except AppError as exc:
                msg = exc.message
                if exc.details:
                    msg = f"{exc.message} | {exc.details}"
                raise PipelineError(exc.code, msg) from exc
            except Exception as exc:
                raise PipelineError(
                    "INTERNAL_ERROR",
                    f"Embedding 失败: {exc}",
                ) from exc

            if len(embeddings) != len(chunk_rows):
                raise PipelineError("INTERNAL_ERROR", "Embedding 数量与分块不一致")

            job.status = "INDEXING"
            job.progress = 90
            await db.commit()

            points = [
                {
                    "chunk_id": chunk.id,
                    "org_id": chunk.org_id,
                    "kb_id": chunk.kb_id,
                    "document_id": chunk.document_id,
                    "page": chunk.page,
                    "section": chunk.section,
                    "vector": vector,
                }
                for chunk, vector in zip(chunk_rows, embeddings, strict=True)
            ]
            try:
                await vectors.add_chunks(points)
            except AppError as exc:
                raise PipelineError(exc.code, exc.message) from exc

            job.status = "SUCCESS"
            job.progress = 100
            job.finished_at = _utcnow()
            doc.status = "READY"
            doc.page_count = parsed.page_count or len(
                {p for _, p, _ in pieces if p is not None}
            ) or 1
            await db.commit()
        except PipelineError as exc:
            await _fail_job(db, job_id, exc.code, exc.message)
        except Exception:
            logger.exception("document job failed: %s", job_id)
            await _fail_job(
                db,
                job_id,
                "DOCUMENT_PARSE_FAILED",
                "文档处理失败",
            )


async def _fail_job(
    db,
    job_id: str,
    code: str,
    message: str,
) -> None:
    try:
        result = await db.execute(
            select(DocumentJob)
            .where(DocumentJob.id == job_id)
            .options(selectinload(DocumentJob.document))
        )
        job = result.scalar_one_or_none()
        if job is None:
            return
        job.status = "FAILED"
        job.error_code = code
        job.error_message = message[:1024]
        job.finished_at = _utcnow()
        if job.document is not None and job.document.status != "DELETED":
            job.document.status = "FAILED"
        await db.commit()
    except Exception:
        logger.exception("failed to mark job FAILED: %s", job_id)
        await db.rollback()
