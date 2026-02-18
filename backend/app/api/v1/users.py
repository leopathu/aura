"""
User Router
Handles user profile management and user-related operations
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID

from app.db.session import get_db
from app.schemas.user import UserResponse, UserUpdate
from app.schemas.auth import MessageResponse
from app.services.user_service import (
    get_user_by_id,
    update_user,
    delete_user
)
from app.core.dependencies import get_current_user
from app.models.user import User


router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user's profile
    
    - Returns authenticated user information
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_my_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update current user's profile
    
    - Updates user information
    - Cannot change email if already verified (security measure)
    """
    # Prevent email change if already verified (security)
    if user_data.email and current_user.is_verified and user_data.email != current_user.email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change email for verified accounts. Please contact support."
        )
    
    updated_user = await update_user(db, current_user.id, user_data)
    
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return updated_user


@router.delete("/me", response_model=MessageResponse)
async def delete_my_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete current user's account (soft delete)
    
    - Deactivates account
    - Data retained for audit purposes
    """
    success = await delete_user(db, current_user.id, soft_delete=True)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete account"
        )
    
    return MessageResponse(
        message="Account deleted successfully. You have been logged out."
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get user by ID
    
    - Returns user information
    - Requires authentication
    """
    user = await get_user_by_id(db, user_id)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user
