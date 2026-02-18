"""
Test Authentication Dependencies
Unit tests for FastAPI authentication dependencies
"""

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from uuid import uuid4

from app.core.dependencies import get_current_user, get_optional_user
from app.core.jwt import create_token_pair
from app.services.user_service import create_user
from app.schemas.user import UserCreate


@pytest.mark.asyncio
async def test_get_current_user_valid_token(db_session):
    """Test getting current user with valid token"""
    # Create user
    user_data = UserCreate(
        email="test@example.com",
        full_name="Test User",
        password="testpassword123"
    )
    user = await create_user(db_session, user_data)
    
    # Create token
    tokens = create_token_pair(user.id)
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=tokens["access_token"]
    )
    
    # Get current user
    current_user = await get_current_user(credentials, db_session)
    
    assert current_user is not None
    assert current_user.id == user.id
    assert current_user.email == user.email


@pytest.mark.asyncio
async def test_get_current_user_invalid_token(db_session):
    """Test getting current user with invalid token"""
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="invalid.token.here"
    )
    
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials, db_session)
    
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_nonexistent_user(db_session):
    """Test getting current user with token for non-existent user"""
    # Create token for non-existent user
    tokens = create_token_pair(uuid4())
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=tokens["access_token"]
    )
    
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials, db_session)
    
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user_inactive_user(db_session):
    """Test getting current user when user is inactive"""
    # Create and deactivate user
    user_data = UserCreate(
        email="inactive@example.com",
        full_name="Inactive User",
        password="testpassword123"
    )
    user = await create_user(db_session, user_data)
    user.is_active = False
    await db_session.commit()
    
    # Create token
    tokens = create_token_pair(user.id)
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=tokens["access_token"]
    )
    
    with pytest.raises(HTTPException) as exc_info:
        await get_current_user(credentials, db_session)
    
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_get_optional_user_with_token(db_session):
    """Test getting optional user with valid token"""
    # Create user
    user_data = UserCreate(
        email="optional@example.com",
        full_name="Optional User",
        password="testpassword123"
    )
    user = await create_user(db_session, user_data)
    
    # Create token
    tokens = create_token_pair(user.id)
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials=tokens["access_token"]
    )
    
    # Get optional user
    current_user = await get_optional_user(credentials, db_session)
    
    assert current_user is not None
    assert current_user.id == user.id


@pytest.mark.asyncio
async def test_get_optional_user_without_token(db_session):
    """Test getting optional user without token"""
    current_user = await get_optional_user(None, db_session)
    assert current_user is None


@pytest.mark.asyncio
async def test_get_optional_user_invalid_token(db_session):
    """Test getting optional user with invalid token"""
    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="invalid.token"
    )
    
    current_user = await get_optional_user(credentials, db_session)
    assert current_user is None
