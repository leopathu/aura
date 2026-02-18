"""
CORS Configuration for Aura Platform

TASK-395: Review CORS configuration
Secure CORS settings with origin validation and proper headers
"""

from fastapi.middleware.cors import CORSMiddleware
from typing import List
from app.core.config import settings


class CORSConfig:
    """
    Secure CORS configuration
    
    Security considerations:
    - No wildcard (*) origins in production
    - Specific allowed origins from environment
    - Credentials support with specific origins
    - Limited methods and headers
    """
    
    # Default allowed origins (override with environment variable)
    DEFAULT_ORIGINS = [
        "http://localhost:3000",  # Next.js dev
        "http://localhost:3001",  # Next.js dev (alternate port)
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
    ]
    
    # Production origins (from environment)
    PRODUCTION_ORIGINS = getattr(settings, 'ALLOWED_ORIGINS', [])
    
    @classmethod
    def get_allowed_origins(cls) -> List[str]:
        """Get list of allowed origins"""
        # In production, use only PRODUCTION_ORIGINS
        # In development, merge both
        if getattr(settings, 'ENVIRONMENT', 'development') == 'production':
            return cls.PRODUCTION_ORIGINS
        else:
            return list(set(cls.DEFAULT_ORIGINS + cls.PRODUCTION_ORIGINS))
    
    @classmethod
    def get_cors_config(cls) -> dict:
        """
        Get CORS configuration for FastAPI
        
        Returns:
            Dictionary with CORS middleware configuration
        """
        allowed_origins = cls.get_allowed_origins()
        
        return {
            "allow_origins": allowed_origins,
            "allow_credentials": True,  # Allow cookies/auth headers
            "allow_methods": [
                "GET",
                "POST",
                "PUT",
                "PATCH",
                "DELETE",
                "OPTIONS"
            ],
            "allow_headers": [
                "Authorization",
                "Content-Type",
                "Accept",
                "Origin",
                "User-Agent",
                "DNT",
                "Cache-Control",
                "X-Requested-With",
            ],
            "expose_headers": [
                "Content-Length",
                "Content-Type",
                "X-RateLimit-Limit",
                "X-RateLimit-Remaining",
                "X-RateLimit-Reset",
            ],
            "max_age": 600,  # Cache preflight for 10 minutes
        }
    
    @classmethod
    def validate_origin(cls, origin: str) -> bool:
        """
        Validate if origin is allowed
        
        Args:
            origin: Origin header value
        
        Returns:
            True if origin is allowed
        """
        allowed = cls.get_allowed_origins()
        return origin in allowed
    
    @classmethod
    def is_secure_origin(cls, origin: str) -> bool:
        """
        Check if origin uses HTTPS (in production)
        
        Args:
            origin: Origin URL
        
        Returns:
            True if origin is secure
        """
        if getattr(settings, 'ENVIRONMENT', 'development') == 'production':
            return origin.startswith('https://')
        return True  # Allow HTTP in development


def add_cors_middleware(app):
    """
    Add CORS middleware to FastAPI application
    
    Usage:
        from app.core.cors import add_cors_middleware
        add_cors_middleware(app)
    """
    config = CORSConfig.get_cors_config()
    
    app.add_middleware(
        CORSMiddleware,
        **config
    )


# Security Notes for CORS:
# 
# 1. Never use allow_origins=["*"] in production
#    - Allows any site to make requests
#    - Bypasses same-origin policy
#    - Enables CSRF attacks
#
# 2. Only allow specific, trusted origins
#    - Use environment variables for configuration
#    - Validate origins before adding
#
# 3. Be careful with allow_credentials=True
#    - Cannot be used with wildcard origins
#    - Allows cookies and auth headers
#    - Only use with specific origins
#
# 4. Limit allowed methods and headers
#    - Only allow what's necessary
#    - Reduces attack surface
#
# 5. Use max_age appropriately
#    - Caches preflight requests
#    - Balance between performance and security
#
# 6. In production, enforce HTTPS
#    - All origins should use https://
#    - Prevents man-in-the-middle attacks
#
# 7. Monitor CORS errors
#    - Log blocked requests
#    - Helps identify legitimate vs malicious traffic


# Example environment variable configuration:
# 
# # .env
# ENVIRONMENT=production
# ALLOWED_ORIGINS=["https://app.aura.com", "https://www.aura.com"]
# 
# # This will:
# - Only allow requests from app.aura.com and www.aura.com
# - Enforce HTTPS in production
# - Enable credentials (cookies, auth headers)
# - Limit methods to GET, POST, PUT, PATCH, DELETE
# - Expose rate limit headers
