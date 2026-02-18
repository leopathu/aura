"""
Rate Limiting Utilities
Simple in-memory rate limiting for authentication endpoints
"""

from datetime import datetime, timedelta
from typing import Dict, Tuple
from collections import defaultdict


class RateLimiter:
    """
    Simple in-memory rate limiter
    For production, use Redis-based rate limiting
    """
    
    def __init__(self):
        # Store: {identifier: [(timestamp, count)]}
        self.requests: Dict[str, list] = defaultdict(list)
    
    def is_allowed(
        self,
        identifier: str,
        max_requests: int = 5,
        window_minutes: int = 15
    ) -> Tuple[bool, int]:
        """
        Check if request is allowed under rate limit
        
        Args:
            identifier: Unique identifier (e.g., IP address or email)
            max_requests: Maximum requests allowed in window
            window_minutes: Time window in minutes
            
        Returns:
            Tuple of (is_allowed, remaining_attempts)
        """
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=window_minutes)
        
        # Clean old requests
        self.requests[identifier] = [
            req_time for req_time in self.requests[identifier]
            if req_time > window_start
        ]
        
        # Check if under limit
        current_count = len(self.requests[identifier])
        
        if current_count >= max_requests:
            return False, 0
        
        # Record new request
        self.requests[identifier].append(now)
        
        remaining = max_requests - current_count - 1
        return True, remaining
    
    def reset(self, identifier: str):
        """
        Reset rate limit for identifier
        
        Args:
            identifier: Unique identifier to reset
        """
        if identifier in self.requests:
            del self.requests[identifier]
    
    def cleanup_old_entries(self, hours: int = 24):
        """
        Clean up old rate limit entries
        
        Args:
            hours: Remove entries older than this many hours
        """
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        
        identifiers_to_remove = []
        for identifier, timestamps in self.requests.items():
            # Keep only recent timestamps
            self.requests[identifier] = [
                ts for ts in timestamps if ts > cutoff
            ]
            
            # Mark for removal if empty
            if not self.requests[identifier]:
                identifiers_to_remove.append(identifier)
        
        # Remove empty entries
        for identifier in identifiers_to_remove:
            del self.requests[identifier]


# Global rate limiter instance
rate_limiter = RateLimiter()
