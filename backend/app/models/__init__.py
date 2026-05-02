"""Models package — import all models here for Alembic auto-detection."""

from app.models.ai_settings import AISettings
from app.models.brain import Brain, BrainDocument
from app.models.chunk import DocumentChunk
from app.models.conversation import ChatMessage, Conversation
from app.models.document import Document
from app.models.user import User

__all__ = ["AISettings", "Brain", "BrainDocument", "ChatMessage", "Conversation", "Document", "DocumentChunk", "User"]
