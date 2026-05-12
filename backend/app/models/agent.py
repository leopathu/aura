"""ORM models for Agent, AgentConnection, AgentDocument, AgentChunk, and AgentSyncLog."""

import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import DateTime, ForeignKey, Index, Integer, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.config import settings
from app.db.base import Base
from app.db.mixins import TimestampMixin, UUIDMixin


class Agent(UUIDMixin, TimestampMixin, Base):
    """A named agent that syncs data from external app connections."""

    __tablename__ = "agents"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    connections: Mapped[list["AgentConnection"]] = relationship(
        "AgentConnection", back_populates="agent", cascade="all, delete-orphan"
    )
    documents: Mapped[list["AgentDocument"]] = relationship(
        "AgentDocument", back_populates="agent", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Agent id={self.id} name={self.name!r}>"


class AgentConnection(UUIDMixin, TimestampMixin, Base):
    """An OAuth-connected external app belonging to an Agent."""

    __tablename__ = "agent_connections"
    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    app_type: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    # Fernet-encrypted JSON blob holding OAuth access/refresh tokens
    credentials_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Fernet-encrypted JSON blob holding the user's own OAuth app credentials
    # { "client_id": "...", "client_secret": "..." }
    app_credentials_enc: Mapped[str | None] = mapped_column(Text, nullable=True)
    # JSON blob for per-connection sync filters (folders, labels, projects…)
    config_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    sync_status: Mapped[str] = mapped_column(Text, nullable=False, default="idle")
    sync_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    sync_interval_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=60)

    agent: Mapped["Agent"] = relationship("Agent", back_populates="connections")
    agent_documents: Mapped[list["AgentDocument"]] = relationship(
        "AgentDocument", back_populates="connection", cascade="all, delete-orphan"
    )
    sync_logs: Mapped[list["AgentSyncLog"]] = relationship(
        "AgentSyncLog", back_populates="connection", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<AgentConnection id={self.id} app_type={self.app_type!r}>"


class AgentDocument(UUIDMixin, TimestampMixin, Base):
    """A document synced from an external app, ready for RAG."""

    __tablename__ = "agent_documents"
    __table_args__ = (
        UniqueConstraint("connection_id", "external_id", name="uq_agent_doc_connection_external"),
        Index("ix_agent_documents_agent_id", "agent_id"),
        Index("ix_agent_documents_connection_id", "connection_id"),
    )

    agent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
    )
    connection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_connections.id", ondelete="CASCADE"),
        nullable=False,
    )
    external_id: Mapped[str] = mapped_column(Text, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_json: Mapped[str | None] = mapped_column(Text, nullable=True)
    # SHA-256 of content — used to detect changes and skip re-embedding
    content_hash: Mapped[str] = mapped_column(Text, nullable=False)
    embed_status: Mapped[str] = mapped_column(Text, nullable=False, default="pending")
    embed_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    agent: Mapped["Agent"] = relationship("Agent", back_populates="documents")
    connection: Mapped["AgentConnection"] = relationship(
        "AgentConnection", back_populates="agent_documents"
    )
    chunks: Mapped[list["AgentChunk"]] = relationship(
        "AgentChunk", back_populates="document", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<AgentDocument id={self.id} title={self.title!r} external_id={self.external_id!r}>"


class AgentChunk(UUIDMixin, TimestampMixin, Base):
    """A chunk of an AgentDocument with its vector embedding."""

    __tablename__ = "agent_chunks"

    agent_document_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_documents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(
        Vector(settings.vector_dimensions), nullable=False
    )

    document: Mapped["AgentDocument"] = relationship("AgentDocument", back_populates="chunks")

    def __repr__(self) -> str:
        return (
            f"<AgentChunk id={self.id} document_id={self.agent_document_id}"
            f" index={self.chunk_index}>"
        )


class AgentSyncLog(UUIDMixin, TimestampMixin, Base):
    """Audit record for a single sync run of an AgentConnection."""

    __tablename__ = "agent_sync_logs"

    connection_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("agent_connections.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    items_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    items_new: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    items_changed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    items_unchanged: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    items_deleted: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    items_failed: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    connection: Mapped["AgentConnection"] = relationship(
        "AgentConnection", back_populates="sync_logs"
    )

    def __repr__(self) -> str:
        return (
            f"<AgentSyncLog id={self.id} connection_id={self.connection_id}"
            f" started_at={self.started_at}>"
        )
