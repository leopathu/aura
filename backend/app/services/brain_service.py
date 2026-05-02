"""Brain CRUD service."""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuraException
from app.models.brain import Brain
from app.models.document import Document
from app.repositories.brain_repository import BrainRepository
from app.repositories.document_repository import DocumentRepository
from app.schemas.brain import BrainCreate, BrainUpdate


class BrainService:
    """Handles brain creation, updates, deletion, and document association."""

    def __init__(self, db: AsyncSession) -> None:
        self._repo = BrainRepository(db)
        self._doc_repo = DocumentRepository(db)

    async def create(self, user_id: uuid.UUID, payload: BrainCreate) -> Brain:
        """Create a new brain owned by the given user."""
        return await self._repo.create(user_id, payload)

    async def list_for_user(self, user_id: uuid.UUID) -> list[Brain]:
        """Return all brains belonging to the user."""
        return await self._repo.list_by_user(user_id)

    async def get(self, brain_id: uuid.UUID, user_id: uuid.UUID) -> Brain:
        """Fetch a brain, ensuring it belongs to the requesting user."""
        brain = await self._repo.get_by_id(brain_id)
        if not brain or brain.user_id != user_id:
            raise AuraException(detail="Brain not found.", code="BRAIN_NOT_FOUND")
        return brain

    async def update(self, brain_id: uuid.UUID, user_id: uuid.UUID, payload: BrainUpdate) -> Brain:
        """Update a brain's metadata."""
        brain = await self.get(brain_id, user_id)
        return await self._repo.update(brain, payload)

    async def delete(self, brain_id: uuid.UUID, user_id: uuid.UUID) -> None:
        """Delete a brain."""
        brain = await self.get(brain_id, user_id)
        await self._repo.delete(brain)

    async def list_documents(self, brain_id: uuid.UUID, user_id: uuid.UUID) -> list[Document]:
        """Return documents connected to a brain."""
        await self.get(brain_id, user_id)  # authorization check
        return await self._repo.list_documents(brain_id)

    async def add_document(
        self, brain_id: uuid.UUID, document_id: uuid.UUID, user_id: uuid.UUID
    ) -> None:
        """Attach a document to a brain."""
        await self.get(brain_id, user_id)
        doc = await self._doc_repo.get_by_id(document_id)
        if not doc:
            raise AuraException(detail="Document not found.", code="DOCUMENT_NOT_FOUND")
        await self._repo.add_document(brain_id, document_id)

    async def remove_document(
        self, brain_id: uuid.UUID, document_id: uuid.UUID, user_id: uuid.UUID
    ) -> None:
        """Detach a document from a brain."""
        await self.get(brain_id, user_id)
        await self._repo.remove_document(brain_id, document_id)
