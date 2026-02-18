"""
Test Rate Limiting
Unit tests for rate limiter
"""

import pytest
from datetime import datetime, timedelta

from app.core.rate_limit import RateLimiter


def test_rate_limiter_allows_under_limit():
    """Test that requests under limit are allowed"""
    limiter = RateLimiter()
    
    # Make 4 requests (under limit of 5)
    for i in range(4):
        allowed, remaining = limiter.is_allowed("test-ip", max_requests=5)
        assert allowed is True
        assert remaining == 4 - i


def test_rate_limiter_blocks_over_limit():
    """Test that requests over limit are blocked"""
    limiter = RateLimiter()
    
    # Make 5 requests (at limit)
    for _ in range(5):
        allowed, remaining = limiter.is_allowed("test-ip", max_requests=5)
        assert allowed is True
    
    # 6th request should be blocked
    allowed, remaining = limiter.is_allowed("test-ip", max_requests=5)
    assert allowed is False
    assert remaining == 0


def test_rate_limiter_resets():
    """Test that reset clears rate limit"""
    limiter = RateLimiter()
    
    # Hit limit
    for _ in range(5):
        limiter.is_allowed("test-ip", max_requests=5)
    
    # Should be blocked
    allowed, _ = limiter.is_allowed("test-ip", max_requests=5)
    assert allowed is False
    
    # Reset
    limiter.reset("test-ip")
    
    # Should be allowed again
    allowed, _ = limiter.is_allowed("test-ip", max_requests=5)
    assert allowed is True


def test_rate_limiter_separate_identifiers():
    """Test that different identifiers have separate limits"""
    limiter = RateLimiter()
    
    # Hit limit for first identifier
    for _ in range(5):
        limiter.is_allowed("ip-1", max_requests=5)
    
    # First should be blocked
    allowed, _ = limiter.is_allowed("ip-1", max_requests=5)
    assert allowed is False
    
    # Second should be allowed
    allowed, _ = limiter.is_allowed("ip-2", max_requests=5)
    assert allowed is True


def test_rate_limiter_cleanup():
    """Test cleanup of old entries"""
    limiter = RateLimiter()
    
    # Add some entries
    limiter.is_allowed("old-ip", max_requests=5)
    limiter.is_allowed("recent-ip", max_requests=5)
    
    # Manually set one entry to old timestamp
    old_time = datetime.utcnow() - timedelta(hours=25)
    limiter.requests["old-ip"] = [old_time]
    
    # Cleanup
    limiter.cleanup_old_entries(hours=24)
    
    # Old entry should be removed
    assert "old-ip" not in limiter.requests
    # Recent entry should remain
    assert "recent-ip" in limiter.requests
