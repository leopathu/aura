"""Pydantic schemas for authentication and user resources."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    """Schema for user registration."""

    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)


class UserLogin(BaseModel):
    """Schema for user login."""

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """Public-facing user schema (no password)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str
    is_active: bool
    created_at: datetime


class Token(BaseModel):
    """JWT token response."""

    access_token: str
    token_type: str = "bearer"


class TokenPayload(BaseModel):
    """Decoded JWT payload."""

    sub: str  # user id as string
