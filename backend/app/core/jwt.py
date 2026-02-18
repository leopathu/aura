"""
JWT Token Management
Token generation, validation, and refresh
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from uuid import UUID

from app.core.config import settings


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT access token
    
    Args:
        data: Payload data to encode
        expires_delta: Token expiration time (default: 30 minutes)
        
    Returns:
        Encoded JWT token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=30)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT refresh token
    
    Args:
        data: Payload data to encode
        expires_delta: Token expiration time (default: 7 days)
        
    Returns:
        Encoded JWT refresh token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=7)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and validate JWT token
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded payload or None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
    """
    Verify JWT token and check type
    
    Args:
        token: JWT token string
        token_type: Expected token type ("access" or "refresh")
        
    Returns:
        Decoded payload or None if invalid
    """
    payload = decode_token(token)
    
    if payload is None:
        return None
    
    # Check token type
    if payload.get("type") != token_type:
        return None
    
    return payload


def get_token_subject(token: str) -> Optional[str]:
    """
    Extract subject (user_id) from token
    
    Args:
        token: JWT token string
        
    Returns:
        Subject string or None if invalid
    """
    payload = decode_token(token)
    
    if payload is None:
        return None
    
    return payload.get("sub")


def is_token_expired(token: str) -> bool:
    """
    Check if token is expired
    
    Args:
        token: JWT token string
        
    Returns:
        True if expired, False otherwise
    """
    payload = decode_token(token)
    
    if payload is None:
        return True
    
    exp = payload.get("exp")
    if exp is None:
        return True
    
    return datetime.utcnow() > datetime.fromtimestamp(exp)


def create_token_pair(user_id: UUID, org_id: Optional[UUID] = None) -> Dict[str, str]:
    """
    Create access and refresh token pair
    
    Args:
        user_id: User UUID
        org_id: Organization UUID (optional)
        
    Returns:
        Dictionary with access_token and refresh_token
    """
    payload = {
        "sub": str(user_id),
    }
    
    if org_id:
        payload["org_id"] = str(org_id)
    
    access_token = create_access_token(payload)
    refresh_token = create_refresh_token({"sub": str(user_id)})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


def refresh_access_token(refresh_token: str) -> Optional[str]:
    """
    Generate new access token from refresh token
    
    Args:
        refresh_token: Valid refresh token
        
    Returns:
        New access token or None if refresh token invalid
    """
    payload = verify_token(refresh_token, token_type="refresh")
    
    if payload is None:
        return None
    
    user_id = payload.get("sub")
    if not user_id:
        return None
    
    # Create new access token
    new_access_token = create_access_token({"sub": user_id})
    
    return new_access_token
