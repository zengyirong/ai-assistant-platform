"""Document routes."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, File, Query, Request, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import ok
from app.core.auth.deps import CurrentUser
from app.core.rbac import require_permissions
from app.db.session import get_db
from app.modules.audit import service as audit_service
from app.modules.document import service as doc_service
from app.modules.job.pipeline import run_parse_index_job

kb_documents_router = APIRouter()
documents_router = APIRouter()


@kb_documents_router.get("/{kb_id}/documents")
async def list_documents(
    request: Request,
    kb_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: CurrentUser = Depends(require_permissions("document:list")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    data = await doc_service.list_documents(
        db, user, kb_id, page=page, page_size=page_size
    )
    return ok(request, data)


@kb_documents_router.post("/{kb_id}/documents")
async def upload_document(
    request: Request,
    kb_id: str,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user: CurrentUser = Depends(require_permissions("document:upload")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    raw = await file.read()
    filename = file.filename or "unnamed.bin"
    data, job_id = await doc_service.upload_document(
        db,
        user,
        kb_id,
        filename=filename,
        data=raw,
    )
    background_tasks.add_task(run_parse_index_job, job_id)
    await audit_service.write_audit(
        action="document.upload",
        result="SUCCESS",
        org_id=user.org_id,
        user_id=user.id,
        resource_type="document",
        resource_id=data.get("id"),
        detail={
            "kb_id": kb_id,
            "file_name": filename,
            "file_size": data.get("file_size"),
            "job_id": job_id,
        },
        request=request,
    )
    return ok(request, data)


@documents_router.get("/{document_id}")
async def get_document(
    request: Request,
    document_id: str,
    user: CurrentUser = Depends(require_permissions("document:list")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    data = await doc_service.get_document(db, user, document_id)
    return ok(request, data)


@documents_router.delete("/{document_id}")
async def delete_document(
    request: Request,
    document_id: str,
    user: CurrentUser = Depends(require_permissions("document:delete")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    await doc_service.delete_document(db, user, document_id)
    await audit_service.write_audit(
        action="document.delete",
        result="SUCCESS",
        org_id=user.org_id,
        user_id=user.id,
        resource_type="document",
        resource_id=document_id,
        request=request,
    )
    return ok(request, {})


@documents_router.post("/{document_id}/retry")
async def retry_document(
    request: Request,
    document_id: str,
    background_tasks: BackgroundTasks,
    user: CurrentUser = Depends(require_permissions("document:retry")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    job = await doc_service.retry_document(db, user, document_id)
    background_tasks.add_task(run_parse_index_job, job["id"])
    await audit_service.write_audit(
        action="document.retry",
        result="SUCCESS",
        org_id=user.org_id,
        user_id=user.id,
        resource_type="document",
        resource_id=document_id,
        detail={"job_id": job.get("id")},
        request=request,
    )
    return ok(request, job)

@documents_router.get("/{document_id}/jobs")
async def list_jobs(
    request: Request,
    document_id: str,
    user: CurrentUser = Depends(require_permissions("document:list")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    data = await doc_service.list_jobs(db, user, document_id)
    return ok(request, data)
