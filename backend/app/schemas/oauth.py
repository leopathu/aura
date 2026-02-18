"""
OAuth Schemas
Pydantic models for OAuth validation
"""

from pydantic import BaseModel, HttpUrl
from datetime import datetime
from uuid import UUID
from typing import Optional


class OAuthInitiateResponse(BaseModel):
    """Schema for OAuth initiation response"""
    authorization_url: str
    state: str


class OAuthCallbackRequest(BaseModel):
    """Schema for OAuth callback"""
    code: str
    state: str


class OAuthTokenResponse(BaseModel):
    """Schema for OAuth token response"""
    id: UUID
    provider: str
    scope: Optional[str]
    expires_at: Optional[datetime]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class OAuthConnectionStatus(BaseModel):
    """Schema for OAuth connection status"""
    provider: str
    is_connected: bool
    expires_at: Optional[datetime]
    scope: Optional[str]
