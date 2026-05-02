"""Create ai_settings table.

Revision ID: 0005
Revises: 0004
Create Date: 2026-05-02
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ai_settings",
        sa.Column(
            "id",
            UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        sa.Column(
            "user_id",
            UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        # LLM
        sa.Column("llm_provider", sa.String(50), nullable=False, server_default="openai"),
        sa.Column("llm_model", sa.String(100), nullable=False, server_default="gpt-4o"),
        sa.Column("llm_api_key", sa.Text, nullable=False, server_default=""),
        sa.Column(
            "llm_base_url", sa.Text, nullable=False, server_default="http://localhost:11434"
        ),
        sa.Column("temperature", sa.Float, nullable=False, server_default="0.2"),
        # Embeddings
        sa.Column(
            "embedding_provider", sa.String(50), nullable=False, server_default="openai"
        ),
        sa.Column(
            "embedding_model",
            sa.String(100),
            nullable=False,
            server_default="text-embedding-3-small",
        ),
        sa.Column("embedding_api_key", sa.Text, nullable=False, server_default=""),
        sa.Column(
            "embedding_base_url",
            sa.Text,
            nullable=False,
            server_default="http://localhost:11434",
        ),
        # RAG pipeline
        sa.Column("chunk_size", sa.Integer, nullable=False, server_default="512"),
        sa.Column("chunk_overlap", sa.Integer, nullable=False, server_default="64"),
        sa.Column("retrieval_top_k", sa.Integer, nullable=False, server_default="5"),
        # Timestamps
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
    )
    op.create_index("ix_ai_settings_user_id", "ai_settings", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_ai_settings_user_id", table_name="ai_settings")
    op.drop_table("ai_settings")
