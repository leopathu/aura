"""
Test Authentication Endpoints
Integration tests for auth API
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.services.user_service import get_user_by_email


@pytest.mark.asyncio
async def test_register_success(async_client: AsyncClient, db_session: AsyncSession):
    """Test successful user registration"""
    response = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "newuser@example.com",
            "full_name": "New User",
            "password": "securepassword123"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["email"] == "newuser@example.com"
    assert data["full_name"] == "New User"
    assert "user_id" in data
    
    # Verify user created in database
    user = await get_user_by_email(db_session, "newuser@example.com")
    assert user is not None
    assert user.email == "newuser@example.com"


@pytest.mark.asyncio
async def test_register_duplicate_email(async_client: AsyncClient, db_session: AsyncSession):
    """Test registration with duplicate email"""
    # First registration
    await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "duplicate@example.com",
            "full_name": "First User",
            "password": "password123"
        }
    )
    
    # Second registration with same email
    response = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "duplicate@example.com",
            "full_name": "Second User",
            "password": "password456"
        }
    )
    
    assert response.status_code == 400
    assert "already exists" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_register_invalid_email(async_client: AsyncClient):
    """Test registration with invalid email"""
    response = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "notanemail",
            "full_name": "Test User",
            "password": "password123"
        }
    )
    
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_register_short_password(async_client: AsyncClient):
    """Test registration with password too short"""
    response = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "full_name": "Test User",
            "password": "short"
        }
    )
    
    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_login_success(async_client: AsyncClient, db_session: AsyncSession):
    """Test successful login"""
    # Register user first
    await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "login@example.com",
            "full_name": "Login User",
            "password": "password123"
        }
    )
    
    # Login
    response = await async_client.post(
        "/api/v1/auth/login",
        json={
            "email": "login@example.com",
            "password": "password123"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["email"] == "login@example.com"


@pytest.mark.asyncio
async def test_login_wrong_password(async_client: AsyncClient):
    """Test login with wrong password"""
    # Register user
    await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "wrongpass@example.com",
            "full_name": "Test User",
            "password": "correctpassword"
        }
    )
    
    # Login with wrong password
    response = await async_client.post(
        "/api/v1/auth/login",
        json={
            "email": "wrongpass@example.com",
            "password": "wrongpassword"
        }
    )
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(async_client: AsyncClient):
    """Test login with non-existent user"""
    response = await async_client.post(
        "/api/v1/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "password123"
        }
    )
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token(async_client: AsyncClient):
    """Test token refresh"""
    # Register and get tokens
    register_response = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "refresh@example.com",
            "full_name": "Refresh User",
            "password": "password123"
        }
    )
    refresh_token = register_response.json()["refresh_token"]
    
    # Refresh access token
    response = await async_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_refresh_invalid_token(async_client: AsyncClient):
    """Test refresh with invalid token"""
    response = await async_client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "invalid.token.here"}
    )
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user(async_client: AsyncClient):
    """Test getting current user info"""
    # Register and get token
    register_response = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "current@example.com",
            "full_name": "Current User",
            "password": "password123"
        }
    )
    access_token = register_response.json()["access_token"]
    
    # Get current user
    response = await async_client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "current@example.com"
    assert data["full_name"] == "Current User"


@pytest.mark.asyncio
async def test_get_current_user_no_token(async_client: AsyncClient):
    """Test getting current user without token"""
    response = await async_client.get("/api/v1/auth/me")
    
    assert response.status_code == 403  # No credentials


@pytest.mark.asyncio
async def test_change_password(async_client: AsyncClient):
    """Test password change"""
    # Register and get token
    register_response = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "changepass@example.com",
            "full_name": "Change Pass User",
            "password": "oldpassword123"
        }
    )
    access_token = register_response.json()["access_token"]
    
    # Change password
    response = await async_client.put(
        "/api/v1/auth/password",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "current_password": "oldpassword123",
            "new_password": "newpassword456"
        }
    )
    
    assert response.status_code == 200
    assert "successfully" in response.json()["message"].lower()
    
    # Verify can login with new password
    login_response = await async_client.post(
        "/api/v1/auth/login",
        json={
            "email": "changepass@example.com",
            "password": "newpassword456"
        }
    )
    assert login_response.status_code == 200


@pytest.mark.asyncio
async def test_change_password_wrong_current(async_client: AsyncClient):
    """Test password change with wrong current password"""
    # Register and get token
    register_response = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "wrongcurrent@example.com",
            "full_name": "Test User",
            "password": "password123"
        }
    )
    access_token = register_response.json()["access_token"]
    
    # Try to change with wrong current password
    response = await async_client.put(
        "/api/v1/auth/password",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "current_password": "wrongpassword",
            "new_password": "newpassword456"
        }
    )
    
    assert response.status_code == 400
    assert "incorrect" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_logout(async_client: AsyncClient):
    """Test logout"""
    # Register and get token
    register_response = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "logout@example.com",
            "full_name": "Logout User",
            "password": "password123"
        }
    )
    access_token = register_response.json()["access_token"]
    
    # Logout
    response = await async_client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    assert response.status_code == 200
    assert "logged out" in response.json()["message"].lower()
