"""ORM model for document chunks and their embeddings."""

import uuid

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import settings
from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDMixin


class DocumentChunk(UUIDMixin, TimestampMixin, Base):
    """A chunk of a document with its vector embedding."""

    __tablename__ = "document_chunks"

    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(
        Vector(settings.vector_dimensions), nullable=False
    )

    document: Mapped["Document"] = relationship(  # noqa: F821
        "Document", back_populates="chunks"
    )

    def __repr__(self) -> str:
        return f"<DocumentChunk id={self.id} document_id={self.document_id} index={self.chunk_index}>"
