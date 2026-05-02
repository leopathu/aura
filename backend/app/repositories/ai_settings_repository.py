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
        """Create or fully replace the AI settings for a user."""
        row = await self.get_by_user(user_id)
        if row is None:
            row = AISettings(user_id=user_id)
            self._db.add(row)

        for field, value in payload.model_dump().items():
            setattr(row, field, value)

        await self._db.flush()
        await self._db.refresh(row)
        return row
