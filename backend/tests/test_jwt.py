"""
Test JWT Token Functions
Unit tests for JWT token creation and validation
"""

import pytest
from datetime import timedelta
from uuid import uuid4

from app.core.jwt import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_token,
    get_token_subject,
    is_token_expired,
    create_token_pair,
    refresh_access_token
)


def test_create_access_token():
    """Test access token creation"""
    user_id = uuid4()
    data = {"sub": str(user_id)}
    
    token = create_access_token(data)
    
    assert isinstance(token, str)
    assert len(token) > 0
    
    # Decode and verify payload
    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == str(user_id)
    assert payload["type"] == "access"


def test_create_refresh_token():
    """Test refresh token creation"""
    user_id = uuid4()
    data = {"sub": str(user_id)}
    
    token = create_refresh_token(data)
    
    assert isinstance(token, str)
    assert len(token) > 0
    
    # Decode and verify payload
    payload = decode_token(token)
    assert payload is not None
    assert payload["sub"] == str(user_id)
    assert payload["type"] == "refresh"


def test_decode_token():
    """Test token decoding"""
    user_id = uuid4()
    data = {"sub": str(user_id), "custom": "data"}
    
    token = create_access_token(data)
    payload = decode_token(token)
    
    assert payload is not None
    assert payload["sub"] == str(user_id)
    assert payload["custom"] == "data"
    assert "exp" in payload
    assert "iat" in payload


def test_decode_invalid_token():
    """Test decoding invalid token"""
    invalid_token = "invalid.token.here"
    payload = decode_token(invalid_token)
    
    assert payload is None


def test_verify_token():
    """Test token verification"""
    user_id = uuid4()
    data = {"sub": str(user_id)}
    
    access_token = create_access_token(data)
    refresh_token = create_refresh_token(data)
    
    # Verify access token
    payload = verify_token(access_token, token_type="access")
    assert payload is not None
    assert payload["type"] == "access"
    
    # Verify refresh token
    payload = verify_token(refresh_token, token_type="refresh")
    assert payload is not None
    assert payload["type"] == "refresh"
    
    # Wrong type should fail
    payload = verify_token(access_token, token_type="refresh")
    assert payload is None


def test_get_token_subject():
    """Test extracting subject from token"""
    user_id = uuid4()
    data = {"sub": str(user_id)}
    
    token = create_access_token(data)
    subject = get_token_subject(token)
    
    assert subject == str(user_id)


def test_is_token_expired():
    """Test token expiration check"""
    user_id = uuid4()
    data = {"sub": str(user_id)}
    
    # Create token that expires in 1 hour (not expired)
    token = create_access_token(data, expires_delta=timedelta(hours=1))
    assert is_token_expired(token) is False
    
    # Create token that expired 1 hour ago
    token = create_access_token(data, expires_delta=timedelta(hours=-1))
    assert is_token_expired(token) is True


def test_create_token_pair():
    """Test creating access and refresh token pair"""
    user_id = uuid4()
    org_id = uuid4()
    
    tokens = create_token_pair(user_id, org_id)
    
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert "token_type" in tokens
    assert tokens["token_type"] == "bearer"
    
    # Verify access token
    access_payload = verify_token(tokens["access_token"], token_type="access")
    assert access_payload is not None
    assert access_payload["sub"] == str(user_id)
    assert access_payload["org_id"] == str(org_id)
    
    # Verify refresh token
    refresh_payload = verify_token(tokens["refresh_token"], token_type="refresh")
    assert refresh_payload is not None
    assert refresh_payload["sub"] == str(user_id)


def test_refresh_access_token():
    """Test refreshing access token"""
    user_id = uuid4()
    
    # Create initial token pair
    tokens = create_token_pair(user_id)
    
    # Refresh access token
    new_access_token = refresh_access_token(tokens["refresh_token"])
    
    assert new_access_token is not None
    assert isinstance(new_access_token, str)
    
    # Verify new access token
    payload = verify_token(new_access_token, token_type="access")
    assert payload is not None
    assert payload["sub"] == str(user_id)


def test_refresh_with_invalid_token():
    """Test refreshing with invalid refresh token"""
    new_access_token = refresh_access_token("invalid.token")
    assert new_access_token is None


def test_refresh_with_access_token():
    """Test refreshing with access token (should fail)"""
    user_id = uuid4()
    access_token = create_access_token({"sub": str(user_id)})
    
    # Should fail because it's an access token, not refresh
    new_access_token = refresh_access_token(access_token)
    assert new_access_token is None
