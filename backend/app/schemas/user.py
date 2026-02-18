"""
User Schemas
Pydantic models for user data validation
"""

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)


class UserCreate(UserBase):
    """Schema for creating a new user"""
    password: str = Field(..., min_length=8, max_length=100)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "full_name": "John Doe",
                "password": "securepassword123"
            }
        }
    )


class UserUpdate(BaseModel):
    """Schema for updating user information"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    password: Optional[str] = Field(None, min_length=8, max_length=100)
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "full_name": "John Smith",
                "email": "newemail@example.com"
            }
        }
    )


class UserResponse(UserBase):
    """Schema for user response (without sensitive data)"""
    id: UUID
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
                "email": "user@example.com",
                "full_name": "John Doe",
                "is_active": True,
                "is_verified": True,
                "created_at": "2026-02-18T10:00:00Z",
                "updated_at": "2026-02-18T10:00:00Z"
            }
        }
    )


class UserInDB(UserBase):
    """Schema for user in database (includes hashed password)"""
    id: UUID
    hashed_password: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
