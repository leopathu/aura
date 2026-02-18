"""
Authentication Schemas
Pydantic models for authentication endpoints
"""

from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from uuid import UUID


class LoginRequest(BaseModel):
    """Schema for login request"""
    email: EmailStr
    password: str = Field(..., min_length=1)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "securepassword123"
            }
        }
    )


class LoginResponse(BaseModel):
    """Schema for login response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: UUID
    email: str
    full_name: str
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "user_id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
                "email": "user@example.com",
                "full_name": "John Doe"
            }
        }
    )


class RegisterRequest(BaseModel):
    """Schema for registration request"""
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    full_name: str = Field(..., min_length=1, max_length=255)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "newuser@example.com",
                "password": "securepassword123",
                "full_name": "Jane Doe"
            }
        }
    )


class RegisterResponse(BaseModel):
    """Schema for registration response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user_id: UUID
    email: str
    full_name: str
    message: str = "Registration successful. Please verify your email."
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "user_id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
                "email": "newuser@example.com",
                "full_name": "Jane Doe",
                "message": "Registration successful. Please verify your email."
            }
        }
    )


class TokenRefreshRequest(BaseModel):
    """Schema for token refresh request"""
    refresh_token: str
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
            }
        }
    )


class TokenRefreshResponse(BaseModel):
    """Schema for token refresh response"""
    access_token: str
    token_type: str = "bearer"
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer"
            }
        }
    )


class PasswordChangeRequest(BaseModel):
    """Schema for password change request"""
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8, max_length=100)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "current_password": "oldpassword123",
                "new_password": "newsecurepassword456"
            }
        }
    )


class PasswordResetRequest(BaseModel):
    """Schema for password reset request"""
    email: EmailStr
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com"
            }
        }
    )


class PasswordResetConfirm(BaseModel):
    """Schema for password reset confirmation"""
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "token": "reset-token-here",
                "new_password": "newsecurepassword456"
            }
        }
    )


class MessageResponse(BaseModel):
    """Generic message response"""
    message: str
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Operation successful"
            }
        }
    )
