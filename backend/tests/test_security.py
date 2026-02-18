"""
Test Security Functions
Unit tests for password hashing and verification
"""

import pytest
from app.core.security import get_password_hash, verify_password


def test_password_hash():
    """Test password hashing"""
    password = "testpassword123"
    hashed = get_password_hash(password)
    
    # Hash should be different from original
    assert hashed != password
    
    # Hash should be a string
    assert isinstance(hashed, str)
    
    # Hash should start with bcrypt identifier
    assert hashed.startswith("$2b$")


def test_password_verification():
    """Test password verification"""
    password = "testpassword123"
    hashed = get_password_hash(password)
    
    # Correct password should verify
    assert verify_password(password, hashed) is True
    
    # Incorrect password should not verify
    assert verify_password("wrongpassword", hashed) is False


def test_different_hashes_for_same_password():
    """Test that same password produces different hashes (due to salt)"""
    password = "testpassword123"
    hash1 = get_password_hash(password)
    hash2 = get_password_hash(password)
    
    # Hashes should be different
    assert hash1 != hash2
    
    # But both should verify the password
    assert verify_password(password, hash1) is True
    assert verify_password(password, hash2) is True


def test_long_password():
    """Test that long passwords work (bcrypt 72-byte limitation handled)"""
    # Password longer than 72 bytes
    long_password = "a" * 100
    hashed = get_password_hash(long_password)
    
    # Should verify correctly
    assert verify_password(long_password, hashed) is True
