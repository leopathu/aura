"""Create brains and brain_documents tables.

Revision ID: 0004
Revises: 0003
Create Date: 2026-05-02
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "brains",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_brains_user_id", "brains", ["user_id"])

    op.create_table(
        "brain_documents",
        sa.Column("brain_id", UUID(as_uuid=True), sa.ForeignKey("brains.id", ondelete="CASCADE"), primary_key=True, nullable=False),
        sa.Column("document_id", UUID(as_uuid=True), sa.ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True, nullable=False),
        sa.UniqueConstraint("brain_id", "document_id", name="uq_brain_document"),
    )


def downgrade() -> None:
    op.drop_table("brain_documents")
    op.drop_index("ix_brains_user_id", table_name="brains")
    op.drop_table("brains")
