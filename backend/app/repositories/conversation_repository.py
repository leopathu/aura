"""Repository for Conversation and ChatMessage database operations."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.conversation import ChatMessage, Conversation
from app.schemas.conversation import ConversationCreate


class ConversationRepository:
    """Handles all Conversation and ChatMessage queries."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, user_id: uuid.UUID, payload: ConversationCreate) -> Conversation:
        """Create a new conversation."""
        conv = Conversation(
            user_id=user_id,
            brain_id=payload.brain_id,
            title=payload.title,
        )
        self.db.add(conv)
        await self.db.flush()
        await self.db.refresh(conv)
        return conv

    async def get_by_id(self, conversation_id: uuid.UUID, user_id: uuid.UUID) -> Conversation | None:
        """Fetch a conversation by id, ensuring it belongs to the user."""
        result = await self.db.execute(
            select(Conversation)
            .where(Conversation.id == conversation_id, Conversation.user_id == user_id)
            .options(selectinload(Conversation.messages))
        )
        return result.scalar_one_or_none()

    async def list_by_brain(self, user_id: uuid.UUID, brain_id: uuid.UUID) -> list[Conversation]:
        """List all conversations for a user in a specific brain, newest first."""
        result = await self.db.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id, Conversation.brain_id == brain_id)
            .order_by(Conversation.updated_at.desc())
        )
        return list(result.scalars().all())

    async def update_title(self, conv: Conversation, title: str) -> None:
        """Update conversation title."""
        conv.title = title
        await self.db.flush()

    async def touch(self, conv: Conversation) -> None:
        """Bump updated_at so conversation floats to the top of the list."""
        from sqlalchemy import func  # noqa: PLC0415
        from datetime import datetime, timezone  # noqa: PLC0415
        conv.updated_at = datetime.now(timezone.utc)
        await self.db.flush()

    async def delete(self, conversation_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Delete a conversation. Returns True if it existed."""
        conv = await self.get_by_id(conversation_id, user_id)
        if not conv:
            return False
        await self.db.delete(conv)
        await self.db.flush()
        return True

    async def add_message(
        self,
        conversation_id: uuid.UUID,
        role: str,
        content: str,
        sources_json: str | None = None,
    ) -> ChatMessage:
        """Append a message to a conversation."""
        msg = ChatMessage(
            conversation_id=conversation_id,
            role=role,
            content=content,
            sources_json=sources_json,
        )
        self.db.add(msg)
        await self.db.flush()
        await self.db.refresh(msg)
        return msg
