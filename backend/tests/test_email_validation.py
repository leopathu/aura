"""
Test Email Validation
Unit tests for email validation utilities
"""

import pytest
from app.core.email_validation import (
    is_valid_email,
    normalize_email,
    validate_email_format
)


def test_valid_email():
    """Test valid email formats"""
    valid_emails = [
        "user@example.com",
        "user.name@example.com",
        "user+tag@example.co.uk",
        "user123@test-domain.com"
    ]
    
    for email in valid_emails:
        assert is_valid_email(email) is True


def test_invalid_email():
    """Test invalid email formats"""
    invalid_emails = [
        "notanemail",
        "@example.com",
        "user@",
        "user@.com",
        "user space@example.com"
    ]
    
    for email in invalid_emails:
        assert is_valid_email(email) is False


def test_normalize_email():
    """Test email normalization"""
    assert normalize_email("  USER@EXAMPLE.COM  ") == "user@example.com"
    assert normalize_email("User@Example.Com") == "user@example.com"
    assert normalize_email("user@example.com") == "user@example.com"


def test_validate_email_format():
    """Test email validation with message"""
    # Valid email
    is_valid, result = validate_email_format("user@example.com")
    assert is_valid is True
    assert result == "user@example.com"
    
    # Invalid email
    is_valid, message = validate_email_format("notanemail")
    assert is_valid is False
    assert isinstance(message, str)
    assert len(message) > 0
