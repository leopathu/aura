"""
Chat Pydantic Schemas
Request and response schemas for chat endpoints
"""

from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID
from typing import Optional, List, Dict, Any


class ChatMessage(BaseModel):
    """Schema for a chat message"""
    role: str = Field(..., regex='^(user|assistant|system)$')
    content: str = Field(..., min_length=1)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ChatRequest(BaseModel):
    """Schema for chat request"""
    agent_id: UUID
    message: str = Field(..., min_length=1)
    conversation_id: Optional[UUID] = None
    stream: bool = Field(default=False)


class ChatResponse(BaseModel):
    """Schema for chat response"""
    conversation_id: UUID
    message: ChatMessage
    created_at: datetime


class ConversationResponse(BaseModel):
    """Schema for conversation response"""
    id: UUID
    org_id: UUID
    agent_id: UUID
    user_id: UUID
    title: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    """Schema for message response"""
    id: UUID
    conversation_id: UUID
    role: str
    content: str
    metadata: Dict[str, Any]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ConversationWithMessages(ConversationResponse):
    """Schema for conversation with messages"""
    messages: List[MessageResponse]
