"""
Organization Pydantic Schemas
Request and response schemas for organization endpoints
"""

from pydantic import BaseModel, Field, validator
from datetime import datetime
from uuid import UUID
from typing import Optional
import re


# Organization Schemas
class OrganizationCreate(BaseModel):
    """Schema for creating a new organization"""
    name: str = Field(..., min_length=2, max_length=255)
    
    @validator('name')
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError('Organization name cannot be empty')
        return v.strip()


class OrganizationUpdate(BaseModel):
    """Schema for updating an organization"""
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    
    @validator('name')
    def validate_name(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Organization name cannot be empty')
        return v.strip() if v else None


class OrganizationResponse(BaseModel):
    """Schema for organization response"""
    id: UUID
    name: str
    slug: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Membership Schemas
class MembershipResponse(BaseModel):
    """Schema for membership response"""
    id: UUID
    user_id: UUID
    org_id: UUID
    role: str
    joined_at: datetime
    
    class Config:
        from_attributes = True


class MemberResponse(BaseModel):
    """Schema for member with user details"""
    id: UUID
    user_id: UUID
    email: str
    full_name: str
    role: str
    joined_at: datetime
    
    class Config:
        from_attributes = True


class MemberInvite(BaseModel):
    """Schema for inviting a member"""
    email: str = Field(..., pattern=r'^[^\s@]+@[^\s@]+\.[^\s@]+$')
    role: str = Field(default='member')
    
    @validator('role')
    def validate_role(cls, v):
        allowed_roles = ['owner', 'admin', 'member']
        if v.lower() not in allowed_roles:
            raise ValueError(f'Role must be one of: {", ".join(allowed_roles)}')
        return v.lower()


class OrganizationWithRole(OrganizationResponse):
    """Schema for organization with user's role"""
    role: str
    
    class Config:
        from_attributes = True
