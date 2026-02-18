"""
FastAPI Dependencies
Authentication and authorization dependencies
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.db.session import get_db
from app.core.jwt import verify_token, get_token_subject
from app.services.user_service import get_user_by_id
from app.models.user import User


# HTTP Bearer token scheme
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token
    
    Args:
        credentials: HTTP authorization credentials
        db: Database session
        
    Returns:
        Current user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    token = credentials.credentials
    
    # Verify token
    payload = verify_token(token, token_type="access")
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract user ID
    user_id_str = payload.get("sub")
    if user_id_str is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID in token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user from database
    user = await get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive"
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user (verified)
    
    Args:
        current_user: Current user from token
        
    Returns:
        Current active user
        
    Raises:
        HTTPException: If user is not verified
    """
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified"
        )
    
    return current_user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Get current user if token provided, None otherwise
    Useful for endpoints that work with or without authentication
    
    Args:
        credentials: Optional HTTP authorization credentials
        db: Database session
        
    Returns:
        Current user or None
    """
    if credentials is None:
        return None
    
    try:
        token = credentials.credentials
        payload = verify_token(token, token_type="access")
        
        if payload is None:
            return None
        
        user_id_str = payload.get("sub")
        if user_id_str is None:
            return None
        
        user_id = UUID(user_id_str)
        user = await get_user_by_id(db, user_id)
        
        return user if user and user.is_active else None
    except Exception:
        return None


def get_current_org_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Optional[UUID]:
    """
    Get current organization ID from token
    
    Args:
        credentials: HTTP authorization credentials
        
    Returns:
        Organization UUID or None
    """
    token = credentials.credentials
    payload = verify_token(token, token_type="access")
    
    if payload is None:
        return None
    
    org_id_str = payload.get("org_id")
    if org_id_str is None:
        return None
    
    try:
        return UUID(org_id_str)
    except ValueError:
        return None
