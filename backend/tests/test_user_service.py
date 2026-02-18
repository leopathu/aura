"""
Test User Service
Unit tests for user management
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from app.services.user_service import (
    create_user,
    get_user_by_id,
    get_user_by_email,
    update_user,
    delete_user,
    verify_user_password,
    activate_user,
    deactivate_user,
    verify_user_email
)
from app.schemas.user import UserCreate, UserUpdate
from app.core.security import verify_password


@pytest.mark.asyncio
async def test_create_user(db_session: AsyncSession):
    """Test user creation"""
    user_data = UserCreate(
        email="test@example.com",
        full_name="Test User",
        password="testpassword123"
    )
    
    user = await create_user(db_session, user_data)
    
    assert user.email == "test@example.com"
    assert user.full_name == "Test User"
    assert user.is_active is True
    assert user.is_verified is False
    assert verify_password("testpassword123", user.hashed_password)


@pytest.mark.asyncio
async def test_get_user_by_id(db_session: AsyncSession):
    """Test retrieving user by ID"""
    # Create user
    user_data = UserCreate(
        email="test2@example.com",
        full_name="Test User 2",
        password="testpassword123"
    )
    created_user = await create_user(db_session, user_data)
    
    # Retrieve user
    user = await get_user_by_id(db_session, created_user.id)
    
    assert user is not None
    assert user.id == created_user.id
    assert user.email == "test2@example.com"


@pytest.mark.asyncio
async def test_get_user_by_id_not_found(db_session: AsyncSession):
    """Test retrieving non-existent user by ID"""
    user = await get_user_by_id(db_session, uuid4())
    assert user is None


@pytest.mark.asyncio
async def test_get_user_by_email(db_session: AsyncSession):
    """Test retrieving user by email"""
    # Create user
    user_data = UserCreate(
        email="test3@example.com",
        full_name="Test User 3",
        password="testpassword123"
    )
    created_user = await create_user(db_session, user_data)
    
    # Retrieve user (case insensitive)
    user = await get_user_by_email(db_session, "TEST3@EXAMPLE.COM")
    
    assert user is not None
    assert user.id == created_user.id
    assert user.email == "test3@example.com"


@pytest.mark.asyncio
async def test_update_user(db_session: AsyncSession):
    """Test updating user information"""
    # Create user
    user_data = UserCreate(
        email="test4@example.com",
        full_name="Test User 4",
        password="testpassword123"
    )
    created_user = await create_user(db_session, user_data)
    
    # Update user
    update_data = UserUpdate(
        full_name="Updated Name",
        email="updated@example.com"
    )
    updated_user = await update_user(db_session, created_user.id, update_data)
    
    assert updated_user is not None
    assert updated_user.full_name == "Updated Name"
    assert updated_user.email == "updated@example.com"


@pytest.mark.asyncio
async def test_delete_user_soft(db_session: AsyncSession):
    """Test soft deleting user"""
    # Create user
    user_data = UserCreate(
        email="test5@example.com",
        full_name="Test User 5",
        password="testpassword123"
    )
    created_user = await create_user(db_session, user_data)
    
    # Soft delete
    result = await delete_user(db_session, created_user.id, soft_delete=True)
    assert result is True
    
    # User should still exist but be inactive
    user = await get_user_by_id(db_session, created_user.id)
    assert user is not None
    assert user.is_active is False


@pytest.mark.asyncio
async def test_verify_user_password(db_session: AsyncSession):
    """Test password verification"""
    # Create user
    user_data = UserCreate(
        email="test6@example.com",
        full_name="Test User 6",
        password="correctpassword"
    )
    await create_user(db_session, user_data)
    
    # Verify correct password
    user = await verify_user_password(db_session, "test6@example.com", "correctpassword")
    assert user is not None
    
    # Verify incorrect password
    user = await verify_user_password(db_session, "test6@example.com", "wrongpassword")
    assert user is None


@pytest.mark.asyncio
async def test_activate_deactivate_user(db_session: AsyncSession):
    """Test user activation/deactivation"""
    # Create user
    user_data = UserCreate(
        email="test7@example.com",
        full_name="Test User 7",
        password="testpassword123"
    )
    created_user = await create_user(db_session, user_data)
    
    # Deactivate
    user = await deactivate_user(db_session, created_user.id)
    assert user.is_active is False
    
    # Activate
    user = await activate_user(db_session, created_user.id)
    assert user.is_active is True


@pytest.mark.asyncio
async def test_verify_user_email(db_session: AsyncSession):
    """Test email verification"""
    # Create user
    user_data = UserCreate(
        email="test8@example.com",
        full_name="Test User 8",
        password="testpassword123"
    )
    created_user = await create_user(db_session, user_data)
    assert created_user.is_verified is False
    
    # Verify email
    user = await verify_user_email(db_session, created_user.id)
    assert user.is_verified is True
