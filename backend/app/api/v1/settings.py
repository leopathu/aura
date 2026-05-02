"""AI settings routes — GET and PUT for current user's model configuration."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.repositories.ai_settings_repository import AISettingsRepository
from app.schemas.ai_settings import AISettingsResponse, AISettingsUpdate

router = APIRouter(prefix="/settings", tags=["Settings"])


def _to_response(row) -> AISettingsResponse:  # type: ignore[no-untyped-def]
    """Map an AISettings ORM row to the response schema, masking API keys."""
    return AISettingsResponse(
        llm_provider=row.llm_provider,
        llm_model=row.llm_model,
        llm_api_key_set=bool(row.llm_api_key),
        llm_base_url=row.llm_base_url,
        temperature=row.temperature,
        embedding_provider=row.embedding_provider,
        embedding_model=row.embedding_model,
        embedding_api_key_set=bool(row.embedding_api_key),
        embedding_base_url=row.embedding_base_url,
        chunk_size=row.chunk_size,
        chunk_overlap=row.chunk_overlap,
        retrieval_top_k=row.retrieval_top_k,
    )


@router.get("", response_model=AISettingsResponse)
async def get_settings(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AISettingsResponse:
    """Return the current user's AI settings (or defaults if not yet configured)."""
    repo = AISettingsRepository(db)
    row = await repo.get_by_user(current_user.id)
    if row is None:
        # Return defaults without creating a row
        from app.models.ai_settings import AISettings  # noqa: PLC0415

        row = AISettings()
    return _to_response(row)


@router.put("", response_model=AISettingsResponse)
async def update_settings(
    payload: AISettingsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> AISettingsResponse:
    """Upsert the current user's AI settings."""
    repo = AISettingsRepository(db)
    row = await repo.upsert(current_user.id, payload)
    return _to_response(row)
