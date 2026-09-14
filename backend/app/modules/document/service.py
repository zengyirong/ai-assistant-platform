"""Document application service."""

from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from pathlib import PurePosixPath
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.storage import get_file_storage
from app.ai.vectorstore import get_vector_store
from app.core.auth.deps import CurrentUser
from app.core.config import settings
from app.core.errors import AppError
from app.models.conversation import MessageCitation
from app.models.document import Document, DocumentChunk, DocumentJob
from app.modules.job.pipeline import ALLOWED_TYPES, sha256_hex
from app.modules.knowledge import service as kb_service


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _iso(dt: datetime | None) -> str | None:
    return dt.isoformat(sep="T", timespec="milliseconds") if dt else None


def document_to_dict(doc: Document, *, job_id: str | None = None) -> dict[str, Any]:
    data = {
        "id": doc.id,
        "org_id": doc.org_id,
        "kb_id": doc.kb_id,
        "file_name": doc.file_name,
        "file_hash": doc.file_hash,
        "file_type": doc.file_type,
        "file_size": int(doc.file_size),
        "page_count": doc.page_count,
        "status": doc.status,
        "created_by": doc.created_by,
        "created_at": _iso(doc.created_at),
        "updated_at": _iso(doc.updated_at),
    }
    if job_id is not None:
        data["job_id"] = job_id
    return data


def job_to_dict(job: DocumentJob) -> dict[str, Any]:
    return {
        "id": job.id,
        "document_id": job.document_id,
        "job_type": job.job_type,
        "status": job.status,
        "progress": job.progress,
        "retry_count": job.retry_count,
        "error_code": job.error_code,
        "error_message": job.error_message,
        "started_at": _iso(job.started_at),
        "finished_at": _iso(job.finished_at),
        "created_at": _iso(job.created_at),
        "updated_at": _iso(job.updated_at),
    }


def _detect_file_type(filename: str) -> str:
    suffix = PurePosixPath(filename).suffix.lower().lstrip(".")
    return suffix


def _validate_upload(filename: str, size: int) -> str:
    file_type = _detect_file_type(filename)
    if not file_type or file_type not in ALLOWED_TYPES:
        raise AppError(
            "DOCUMENT_FORMAT_INVALID",
            f"不支持的文件类型: .{file_type or 'unknown'}",
            http_status=422,
        )
    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if size <= 0:
        raise AppError("VALIDATION_ERROR", "空文件不可上传", http_status=400)
    if size > max_bytes:
        raise AppError(
            "DOCUMENT_TOO_LARGE",
            f"文件超过 {settings.MAX_UPLOAD_SIZE_MB}MB 限制",
            http_status=422,
        )
    return file_type


