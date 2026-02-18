"""
OAuth Token Model
SQLAlchemy model for storing encrypted OAuth tokens
"""

from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from app.db.session import Base


class OAuthToken(Base):
    """OAuth token storage with encryption"""
    
    __tablename__ = "oauth_tokens"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    org_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = Column(String(50), nullable=False)  # google, microsoft, etc.
    encrypted_access_token = Column(Text, nullable=False)
    encrypted_refresh_token = Column(Text)
    token_type = Column(String(50), default="Bearer")
    expires_at = Column(DateTime(timezone=True))
    scope = Column(Text)  # Space-separated scopes
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<OAuthToken {self.provider} for user {self.user_id}>"
