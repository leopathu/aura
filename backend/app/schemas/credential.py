"""
Credential Schemas
Pydantic models for credential validation
"""

from pydantic import BaseModel, Field, validator
from datetime import datetime
from uuid import UUID
from typing import Optional


class CredentialCreate(BaseModel):
    """Schema for creating a credential"""
    credential_type: str = Field(..., min_length=1, max_length=50)
    api_key: str = Field(..., min_length=1)
    label: Optional[str] = Field(None, max_length=255)
    
    @validator('credential_type')
    def validate_credential_type(cls, v):
        valid_types = ['openai', 'anthropic', 'google_gemini', 'cohere', 'huggingface', 'jira']
        if v not in valid_types:
            raise ValueError(f'Invalid credential type. Must be one of: {", ".join(valid_types)}')
        return v


class CredentialUpdate(BaseModel):
    """Schema for updating a credential (label only)"""
    label: str = Field(..., min_length=1, max_length=255)


class CredentialResponse(BaseModel):
    """Schema for credential response (never expose API key)"""
    id: UUID
    org_id: UUID
    credential_type: str
    label: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    # Masked API key (show only last 4 characters)
    masked_key: Optional[str] = None
    
    class Config:
        from_attributes = True


class CredentialTestRequest(BaseModel):
    """Schema for testing a credential"""
    credential_id: UUID


class CredentialTestResponse(BaseModel):
    """Schema for credential test result"""
    success: bool
    message: str
    provider: Optional[str] = None
