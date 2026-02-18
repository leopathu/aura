"""
OAuth API Endpoints
Handles OAuth2 authentication flow for external services
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.dependencies import get_db, get_current_user
from app.core.config import settings
from app.models.user import User
from app.schemas.oauth import (
    OAuthInitiateResponse,
    OAuthTokenResponse,
    OAuthConnectionStatus
)
from app.services import oauth_service


router = APIRouter(prefix="/auth", tags=["oauth"])


@router.get("/oauth/google")
async def initiate_google_oauth(
    org_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Initiate Google OAuth flow
    
    Generates authorization URL and redirects user to Google consent screen
    """
    # Generate state token
    state = oauth_service.generate_oauth_state(current_user.id, org_id)
    
    # Get Google OAuth client
    client = oauth_service.oauth.create_client('google')
    
    # Generate authorization URL
    redirect_uri = settings.GOOGLE_REDIRECT_URI
    authorization_url = await client.create_authorization_url(
        'https://accounts.google.com/o/oauth2/auth',
        redirect_uri=redirect_uri,
        state=state
    )
    
    # Redirect to Google
    return RedirectResponse(url=authorization_url['url'])


@router.get("/callback/google")
async def google_oauth_callback(
    request: Request,
    code: str,
    state: str,
    db: Session = Depends(get_db)
):
    """
    Google OAuth callback handler
    
    Exchanges authorization code for access token
    """
    # Validate state
    state_data = oauth_service.validate_oauth_state(state)
    if not state_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired state token"
        )
    
    user_id = UUID(state_data['user_id'])
    org_id = UUID(state_data['org_id'])
    
    # Exchange code for token
    try:
        client = oauth_service.oauth.create_client('google')
        token = await client.fetch_access_token(
            code=code,
            redirect_uri=settings.GOOGLE_REDIRECT_URI
        )
        
        # Store token
        await oauth_service.store_oauth_token(
            db,
            user_id,
            org_id,
            'google',
            token['access_token'],
            token.get('refresh_token'),
            token.get('expires_in'),
            token.get('scope'),
            token.get('token_type', 'Bearer')
        )
        
        # Redirect to frontend success page
        return RedirectResponse(
            url=f"{settings.ALLOWED_ORIGINS[0]}/settings/integrations?oauth=success"
        )
    
    except Exception as e:
        # Redirect to frontend error page
        return RedirectResponse(
            url=f"{settings.ALLOWED_ORIGINS[0]}/settings/integrations?oauth=error"
        )


@router.get("/oauth/google/status", response_model=OAuthConnectionStatus)
async def get_google_oauth_status(
    org_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get Google OAuth connection status
    """
    oauth_token = await oauth_service.get_oauth_token(
        db,
        current_user.id,
        org_id,
        'google'
    )
    
    if oauth_token:
        return OAuthConnectionStatus(
            provider='google',
            is_connected=True,
            expires_at=oauth_token.expires_at,
            scope=oauth_token.scope
        )
    else:
        return OAuthConnectionStatus(
            provider='google',
            is_connected=False,
            expires_at=None,
            scope=None
        )


@router.post("/oauth/google/refresh", response_model=OAuthTokenResponse)
async def refresh_google_oauth_token(
    org_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Refresh Google OAuth token
    """
    refreshed_token = await oauth_service.refresh_oauth_token(
        db,
        current_user.id,
        org_id,
        'google'
    )
    
    if not refreshed_token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No OAuth token found or refresh failed"
        )
    
    return OAuthTokenResponse.from_orm(refreshed_token)


