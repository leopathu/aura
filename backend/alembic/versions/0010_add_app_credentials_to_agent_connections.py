"""Migration: add app_credentials_enc column to agent_connections.

Stores each connection's own OAuth app credentials (client_id + client_secret)
encrypted at rest so users can supply their own OAuth applications.

Revision ID: 0010
Revises: 0009
Create Date: 2026-05-12
"""

import sqlalchemy as sa
from alembic import op

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "agent_connections",
        sa.Column("app_credentials_enc", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("agent_connections", "app_credentials_enc")
