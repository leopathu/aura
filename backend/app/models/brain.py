"""ORM models for Brain and BrainDocument association."""

import uuid

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDMixin


class Brain(UUIDMixin, TimestampMixin, Base):
    """A named collection of documents for scoped RAG queries."""

    __tablename__ = "brains"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    user: Mapped["User"] = relationship("User", back_populates="brains")  # noqa: F821
    brain_documents: Mapped[list["BrainDocument"]] = relationship(
        "BrainDocument", back_populates="brain", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Brain id={self.id} name={self.name!r}>"


class BrainDocument(Base):
    """Association table linking Brains to Documents."""

    __tablename__ = "brain_documents"
    __table_args__ = (UniqueConstraint("brain_id", "document_id", name="uq_brain_document"),)

    brain_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("brains.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )

    brain: Mapped["Brain"] = relationship("Brain", back_populates="brain_documents")
    document: Mapped["Document"] = relationship("Document")  # noqa: F821

    def __repr__(self) -> str:
        return f"<BrainDocument brain_id={self.brain_id} document_id={self.document_id}>"
