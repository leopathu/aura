"""Migration: create agents, agent_connections, agent_documents, agent_chunks tables.

Revision ID: 0009
Revises: 0008
Create Date: 2026-05-12
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # agents
    # ------------------------------------------------------------------
    op.create_table(
        "agents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_agents_user_id", "agents", ["user_id"])

    # ------------------------------------------------------------------
    # agent_connections
    # ------------------------------------------------------------------
    op.create_table(
        "agent_connections",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("app_type", sa.Text(), nullable=False),
        sa.Column("display_name", sa.Text(), nullable=False),
        sa.Column("credentials_enc", sa.Text(), nullable=True),
        sa.Column("config_json", sa.Text(), nullable=True),
        sa.Column("sync_status", sa.Text(), nullable=False, server_default="idle"),
        sa.Column("sync_error", sa.Text(), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sync_interval_minutes", sa.Integer(), nullable=False, server_default="60"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_agent_connections_agent_id", "agent_connections", ["agent_id"])
    op.create_index("ix_agent_connections_app_type", "agent_connections", ["app_type"])

    # ------------------------------------------------------------------
    # agent_documents
    # ------------------------------------------------------------------
    op.create_table(
        "agent_documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("connection_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("external_id", sa.Text(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("content_hash", sa.Text(), nullable=False),
        sa.Column("embed_status", sa.Text(), nullable=False, server_default="pending"),
        sa.Column("embed_error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["connection_id"], ["agent_connections.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_agent_documents_agent_id", "agent_documents", ["agent_id"])
    op.create_index("ix_agent_documents_connection_id", "agent_documents", ["connection_id"])
    # Unique per (connection, external item) — enables upsert / change detection
    op.create_index(
        "uq_agent_doc_connection_external",
        "agent_documents",
        ["connection_id", "external_id"],
        unique=True,
    )

    # ------------------------------------------------------------------
    # agent_chunks
    # ------------------------------------------------------------------
    op.create_table(
        "agent_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_document_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        # Vector dimension intentionally left as text type here; pgvector column
        # is defined in the ORM model using Vector(settings.vector_dimensions).
        # We use raw SQL for the column definition to pass the dimension at runtime.
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["agent_document_id"], ["agent_documents.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # Add the vector column as nullable first (pgvector rejects a 1-element
    # default when the dimension is > 1), then make it NOT NULL after the
    # column exists with no rows yet.
    op.execute("ALTER TABLE agent_chunks ADD COLUMN embedding vector(1024)")
    op.execute("ALTER TABLE agent_chunks ALTER COLUMN embedding SET NOT NULL")
    op.create_index("ix_agent_chunks_agent_document_id", "agent_chunks", ["agent_document_id"])


def downgrade() -> None:
    op.drop_table("agent_chunks")
    op.drop_table("agent_documents")
    op.drop_table("agent_connections")
    op.drop_table("agents")
