"""Infrastructure health endpoints (not under /api/v1)."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.db.session import check_mysql

router = APIRouter(tags=["Infra"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready")
async def ready() -> JSONResponse:
    mysql_ok = await check_mysql()
    qdrant_ok = await check_qdrant()
    checks = {
        "mysql": "ok" if mysql_ok else "fail",
        "qdrant": "ok" if qdrant_ok else "fail",
    }
    if not (mysql_ok and qdrant_ok):
        return JSONResponse(
            status_code=503,
            content={
                "code": "SERVICE_UNAVAILABLE",
                "message": "依赖未就绪",
                "request_id": "ready",
                "details": checks,
            },
        )
    return JSONResponse(content={"status": "ready", "checks": checks})


async def check_qdrant() -> bool:
    import httpx

    from app.core.config import settings

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            headers = {}
            if settings.QDRANT_API_KEY:
                headers["api-key"] = settings.QDRANT_API_KEY
            resp = await client.get(f"{settings.QDRANT_URL.rstrip('/')}/readyz", headers=headers)
            return resp.status_code < 500
    except Exception:
        return False
