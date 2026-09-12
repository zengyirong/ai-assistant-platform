from fastapi import APIRouter

from app.api.v1 import auth, knowledge

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(
    knowledge.router, prefix="/knowledge-bases", tags=["KnowledgeBase"]
)
