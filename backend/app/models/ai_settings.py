"""AI Settings ORM model — per-user LLM, embedding, and RAG pipeline configuration."""

import uuid

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy import DateTime

from app.db.base import Base


class AISettings(Base):
    """Stores per-user AI model configuration (one row per user, upserted)."""

    __tablename__ = "ai_settings"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid()
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # LLM configuration
    llm_provider: Mapped[str] = mapped_column(String(50), nullable=False, default="openai")
    llm_model: Mapped[str] = mapped_column(String(100), nullable=False, default="gpt-4o")
    llm_api_key: Mapped[str] = mapped_column(Text, nullable=False, default="")
    llm_base_url: Mapped[str] = mapped_column(
        Text, nullable=False, default="http://localhost:11434"
    )
    temperature: Mapped[float] = mapped_column(Float, nullable=False, default=0.2)

    # Embedding configuration
    embedding_provider: Mapped[str] = mapped_column(String(50), nullable=False, default="openai")
    embedding_model: Mapped[str] = mapped_column(
        String(100), nullable=False, default="text-embedding-3-small"
    )
    embedding_api_key: Mapped[str] = mapped_column(Text, nullable=False, default="")
    embedding_base_url: Mapped[str] = mapped_column(
        Text, nullable=False, default="http://localhost:11434"
    )

    # RAG pipeline
    chunk_size: Mapped[int] = mapped_column(Integer, nullable=False, default=512)
    chunk_overlap: Mapped[int] = mapped_column(Integer, nullable=False, default=64)
    retrieval_top_k: Mapped[int] = mapped_column(Integer, nullable=False, default=5)

    # Timestamps
    created_at: Mapped[str] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[str] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped["User"] = relationship("User", back_populates="ai_settings")  # type: ignore[name-defined]
