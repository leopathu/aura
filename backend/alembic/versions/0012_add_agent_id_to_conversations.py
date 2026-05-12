"""Migration: add agent_id to conversations; make brain_id nullable.

Conversations can now belong to either a Brain or an Agent.  Exactly one of
``brain_id`` or ``agent_id`` should be set on any given row — this is enforced
at the application layer.

Revision ID: 0012
Revises: 0011
Create Date: 2026-05-12
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Make brain_id nullable so Agent conversations don't need one.
    op.alter_column("conversations", "brain_id", nullable=True)

    # Add nullable agent_id FK.
    op.add_column(
        "conversations",
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_conversations_agent_id",
        "conversations",
        "agents",
        ["agent_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_conversations_agent_id", "conversations", ["agent_id"])


def downgrade() -> None:
    op.drop_index("ix_conversations_agent_id", table_name="conversations")
    op.drop_constraint("fk_conversations_agent_id", "conversations", type_="foreignkey")
    op.drop_column("conversations", "agent_id")
    op.alter_column("conversations", "brain_id", nullable=False)
