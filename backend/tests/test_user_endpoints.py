"""
Test User Endpoints
Integration tests for user API
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_get_my_profile(async_client: AsyncClient):
    """Test getting current user profile"""
    # Register and get token
    register_response = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "profile@example.com",
            "full_name": "Profile User",
            "password": "password123"
        }
    )
    access_token = register_response.json()["access_token"]
    
    # Get profile
    response = await async_client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "profile@example.com"
    assert data["full_name"] == "Profile User"


@pytest.mark.asyncio
async def test_update_my_profile(async_client: AsyncClient):
    """Test updating current user profile"""
    # Register and get token
    register_response = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "update@example.com",
            "full_name": "Original Name",
            "password": "password123"
        }
    )
    access_token = register_response.json()["access_token"]
    
    # Update profile
    response = await async_client.put(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "full_name": "Updated Name"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated Name"
    assert data["email"] == "update@example.com"


@pytest.mark.asyncio
async def test_delete_my_account(async_client: AsyncClient):
    """Test deleting user account"""
    # Register and get token
    register_response = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "delete@example.com",
            "full_name": "Delete User",
            "password": "password123"
        }
    )
    access_token = register_response.json()["access_token"]
    
    # Delete account
    response = await async_client.delete(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    assert response.status_code == 200
    assert "deleted" in response.json()["message"].lower()
    
    # Verify cannot login after deletion
    login_response = await async_client.post(
        "/api/v1/auth/login",
        json={
            "email": "delete@example.com",
            "password": "password123"
        }
    )
    assert login_response.status_code == 401


@pytest.mark.asyncio
async def test_get_user_by_id(async_client: AsyncClient):
    """Test getting user by ID"""
    # Register and get token
    register_response = await async_client.post(
        "/api/v1/auth/register",
        json={
            "email": "getbyid@example.com",
            "full_name": "Get By ID User",
            "password": "password123"
        }
    )
    access_token = register_response.json()["access_token"]
    user_id = register_response.json()["user_id"]
    
    # Get user by ID
    response = await async_client.get(
        f"/api/v1/users/{user_id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "getbyid@example.com"


@pytest.mark.asyncio
async def test_get_user_unauthorized(async_client: AsyncClient):
    """Test getting user without authentication"""
    response = await async_client.get("/api/v1/users/me")
    
    assert response.status_code == 403
