"""
User Service
Business logic for user management
"""

from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import get_password_hash, verify_password


async def create_user(db: AsyncSession, user_data: UserCreate) -> User:
    """
    Create a new user
    
    Args:
        db: Database session
        user_data: User creation data
        
    Returns:
        Created user
    """
    hashed_password = get_password_hash(user_data.password)
    
    user = User(
        email=user_data.email.lower(),
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        is_active=True,
        is_verified=False
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return user


async def get_user_by_id(db: AsyncSession, user_id: UUID) -> Optional[User]:
    """
    Get user by ID
    
    Args:
        db: Database session
        user_id: User UUID
        
    Returns:
        User or None if not found
    """
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """
    Get user by email
    
    Args:
        db: Database session
        email: User email
        
    Returns:
        User or None if not found
    """
    result = await db.execute(
        select(User).where(User.email == email.lower())
    )
    return result.scalar_one_or_none()


async def update_user(db: AsyncSession, user_id: UUID, user_data: UserUpdate) -> Optional[User]:
    """
    Update user information
    
    Args:
        db: Database session
        user_id: User UUID
        user_data: Update data
        
    Returns:
        Updated user or None if not found
    """
    user = await get_user_by_id(db, user_id)
    if not user:
        return None
    
    # Update only provided fields
    update_data = user_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        if field == "password" and value:
            # Hash password if being updated
            setattr(user, "hashed_password", get_password_hash(value))
        elif field == "email" and value:
            # Lowercase email
            setattr(user, field, value.lower())
        elif hasattr(user, field):
            setattr(user, field, value)
    
    await db.commit()
    await db.refresh(user)
    
    return user


async def delete_user(db: AsyncSession, user_id: UUID, soft_delete: bool = True) -> bool:
    """
    Delete user (soft delete by default)
    
    Args:
        db: Database session
        user_id: User UUID
        soft_delete: If True, just mark as inactive. If False, actually delete.
        
    Returns:
        True if deleted, False if not found
    """
    user = await get_user_by_id(db, user_id)
    if not user:
        return False
    
    if soft_delete:
        # Soft delete - just mark as inactive
        user.is_active = False
        await db.commit()
    else:
        # Hard delete - actually remove from database
        await db.delete(user)
        await db.commit()
    
    return True


async def verify_user_password(db: AsyncSession, email: str, password: str) -> Optional[User]:
    """
    Verify user credentials
    
    Args:
        db: Database session
        email: User email
        password: Plain text password
        
    Returns:
        User if credentials are valid, None otherwise
    """
    user = await get_user_by_email(db, email)
    if not user:
        return None
    
    if not user.is_active:
        return None
    
    if not verify_password(password, user.hashed_password):
        return None
    
    return user


async def activate_user(db: AsyncSession, user_id: UUID) -> Optional[User]:
    """
    Activate a user account
    
    Args:
        db: Database session
        user_id: User UUID
        
    Returns:
        Updated user or None if not found
    """
    user = await get_user_by_id(db, user_id)
    if not user:
        return None
    
    user.is_active = True
    await db.commit()
    await db.refresh(user)
    
    return user


async def deactivate_user(db: AsyncSession, user_id: UUID) -> Optional[User]:
    """
    Deactivate a user account
    
    Args:
        db: Database session
        user_id: User UUID
        
    Returns:
        Updated user or None if not found
    """
    user = await get_user_by_id(db, user_id)
    if not user:
        return None
    
    user.is_active = False
    await db.commit()
    await db.refresh(user)
    
    return user


async def verify_user_email(db: AsyncSession, user_id: UUID) -> Optional[User]:
    """
    Mark user email as verified
    
    Args:
        db: Database session
        user_id: User UUID
        
    Returns:
        Updated user or None if not found
    """
    user = await get_user_by_id(db, user_id)
    if not user:
        return None
    
    user.is_verified = True
    await db.commit()
    await db.refresh(user)
    
    return user
