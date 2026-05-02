"""Add embed_status and embed_error columns to documents.

Revision ID: 0007
Revises: 0006
Create Date: 2026-05-03
"""

import sqlalchemy as sa
from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column("embed_status", sa.Text(), nullable=False, server_default="pending"),
    )
    op.add_column(
        "documents",
        sa.Column("embed_error", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("documents", "embed_error")
    op.drop_column("documents", "embed_status")
