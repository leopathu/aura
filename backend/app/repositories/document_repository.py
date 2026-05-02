"""Repository for Document database operations."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.document import Document
from app.schemas.document import DocumentCreate, DocumentUpdate


class DocumentRepository:
    """Handles all Document database queries."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, payload: DocumentCreate) -> Document:
        """Persist a new document and return it."""
        document = Document(**payload.model_dump())
        self.db.add(document)
        await self.db.flush()
        await self.db.refresh(document)
        return document

    async def get_by_id(self, document_id: uuid.UUID) -> Document | None:
        """Fetch a single document by its UUID."""
        result = await self.db.execute(select(Document).where(Document.id == document_id))
        return result.scalar_one_or_none()

    async def list_all(self, limit: int = 50, offset: int = 0) -> list[Document]:
        """Return a paginated list of documents."""
        result = await self.db.execute(
            select(Document).order_by(Document.created_at.desc()).limit(limit).offset(offset)
        )
        return list(result.scalars().all())

    async def update(self, document: Document, payload: DocumentUpdate) -> Document:
        """Apply partial updates to a document."""
        update_data = payload.model_dump(exclude_none=True)
        for field, value in update_data.items():
            setattr(document, field, value)
        await self.db.flush()
        await self.db.refresh(document)
        return document

    async def set_embed_status(
        self, document_id: uuid.UUID, status: str, error: str | None = None
    ) -> None:
        """Update the embed_status (and optional error) for a document."""
        doc = await self.get_by_id(document_id)
        if doc:
            doc.embed_status = status
            doc.embed_error = error
            await self.db.flush()

    async def delete(self, document: Document) -> None:
        """Delete a document and cascade to its chunks."""
        await self.db.delete(document)
        await self.db.flush()
