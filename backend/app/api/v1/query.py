"""RAG query route."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.repositories.ai_settings_repository import AISettingsRepository
from app.schemas.query import QueryRequest, QueryResponse
from app.services.rag_service import RAGService

router = APIRouter(prefix="/query", tags=["Query"])


@router.post("/", response_model=QueryResponse)
async def query(
    request: QueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> QueryResponse:
    """Run a RAG query: embed → retrieve → generate → respond."""
    ai = await AISettingsRepository(db).get_by_user(current_user.id)
    svc = RAGService(db, ai=ai)
    return await svc.query(request)
