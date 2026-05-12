"""Migration: create agent_sync_logs table.

Records a full audit trail for every sync run: timing, item counts, and any
error that occurred.  Used by the GET /sync/history endpoint and the frontend
Connections detail view.

Revision ID: 0011
Revises: 0010
Create Date: 2026-05-12
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_sync_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("connection_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("items_total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("items_new", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("items_changed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("items_unchanged", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("items_deleted", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("items_failed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error", sa.Text(), nullable=True),
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
            ["connection_id"], ["agent_connections.id"], ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_agent_sync_logs_connection_id", "agent_sync_logs", ["connection_id"])
    op.create_index("ix_agent_sync_logs_started_at", "agent_sync_logs", ["started_at"])


def downgrade() -> None:
    op.drop_index("ix_agent_sync_logs_started_at", table_name="agent_sync_logs")
    op.drop_index("ix_agent_sync_logs_connection_id", table_name="agent_sync_logs")
    op.drop_table("agent_sync_logs")