@router.delete("/oauth/google/disconnect", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect_google_oauth(
    org_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Disconnect Google OAuth
    
    Revokes access and removes stored token
    """
    success = await oauth_service.revoke_oauth_token(
        db,
        current_user.id,
        org_id,
        'google'
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No OAuth connection found"
        )
    
    return None


# ===== SLACK OAUTH ENDPOINTS =====

@router.get("/oauth/slack")
async def initiate_slack_oauth(
    org_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """
    Initiate Slack OAuth flow
    
    Generates authorization URL and redirects user to Slack consent screen
    """
    # Generate state token
    state = oauth_service.generate_oauth_state(current_user.id, org_id)
    
    # Build authorization URL
    redirect_uri = settings.SLACK_REDIRECT_URI
    scopes = [
        'channels:read',      # List public channels
        'groups:read',        # List private channels
        'chat:write',         # Send messages
        'channels:history',   # Read channel messages
        'groups:history',     # Read private channel messages
        'team:read',          # Get workspace info
        'users:read',         # Read user info for name resolution
    ]
    
    authorization_url = (
        f"https://slack.com/oauth/v2/authorize"
        f"?client_id={settings.SLACK_CLIENT_ID}"
        f"&scope={','.join(scopes)}"
        f"&redirect_uri={redirect_uri}"
        f"&state={state}"
    )
    
    # Redirect to Slack
    return RedirectResponse(url=authorization_url)


@router.get("/callback/slack")
async def slack_oauth_callback(
    request: Request,
    code: str,
    state: str,
    db: Session = Depends(get_db)
):
    """
    Slack OAuth callback handler
    
    Exchanges authorization code for access token
    """
    # Validate state
    state_data = oauth_service.validate_oauth_state(state)
    if not state_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired state token"
        )
    
    user_id = UUID(state_data['user_id'])
    org_id = UUID(state_data['org_id'])
    
    # Exchange code for token
    try:
        import httpx
        
        # Call Slack token endpoint
        async with httpx.AsyncClient() as client:
            response = await client.post(
                'https://slack.com/api/oauth.v2.access',
                data={
                    'client_id': settings.SLACK_CLIENT_ID,
                    'client_secret': settings.SLACK_CLIENT_SECRET,
                    'code': code,
                    'redirect_uri': settings.SLACK_REDIRECT_URI
                }
            )
            token_data = response.json()
        
        if not token_data.get('ok'):
            raise Exception(token_data.get('error', 'Unknown error'))
        
        # Store token
        await oauth_service.store_oauth_token(
            db,
            user_id,
            org_id,
            'slack',
            token_data['access_token'],
            None,  # Slack bot tokens don't expire or refresh
            None,  # No expiration
            token_data.get('scope'),
            'Bearer'
        )
        
        # Redirect to frontend success page
        return RedirectResponse(
            url=f"{settings.ALLOWED_ORIGINS[0]}/settings/integrations?oauth=success"
        )
    
    except Exception as e:
        # Redirect to frontend error page
        return RedirectResponse(
            url=f"{settings.ALLOWED_ORIGINS[0]}/settings/integrations?oauth=error"
        )


@router.get("/oauth/slack/status", response_model=OAuthConnectionStatus)
async def get_slack_oauth_status(
    org_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get Slack OAuth connection status
    """
    oauth_token = await oauth_service.get_oauth_token(
        db,
        current_user.id,
        org_id,
        'slack'
    )
    
    if oauth_token:
        return OAuthConnectionStatus(
            provider='slack',
            is_connected=True,
            expires_at=oauth_token.expires_at,
            scope=oauth_token.scope
        )
    else:
        return OAuthConnectionStatus(
            provider='slack',
            is_connected=False,
            expires_at=None,
            scope=None
        )


@router.post("/oauth/slack/refresh", response_model=OAuthTokenResponse)
async def refresh_slack_oauth_token(
    org_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Refresh Slack OAuth token
    
    Note: Slack bot tokens don't expire, but this endpoint exists for consistency
    """
    oauth_token = await oauth_service.get_oauth_token(
        db,
        current_user.id,
        org_id,
        'slack'
    )
    
    if not oauth_token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No OAuth token found"
        )
    
    return OAuthTokenResponse.from_orm(oauth_token)


@router.delete("/oauth/slack/disconnect", status_code=status.HTTP_204_NO_CONTENT)
async def disconnect_slack_oauth(
    org_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Disconnect Slack OAuth
    
    Revokes access and removes stored token
    """
    success = await oauth_service.revoke_oauth_token(
        db,
        current_user.id,
        org_id,
        'slack'
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No OAuth connection found"
        )
    
    return None
