"""
OAuth Service
Handles OAuth2 authentication flow with multiple providers
"""

from authlib.integrations.starlette_client import OAuth
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime, timedelta
import secrets

from app.core.config import settings
from app.models.oauth_token import OAuthToken
from app.services.encryption_service import encryption_service


# OAuth client configuration
oauth = OAuth()

# Register Google OAuth
oauth.register(
    name='google',
    client_id=settings.GOOGLE_CLIENT_ID,
    client_secret=settings.GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile https://www.googleapis.com/auth/gmail.readonly https://www.googleapis.com/auth/gmail.send'
    }
)


# OAuth state storage (in-memory for simplicity, use Redis in production)
oauth_states: Dict[str, Dict[str, Any]] = {}


def generate_oauth_state(user_id: UUID, org_id: UUID) -> str:
    """
    Generate OAuth state token
    
    Args:
        user_id: User ID
        org_id: Organization ID
        
    Returns:
        State token
    """
    state = secrets.token_urlsafe(32)
    oauth_states[state] = {
        'user_id': str(user_id),
        'org_id': str(org_id),
        'created_at': datetime.utcnow()
    }
    
    # Clean up old states (older than 10 minutes)
    cleanup_old_states()
    
    return state


def validate_oauth_state(state: str) -> Optional[Dict[str, Any]]:
    """
    Validate OAuth state token
    
    Args:
        state: State token
        
    Returns:
        State data or None
    """
    state_data = oauth_states.get(state)
    if not state_data:
        return None
    
    # Check if state is expired (10 minutes)
    if datetime.utcnow() - state_data['created_at'] > timedelta(minutes=10):
        oauth_states.pop(state, None)
        return None
    
    # Remove used state
    oauth_states.pop(state, None)
    
    return state_data


def cleanup_old_states():
    """Remove OAuth states older than 10 minutes"""
    cutoff = datetime.utcnow() - timedelta(minutes=10)
    to_remove = [
        state for state, data in oauth_states.items()
        if data['created_at'] < cutoff
    ]
    for state in to_remove:
        oauth_states.pop(state, None)


async def store_oauth_token(
    db: Session,
    user_id: UUID,
    org_id: UUID,
    provider: str,
    access_token: str,
    refresh_token: Optional[str] = None,
    expires_in: Optional[int] = None,
    scope: Optional[str] = None,
    token_type: str = "Bearer"
) -> OAuthToken:
    """
    Store OAuth token with encryption
    
    Args:
        db: Database session
        user_id: User ID
        org_id: Organization ID
        provider: OAuth provider (google, microsoft, etc.)
        access_token: Access token
        refresh_token: Optional refresh token
        expires_in: Token expiration in seconds
        scope: Token scopes
        token_type: Token type (usually Bearer)
        
    Returns:
        Created OAuth token
    """
    # Check if token already exists
    existing_token = db.query(OAuthToken).filter(
        OAuthToken.user_id == user_id,
        OAuthToken.org_id == org_id,
        OAuthToken.provider == provider
    ).first()
    
    # Encrypt tokens
    encrypted_access = encryption_service.encrypt(access_token)
    encrypted_refresh = encryption_service.encrypt(refresh_token) if refresh_token else None
    
    # Calculate expiration
    expires_at = None
    if expires_in:
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
    
    if existing_token:
        # Update existing token
        existing_token.encrypted_access_token = encrypted_access
        if encrypted_refresh:
            existing_token.encrypted_refresh_token = encrypted_refresh
        existing_token.token_type = token_type
        existing_token.expires_at = expires_at
        existing_token.scope = scope
        existing_token.is_active = True
        existing_token.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(existing_token)
        return existing_token
    else:
        # Create new token
        oauth_token = OAuthToken(
            user_id=user_id,
            org_id=org_id,
            provider=provider,
            encrypted_access_token=encrypted_access,
            encrypted_refresh_token=encrypted_refresh,
            token_type=token_type,
            expires_at=expires_at,
            scope=scope
        )
        
        db.add(oauth_token)
        db.commit()
        db.refresh(oauth_token)
        return oauth_token


async def get_oauth_token(
    db: Session,
    user_id: UUID,
    org_id: UUID,
    provider: str
) -> Optional[OAuthToken]:
    """
    Get OAuth token for user and provider
    
    Args:
        db: Database session
        user_id: User ID
        org_id: Organization ID
        provider: OAuth provider
        
    Returns:
        OAuth token or None
    """
    return db.query(OAuthToken).filter(
        OAuthToken.user_id == user_id,
        OAuthToken.org_id == org_id,
        OAuthToken.provider == provider,
        OAuthToken.is_active == True
    ).first()


async def get_decrypted_access_token(
    db: Session,
    user_id: UUID,
    org_id: UUID,
    provider: str
) -> Optional[str]:
    """
    Get decrypted access token
    
    Args:
        db: Database session
        user_id: User ID
        org_id: Organization ID
        provider: OAuth provider
        
    Returns:
        Decrypted access token or None
    """
    oauth_token = await get_oauth_token(db, user_id, org_id, provider)
    if not oauth_token:
        return None
    
    return encryption_service.decrypt(oauth_token.encrypted_access_token)


async def refresh_oauth_token(
    db: Session,
    user_id: UUID,
    org_id: UUID,
    provider: str
) -> Optional[OAuthToken]:
    """
    Refresh OAuth token using refresh token
    
    Args:
        db: Database session
        user_id: User ID
        org_id: Organization ID
        provider: OAuth provider
        
    Returns:
        Updated OAuth token or None
    """
    oauth_token = await get_oauth_token(db, user_id, org_id, provider)
    if not oauth_token or not oauth_token.encrypted_refresh_token:
        return None
    
    # Decrypt refresh token
    refresh_token = encryption_service.decrypt(oauth_token.encrypted_refresh_token)
    
    # Use authlib to refresh
    try:
        client = oauth.create_client(provider)
        token_response = await client.fetch_access_token(
            grant_type='refresh_token',
            refresh_token=refresh_token
        )
        
        # Update token
        oauth_token.encrypted_access_token = encryption_service.encrypt(
            token_response['access_token']
        )
        
        if 'refresh_token' in token_response:
            oauth_token.encrypted_refresh_token = encryption_service.encrypt(
                token_response['refresh_token']
            )
        
        if 'expires_in' in token_response:
            oauth_token.expires_at = datetime.utcnow() + timedelta(
                seconds=token_response['expires_in']
            )
        
        oauth_token.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(oauth_token)
        
        return oauth_token
    
    except Exception:
        return None


async def revoke_oauth_token(
    db: Session,
    user_id: UUID,
    org_id: UUID,
    provider: str
) -> bool:
    """
    Revoke OAuth token
    
    Args:
        db: Database session
        user_id: User ID
        org_id: Organization ID
        provider: OAuth provider
        
    Returns:
        True if revoked, False otherwise
    """
    oauth_token = await get_oauth_token(db, user_id, org_id, provider)
    if not oauth_token:
        return False
    
    # Mark as inactive
    oauth_token.is_active = False
    db.commit()
    
    return True
