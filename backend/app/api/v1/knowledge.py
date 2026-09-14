"""Knowledge base routes."""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import ok
from app.core.auth.deps import CurrentUser
from app.core.rbac import require_permissions
from app.db.session import get_db
from app.modules.audit import service as audit_service
from app.modules.knowledge import service as kb_service

router = APIRouter()

Visibility = Literal["PRIVATE", "SPACE"]
MemberRole = Literal["OWNER", "EDITOR", "VIEWER"]


class KnowledgeBaseCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=1024)
    visibility: Visibility
    space_id: str | None = None


class KnowledgeBaseUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    description: str | None = Field(default=None, max_length=1024)
    visibility: Visibility | None = None
    space_id: str | None = None


class KbMemberAddRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=36)
    role: MemberRole


class RagConfigUpdateRequest(BaseModel):
    chunk_strategy: str | None = None
    chunk_size: int | None = Field(default=None, ge=100, le=8000)
    chunk_overlap: int | None = Field(default=None, ge=0, le=4000)
    top_k: int | None = Field(default=None, ge=1, le=50)
    score_threshold: float | None = None
    llm_model: str | None = None
    temperature: float | None = Field(default=None, ge=0, le=2)
    system_prompt: str | None = None


@router.get("")
async def list_knowledge_bases(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user: CurrentUser = Depends(require_permissions("knowledge:list")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    data = await kb_service.list_knowledge_bases(
        db, user, page=page, page_size=page_size
    )
    return ok(request, data)


@router.post("")
async def create_knowledge_base(
    request: Request,
    body: KnowledgeBaseCreateRequest,
    user: CurrentUser = Depends(require_permissions("knowledge:create")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    data = await kb_service.create_knowledge_base(
        db,
        user,
        name=body.name,
        description=body.description,
        visibility=body.visibility,
        space_id=body.space_id,
    )
    return ok(request, data)


@router.get("/{kb_id}")
async def get_knowledge_base(
    request: Request,
    kb_id: str,
    user: CurrentUser = Depends(require_permissions("knowledge:list")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    data = await kb_service.get_knowledge_base(db, user, kb_id)
    return ok(request, data)


@router.put("/{kb_id}")
async def update_knowledge_base(
    request: Request,
    kb_id: str,
    body: KnowledgeBaseUpdateRequest,
    user: CurrentUser = Depends(require_permissions("knowledge:update")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    payload = body.model_dump(exclude_unset=True)
    data = await kb_service.update_knowledge_base(
        db,
        user,
        kb_id,
        name=payload.get("name"),
        description=payload.get("description"),
        visibility=payload.get("visibility"),
        space_id=payload.get("space_id"),
        space_id_set="space_id" in payload,
    )
    return ok(request, data)


@router.delete("/{kb_id}")
async def delete_knowledge_base(
    request: Request,
    kb_id: str,
    user: CurrentUser = Depends(require_permissions("knowledge:delete")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    await kb_service.delete_knowledge_base(db, user, kb_id)
    return ok(request, {})


@router.get("/{kb_id}/members")
async def list_members(
    request: Request,
    kb_id: str,
    user: CurrentUser = Depends(require_permissions("knowledge:list")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    data = await kb_service.list_members(db, user, kb_id)
    return ok(request, data)


@router.post("/{kb_id}/members")
async def add_member(
    request: Request,
    kb_id: str,
    body: KbMemberAddRequest,
    user: CurrentUser = Depends(require_permissions("knowledge:update")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    await kb_service.add_member(
        db, user, kb_id, user_id=body.user_id, role=body.role
    )
    await audit_service.write_audit(
        action="kb.member.upsert",
        result="SUCCESS",
        org_id=user.org_id,
        user_id=user.id,
        resource_type="knowledge_base",
        resource_id=kb_id,
        detail={"member_user_id": body.user_id, "role": body.role},
        request=request,
    )
    return ok(request, {})


@router.delete("/{kb_id}/members/{user_id}")
async def remove_member(
    request: Request,
    kb_id: str,
    user_id: str,
    user: CurrentUser = Depends(require_permissions("knowledge:update")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    await kb_service.remove_member(db, user, kb_id, user_id)
    await audit_service.write_audit(
        action="kb.member.remove",
        result="SUCCESS",
        org_id=user.org_id,
        user_id=user.id,
        resource_type="knowledge_base",
        resource_id=kb_id,
        detail={"member_user_id": user_id},
        request=request,
    )
    return ok(request, {})


@router.get("/{kb_id}/rag-config")
async def get_rag_config(
    request: Request,
    kb_id: str,
    user: CurrentUser = Depends(require_permissions("knowledge:list")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    data = await kb_service.get_rag_config(db, user, kb_id)
    return ok(request, data)


@router.put("/{kb_id}/rag-config")
async def update_rag_config(
    request: Request,
    kb_id: str,
    body: RagConfigUpdateRequest,
    user: CurrentUser = Depends(require_permissions("knowledge:update")),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    data = await kb_service.update_rag_config(
        db, user, kb_id, body.model_dump(exclude_unset=True)
    )
    return ok(request, data)
