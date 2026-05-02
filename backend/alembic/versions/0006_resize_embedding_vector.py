"""Resize embedding vector column from 1536 to 1024 dimensions.

Revision ID: 0006
Revises: 0005
Create Date: 2026-05-03
"""

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop existing data and recreate column with new dimension.
    # Truncate chunks first since old embeddings are incompatible.
    op.execute("TRUNCATE TABLE document_chunks")
    op.execute("ALTER TABLE document_chunks DROP COLUMN embedding")
    op.execute("ALTER TABLE document_chunks ADD COLUMN embedding vector(1024) NOT NULL DEFAULT array_fill(0, ARRAY[1024])::vector")
    op.execute("ALTER TABLE document_chunks ALTER COLUMN embedding DROP DEFAULT")


def downgrade() -> None:
    op.execute("TRUNCATE TABLE document_chunks")
    op.execute("ALTER TABLE document_chunks DROP COLUMN embedding")
    op.execute("ALTER TABLE document_chunks ADD COLUMN embedding vector(1536) NOT NULL DEFAULT array_fill(0, ARRAY[1536])::vector")
    op.execute("ALTER TABLE document_chunks ALTER COLUMN embedding DROP DEFAULT")
