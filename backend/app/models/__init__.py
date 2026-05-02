"""Models package — import all models here for Alembic auto-detection."""

from app.models.chunk import DocumentChunk
from app.models.document import Document

__all__ = ["Document", "DocumentChunk"]
