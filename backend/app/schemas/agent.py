"""
Agent Pydantic Schemas
Request and response schemas for agent endpoints
"""

from pydantic import BaseModel, Field, validator
from datetime import datetime
from uuid import UUID
from typing import Optional, Dict, Any


class AgentCreate(BaseModel):
    """Schema for creating a new agent"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    config: Dict[str, Any] = Field(default_factory=dict)
    
    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Agent name cannot be empty')
        return v.strip()


class AgentUpdate(BaseModel):
    """Schema for updating an agent"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Agent name cannot be empty')
        return v.strip() if v else None


class AgentResponse(BaseModel):
    """Schema for agent response"""
    id: UUID
    org_id: UUID
    name: str
    description: Optional[str]
    system_prompt: Optional[str]
    config: Dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
