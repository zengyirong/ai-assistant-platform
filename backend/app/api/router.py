from fastapi import APIRouter

from app.api.v1 import auth, document, knowledge

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["Auth"])
api_router.include_router(
    knowledge.router, prefix="/knowledge-bases", tags=["KnowledgeBase"]
)
api_router.include_router(
    document.kb_documents_router,
    prefix="/knowledge-bases",
    tags=["Document"],
)
api_router.include_router(
    document.documents_router,
    prefix="/documents",
    tags=["Document"],
)
