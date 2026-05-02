"""Repository for AI settings — one row per user, upserted."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.ai_settings import AISettings
from app.schemas.ai_settings import AISettingsUpdate


class AISettingsRepository:
    """Database access layer for user AI settings."""

    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def get_by_user(self, user_id: uuid.UUID) -> AISettings | None:
        """Return the AI settings row for a user, or None if not yet configured."""
        result = await self._db.execute(
            select(AISettings).where(AISettings.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def upsert(self, user_id: uuid.UUID, payload: AISettingsUpdate) -> AISettings:
        """Create or update AI settings for a user.

        API key fields are only updated when a non-empty value is submitted,
        so the frontend can omit keys (blank = keep current).
        """
        row = await self.get_by_user(user_id)
        if row is None:
            row = AISettings(user_id=user_id)
            self._db.add(row)

        KEY_FIELDS = {"llm_api_key", "embedding_api_key"}
        for field, value in payload.model_dump().items():
            if field in KEY_FIELDS and not value:
                # blank submitted → keep the stored key
                continue
            setattr(row, field, value)

        await self._db.flush()
        await self._db.refresh(row)
        return row
