"""Knowledge base application service."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.auth.deps import CurrentUser
from app.core.errors import AppError
from app.core.rbac import is_admin
from app.models.knowledge import KnowledgeBase, KnowledgeBaseMember, RagConfig
from app.models.organization import Space, SpaceMember

AccessLevel = Literal["VIEW", "EDIT", "MANAGE"]


def _iso(dt: datetime | None) -> str | None:
    return dt.isoformat(sep="T", timespec="milliseconds") if dt else None


def kb_to_dict(kb: KnowledgeBase, *, document_count: int | None = 0) -> dict[str, Any]:
    return {
        "id": kb.id,
        "org_id": kb.org_id,
        "space_id": kb.space_id,
        "name": kb.name,
        "description": kb.description,
        "visibility": kb.visibility,
        "status": kb.status,
        "created_by": kb.created_by,
        "document_count": document_count,
        "created_at": _iso(kb.created_at),
        "updated_at": _iso(kb.updated_at),
    }


def member_to_dict(member: KnowledgeBaseMember) -> dict[str, Any]:
    return {
        "user_id": member.user_id,
        "role": member.role,
        "created_at": _iso(member.created_at),
    }


def rag_config_to_dict(cfg: RagConfig) -> dict[str, Any]:
    return {
        "id": cfg.id,
        "kb_id": cfg.kb_id,
        "chunk_strategy": cfg.chunk_strategy,
        "chunk_size": cfg.chunk_size,
        "chunk_overlap": cfg.chunk_overlap,
        "top_k": cfg.top_k,
        "score_threshold": (
            float(cfg.score_threshold) if cfg.score_threshold is not None else None
        ),
        "llm_model": cfg.llm_model,
        "temperature": float(cfg.temperature),
        "system_prompt": cfg.system_prompt,
        "created_at": _iso(cfg.created_at),
        "updated_at": _iso(cfg.updated_at),
    }


def _member_role(kb: KnowledgeBase, user_id: str) -> str | None:
    for member in kb.members:
        if member.user_id == user_id:
            return member.role
    return None


async def _space_member_ids(
    db: AsyncSession,
    *,
    user_id: str,
) -> set[str]:
    result = await db.execute(
        select(SpaceMember.space_id).where(SpaceMember.user_id == user_id)
    )
    return set(result.scalars().all())


def user_can_view_kb(
    user: CurrentUser,
    kb: KnowledgeBase,
    *,
    space_ids: set[str],
) -> bool:
    if kb.org_id != user.org_id:
        return False
    if kb.status != "ACTIVE" and not is_admin(user):
        return False
    if is_admin(user):
        return True
    if kb.created_by == user.id:
        return True
    if _member_role(kb, user.id) is not None:
        return True
    if kb.visibility == "SPACE" and kb.space_id and kb.space_id in space_ids:
        return True
    return False


def user_access_level(
    user: CurrentUser,
    kb: KnowledgeBase,
    *,
    space_ids: set[str],
) -> AccessLevel | None:
    if not user_can_view_kb(user, kb, space_ids=space_ids):
        return None
    if is_admin(user):
        return "MANAGE"
    role = _member_role(kb, user.id)
    if role == "OWNER":
        return "MANAGE"
    if role == "EDITOR":
        return "EDIT"
    if role == "VIEWER":
        return "VIEW"
    if kb.created_by == user.id:
        return "MANAGE"
    return "VIEW"


def require_level(level: AccessLevel | None, needed: AccessLevel) -> None:
    order = {"VIEW": 1, "EDIT": 2, "MANAGE": 3}
    if level is None:
        raise AppError("KB_NOT_FOUND", "知识库不存在或不可见", http_status=404)
    if order[level] < order[needed]:
        raise AppError("KB_PERMISSION_DENIED", "无权操作该知识库", http_status=403)


async def _get_kb(
    db: AsyncSession,
    kb_id: str,
    *,
    with_rag: bool = False,
) -> KnowledgeBase | None:
    options = [selectinload(KnowledgeBase.members)]
    if with_rag:
        options.append(selectinload(KnowledgeBase.rag_config))
    result = await db.execute(
        select(KnowledgeBase).where(KnowledgeBase.id == kb_id).options(*options)
    )
    return result.scalar_one_or_none()


async def _ensure_space(
    db: AsyncSession,
    *,
    org_id: str,
    space_id: str | None,
    visibility: str,
) -> str | None:
    if visibility == "PRIVATE":
        return space_id
    if visibility != "SPACE":
        raise AppError("VALIDATION_ERROR", "visibility 无效", http_status=400)
    if not space_id:
        raise AppError(
            "VALIDATION_ERROR",
            "SPACE 可见性必须指定 space_id",
            http_status=400,
        )
    result = await db.execute(
        select(Space).where(Space.id == space_id, Space.org_id == org_id)
    )
    space = result.scalar_one_or_none()
    if space is None:
        raise AppError("SPACE_NOT_FOUND", "空间不存在", http_status=404)
    return space_id


def _accessible_filter(
    user: CurrentUser,
    *,
    space_ids: set[str],
) -> Any:
    if is_admin(user):
        return KnowledgeBase.org_id == user.org_id

    member_exists = (
        select(KnowledgeBaseMember.id)
        .where(
            KnowledgeBaseMember.kb_id == KnowledgeBase.id,
            KnowledgeBaseMember.user_id == user.id,
        )
        .exists()
    )
    clauses = [
        KnowledgeBase.created_by == user.id,
        member_exists,
    ]
    if space_ids:
        clauses.append(
            (KnowledgeBase.visibility == "SPACE")
            & KnowledgeBase.space_id.in_(space_ids)
        )
    return (KnowledgeBase.org_id == user.org_id) & or_(*clauses)


async def list_knowledge_bases(
    db: AsyncSession,
    user: CurrentUser,
    *,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    space_ids = await _space_member_ids(db, user_id=user.id)
    filters = [
        _accessible_filter(user, space_ids=space_ids),
        KnowledgeBase.status == "ACTIVE",
    ]
    base: Select[Any] = select(KnowledgeBase).where(*filters)
    total = await db.scalar(select(func.count()).select_from(base.subquery()))
    result = await db.execute(
        base.order_by(KnowledgeBase.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .options(selectinload(KnowledgeBase.members))
    )
    items = [kb_to_dict(kb) for kb in result.scalars().all()]
    return {
        "items": items,
        "total": int(total or 0),
        "page": page,
        "page_size": page_size,
    }


async def create_knowledge_base(
    db: AsyncSession,
    user: CurrentUser,
    *,
    name: str,
    visibility: str,
    description: str | None = None,
    space_id: str | None = None,
) -> dict[str, Any]:
    resolved_space = await _ensure_space(
        db,
        org_id=user.org_id,
        space_id=space_id,
        visibility=visibility,
    )
    kb = KnowledgeBase(
        org_id=user.org_id,
        space_id=resolved_space if visibility == "SPACE" else None,
        name=name.strip(),
        description=description,
        visibility=visibility,
        status="ACTIVE",
        created_by=user.id,
    )
    db.add(kb)
    await db.flush()
    db.add(
        KnowledgeBaseMember(
            kb_id=kb.id,
            user_id=user.id,
            role="OWNER",
        )
    )
    db.add(RagConfig(kb_id=kb.id))
    await db.flush()
    await db.refresh(kb)
    return kb_to_dict(kb)


async def get_knowledge_base(
    db: AsyncSession,
    user: CurrentUser,
    kb_id: str,
) -> dict[str, Any]:
    kb = await _get_kb(db, kb_id)
    if kb is None or kb.status != "ACTIVE":
        raise AppError("KB_NOT_FOUND", "知识库不存在或不可见", http_status=404)
    space_ids = await _space_member_ids(db, user_id=user.id)
    require_level(user_access_level(user, kb, space_ids=space_ids), "VIEW")
    return kb_to_dict(kb)


async def update_knowledge_base(
    db: AsyncSession,
    user: CurrentUser,
    kb_id: str,
    *,
    name: str | None = None,
    description: str | None = None,
    visibility: str | None = None,
    space_id: str | None = None,
    space_id_set: bool = False,
) -> dict[str, Any]:
    kb = await _get_kb(db, kb_id)
    if kb is None or kb.status != "ACTIVE":
        raise AppError("KB_NOT_FOUND", "知识库不存在或不可见", http_status=404)
    space_ids = await _space_member_ids(db, user_id=user.id)
    require_level(user_access_level(user, kb, space_ids=space_ids), "EDIT")

    next_visibility = visibility if visibility is not None else kb.visibility
    next_space = kb.space_id
    if space_id_set:
        next_space = space_id
    if visibility is not None or space_id_set:
        next_space = await _ensure_space(
            db,
            org_id=user.org_id,
            space_id=next_space,
            visibility=next_visibility,
        )
        if next_visibility == "PRIVATE":
            next_space = None

    if name is not None:
        kb.name = name.strip()
    if description is not None:
        kb.description = description
    kb.visibility = next_visibility
    kb.space_id = next_space
    await db.flush()
    await db.refresh(kb)
    return kb_to_dict(kb)


async def delete_knowledge_base(
    db: AsyncSession,
    user: CurrentUser,
    kb_id: str,
) -> None:
    kb = await _get_kb(db, kb_id)
    if kb is None or kb.status != "ACTIVE":
        raise AppError("KB_NOT_FOUND", "知识库不存在或不可见", http_status=404)
    space_ids = await _space_member_ids(db, user_id=user.id)
    require_level(user_access_level(user, kb, space_ids=space_ids), "MANAGE")
    kb.status = "ARCHIVED"
    await db.flush()


async def list_members(
    db: AsyncSession,
    user: CurrentUser,
    kb_id: str,
) -> dict[str, Any]:
    kb = await _get_kb(db, kb_id)
    if kb is None or kb.status != "ACTIVE":
        raise AppError("KB_NOT_FOUND", "知识库不存在或不可见", http_status=404)
    space_ids = await _space_member_ids(db, user_id=user.id)
    require_level(user_access_level(user, kb, space_ids=space_ids), "VIEW")
    return {"items": [member_to_dict(m) for m in kb.members]}


async def add_member(
    db: AsyncSession,
    user: CurrentUser,
    kb_id: str,
    *,
    user_id: str,
    role: str,
) -> None:
    if role not in {"OWNER", "EDITOR", "VIEWER"}:
        raise AppError("VALIDATION_ERROR", "成员角色无效", http_status=400)
    kb = await _get_kb(db, kb_id)
    if kb is None or kb.status != "ACTIVE":
        raise AppError("KB_NOT_FOUND", "知识库不存在或不可见", http_status=404)
    space_ids = await _space_member_ids(db, user_id=user.id)
    require_level(user_access_level(user, kb, space_ids=space_ids), "MANAGE")

    existing = _member_role(kb, user_id)
    if existing is not None:
        for member in kb.members:
            if member.user_id == user_id:
                member.role = role
                break
    else:
        db.add(
            KnowledgeBaseMember(
                kb_id=kb.id,
                user_id=user_id,
                role=role,
            )
        )
    await db.flush()


async def remove_member(
    db: AsyncSession,
    user: CurrentUser,
    kb_id: str,
    target_user_id: str,
) -> None:
    kb = await _get_kb(db, kb_id)
    if kb is None or kb.status != "ACTIVE":
        raise AppError("KB_NOT_FOUND", "知识库不存在或不可见", http_status=404)
    space_ids = await _space_member_ids(db, user_id=user.id)
    require_level(user_access_level(user, kb, space_ids=space_ids), "MANAGE")

    target = next((m for m in kb.members if m.user_id == target_user_id), None)
    if target is None:
        raise AppError("KB_NOT_FOUND", "成员不存在", http_status=404)
    if target.role == "OWNER":
        owner_count = sum(1 for m in kb.members if m.role == "OWNER")
        if owner_count <= 1:
            raise AppError(
                "VALIDATION_ERROR",
                "不能移除最后一个 OWNER",
                http_status=400,
            )
    await db.delete(target)
    await db.flush()


async def get_rag_config(
    db: AsyncSession,
    user: CurrentUser,
    kb_id: str,
) -> dict[str, Any]:
    kb = await _get_kb(db, kb_id, with_rag=True)
    if kb is None or kb.status != "ACTIVE":
        raise AppError("KB_NOT_FOUND", "知识库不存在或不可见", http_status=404)
    space_ids = await _space_member_ids(db, user_id=user.id)
    require_level(user_access_level(user, kb, space_ids=space_ids), "VIEW")
    if kb.rag_config is None:
        raise AppError("KB_NOT_FOUND", "RAG 配置不存在", http_status=404)
    return rag_config_to_dict(kb.rag_config)


async def update_rag_config(
    db: AsyncSession,
    user: CurrentUser,
    kb_id: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    kb = await _get_kb(db, kb_id, with_rag=True)
    if kb is None or kb.status != "ACTIVE":
        raise AppError("KB_NOT_FOUND", "知识库不存在或不可见", http_status=404)
    space_ids = await _space_member_ids(db, user_id=user.id)
    require_level(user_access_level(user, kb, space_ids=space_ids), "EDIT")
    cfg = kb.rag_config
    if cfg is None:
        cfg = RagConfig(kb_id=kb.id)
        db.add(cfg)
        await db.flush()

    field_map = {
        "chunk_strategy": str,
        "chunk_size": int,
        "chunk_overlap": int,
        "top_k": int,
        "llm_model": lambda v: v,
        "system_prompt": lambda v: v,
    }
    for key, caster in field_map.items():
        if key in payload and payload[key] is not None:
            setattr(cfg, key, caster(payload[key]))
    if "score_threshold" in payload:
        value = payload["score_threshold"]
        cfg.score_threshold = None if value is None else Decimal(str(value))
    if "temperature" in payload and payload["temperature"] is not None:
        cfg.temperature = Decimal(str(payload["temperature"]))

    await db.flush()
    await db.refresh(cfg)
    return rag_config_to_dict(cfg)