async def list_documents(
    db: AsyncSession,
    user: CurrentUser,
    kb_id: str,
    *,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    await kb_service.ensure_kb_access(db, user, kb_id, needed="VIEW")
    filters = [
        Document.kb_id == kb_id,
        Document.org_id == user.org_id,
        Document.status != "DELETED",
    ]
    base: Select[Any] = select(Document).where(*filters)
    total = await db.scalar(select(func.count()).select_from(base.subquery()))
    result = await db.execute(
        base.order_by(Document.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = [document_to_dict(doc) for doc in result.scalars().all()]
    return {
        "items": items,
        "total": int(total or 0),
        "page": page,
        "page_size": page_size,
    }


async def upload_document(
    db: AsyncSession,
    user: CurrentUser,
    kb_id: str,
    *,
    filename: str,
    data: bytes,
) -> tuple[dict[str, Any], str]:
    kb = await kb_service.ensure_kb_access(db, user, kb_id, needed="EDIT")
    file_type = _validate_upload(filename, len(data))
    file_hash = sha256_hex(data)

    existing = await db.scalar(
        select(Document.id).where(
            Document.kb_id == kb_id,
            Document.file_hash == file_hash,
            Document.status != "DELETED",
        )
    )
    if existing:
        raise AppError(
            "DOCUMENT_DUPLICATED",
            "知识库内已存在相同文件",
            http_status=409,
        )

    storage = get_file_storage()
    doc = Document(
        org_id=kb.org_id,
        kb_id=kb_id,
        file_name=filename,
        storage_path="",  # set after id
        file_hash=file_hash,
        file_type=file_type,
        file_size=len(data),
        status="UPLOADED",
        created_by=user.id,
    )
    db.add(doc)
    await db.flush()

    key = f"{kb.org_id}/{kb_id}/{doc.id}/{filename}"
    await storage.save_bytes(data, key=key)
    doc.storage_path = key

    job = DocumentJob(
        document_id=doc.id,
        job_type="PARSE_INDEX",
        status="PENDING",
        progress=0,
    )
    db.add(job)
    try:
        await db.flush()
    except IntegrityError as exc:
        await db.rollback()
        raise AppError(
            "DOCUMENT_DUPLICATED",
            "知识库内已存在相同文件",
            http_status=409,
        ) from exc

    await db.commit()
    await db.refresh(doc)
    await db.refresh(job)
    return document_to_dict(doc, job_id=job.id), job.id


async def get_document(
    db: AsyncSession,
    user: CurrentUser,
    document_id: str,
) -> dict[str, Any]:
    doc = await _get_document(db, document_id)
    await kb_service.ensure_kb_access(db, user, doc.kb_id, needed="VIEW")
    return document_to_dict(doc)


async def delete_document(
    db: AsyncSession,
    user: CurrentUser,
    document_id: str,
) -> None:
    doc = await _get_document(db, document_id)
    await kb_service.ensure_kb_access(db, user, doc.kb_id, needed="EDIT")

    storage = get_file_storage()
    try:
        await storage.delete(doc.storage_path)
    except Exception:
        pass

    try:
        await get_vector_store().delete_by_document(doc.id)
    except AppError:
        # Soft-delete still proceeds; vectors can be cleaned by retry/ops later
        pass

    # Citations keep FK to chunk/document without CASCADE — clear first.
    await db.execute(
        MessageCitation.__table__.delete().where(
            MessageCitation.document_id == doc.id
        )
    )
    await db.execute(
        DocumentChunk.__table__.delete().where(DocumentChunk.document_id == doc.id)
    )
    # Free UNIQUE(kb_id, file_hash) so the same file can be re-uploaded
    doc.file_hash = hashlib.sha256(
        f"{doc.file_hash}:deleted:{doc.id}".encode()
    ).hexdigest()
    doc.status = "DELETED"
    for job in doc.jobs:
        if job.status in {"PENDING", "PARSING", "CHUNKING", "EMBEDDING", "INDEXING"}:
            job.status = "CANCELLED"
            job.finished_at = _utcnow()
    await db.commit()


async def retry_document(
    db: AsyncSession,
    user: CurrentUser,
    document_id: str,
) -> dict[str, Any]:
    doc = await _get_document(db, document_id)
    await kb_service.ensure_kb_access(db, user, doc.kb_id, needed="EDIT")
    if doc.status not in {"FAILED", "UPLOADED"}:
        raise AppError(
            "VALIDATION_ERROR",
            "仅 FAILED / UPLOADED 文档可重试",
            http_status=400,
        )

    prev_retry = 0
    for job in doc.jobs:
        prev_retry = max(prev_retry, job.retry_count)

    job = DocumentJob(
        document_id=doc.id,
        job_type="PARSE_INDEX",
        status="PENDING",
        progress=0,
        retry_count=prev_retry + 1,
    )
    doc.status = "UPLOADED"
    db.add(job)
    await db.commit()
    await db.refresh(job)
    return job_to_dict(job)


async def list_jobs(
    db: AsyncSession,
    user: CurrentUser,
    document_id: str,
) -> dict[str, Any]:
    doc = await _get_document(db, document_id)
    await kb_service.ensure_kb_access(db, user, doc.kb_id, needed="VIEW")
    items = sorted(doc.jobs, key=lambda j: j.created_at or datetime.min, reverse=True)
    return {"items": [job_to_dict(j) for j in items]}


async def _get_document(db: AsyncSession, document_id: str) -> Document:
    result = await db.execute(
        select(Document)
        .where(Document.id == document_id)
        .options(selectinload(Document.jobs))
    )
    doc = result.scalar_one_or_none()
    if doc is None or doc.status == "DELETED":
        raise AppError("DOCUMENT_NOT_FOUND", "文档不存在", http_status=404)
    return doc
