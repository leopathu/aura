"""Repository for Brain and BrainDocument database queries."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brain import Brain, BrainDocument
from app.models.document import Document
from app.schemas.brain import BrainCreate, BrainUpdate


class BrainRepository:
    """Handles all Brain-related database queries."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, user_id: uuid.UUID, payload: BrainCreate) -> Brain:
        """Create a new brain owned by a user."""
        brain = Brain(
            name=payload.name,
            description=payload.description,
            user_id=user_id,
        )
        self.db.add(brain)
        await self.db.flush()
        await self.db.refresh(brain)
        return brain

    async def list_by_user(self, user_id: uuid.UUID) -> list[Brain]:
        """Return all brains owned by the given user."""
        result = await self.db.execute(
            select(Brain).where(Brain.user_id == user_id).order_by(Brain.created_at)
        )
        return list(result.scalars().all())

    async def get_by_id(self, brain_id: uuid.UUID) -> Brain | None:
        """Fetch a brain by its UUID."""
        result = await self.db.execute(select(Brain).where(Brain.id == brain_id))
        return result.scalar_one_or_none()

    async def update(self, brain: Brain, payload: BrainUpdate) -> Brain:
        """Apply partial updates to a brain."""
        if payload.name is not None:
            brain.name = payload.name
        if payload.description is not None:
            brain.description = payload.description
        await self.db.flush()
        await self.db.refresh(brain)
        return brain

    async def delete(self, brain: Brain) -> None:
        """Delete a brain (cascades to brain_documents)."""
        await self.db.delete(brain)
        await self.db.flush()

    # ------------------------------------------------------------------
    # Document association
    # ------------------------------------------------------------------

    async def list_documents(self, brain_id: uuid.UUID) -> list[Document]:
        """Return all documents connected to a brain."""
        result = await self.db.execute(
            select(Document)
            .join(BrainDocument, BrainDocument.document_id == Document.id)
            .where(BrainDocument.brain_id == brain_id)
            .order_by(Document.created_at)
        )
        return list(result.scalars().all())

    async def add_document(self, brain_id: uuid.UUID, document_id: uuid.UUID) -> None:
        """Associate a document with a brain (idempotent)."""
        existing = await self.db.execute(
            select(BrainDocument).where(
                BrainDocument.brain_id == brain_id,
                BrainDocument.document_id == document_id,
            )
        )
        if existing.scalar_one_or_none() is None:
            self.db.add(BrainDocument(brain_id=brain_id, document_id=document_id))
            await self.db.flush()

    async def remove_document(self, brain_id: uuid.UUID, document_id: uuid.UUID) -> bool:
        """Remove a document from a brain. Returns True if it existed."""
        result = await self.db.execute(
            select(BrainDocument).where(
                BrainDocument.brain_id == brain_id,
                BrainDocument.document_id == document_id,
            )
        )
        assoc = result.scalar_one_or_none()
        if assoc is None:
            return False
        await self.db.delete(assoc)
        await self.db.flush()
        return True

    async def get_document_ids(self, brain_id: uuid.UUID) -> list[uuid.UUID]:
        """Return the list of document UUIDs connected to a brain."""
        result = await self.db.execute(
            select(BrainDocument.document_id).where(BrainDocument.brain_id == brain_id)
        )
        return list(result.scalars().all())
