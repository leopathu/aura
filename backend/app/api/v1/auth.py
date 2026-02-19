"""
Authentication Router
Handles user registration, login, token refresh, and password management
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from app.db.session import get_db
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
    TokenRefreshRequest,
    TokenRefreshResponse,
    PasswordChangeRequest,
    MessageResponse
)
from app.schemas.user import UserResponse
from app.services.user_service import (
    create_user,
    get_user_by_email,
    verify_user_password,
    update_user
)
from app.core.jwt import create_token_pair, refresh_access_token
from app.core.dependencies import get_current_user
from app.core.rate_limit import rate_limiter
from app.core.security import verify_password
from app.models.user import User
from app.models.organization import Organization, Membership, MemberRole


router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_client_ip(request: Request) -> str:
    """Extract client IP address from request"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: Request,
    user_data: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user
    
    - Creates user account
    - Creates default organization
    - Generates access and refresh tokens
    """
    # Rate limiting
    client_ip = get_client_ip(request)
    allowed, remaining = rate_limiter.is_allowed(f"register:{client_ip}", max_requests=5, window_minutes=60)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many registration attempts. Please try again later."
        )
    
    # Check if user already exists
    existing_user = await get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Create user
    from app.schemas.user import UserCreate
    user = await create_user(
        db,
        UserCreate(
            email=user_data.email,
            full_name=user_data.full_name,
            password=user_data.password
        )
    )
    
    # Create default organization
    from app.core.config import settings
    org_slug = user.email.split('@')[0] + '-workspace'
    org = Organization(
        name=f"{user.full_name}'s Workspace",
        slug=org_slug
    )
    db.add(org)
    await db.flush()
    
    # Create membership (owner role)
    membership = Membership(
        user_id=user.id,
        org_id=org.id,
        role=MemberRole.OWNER
    )
    db.add(membership)
    await db.commit()
    await db.refresh(user)
    
    # Generate tokens
    tokens = create_token_pair(user.id, org.id)
    
    return RegisterResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type=tokens["token_type"],
        user_id=user.id,
        email=user.email,
        full_name=user.full_name,
        message="Registration successful. Please verify your email."
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    request: Request,
    credentials: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Login with email and password
    
    - Validates credentials
    - Returns access and refresh tokens
    """
    # Rate limiting
    client_ip = get_client_ip(request)
    allowed, remaining = rate_limiter.is_allowed(
        f"login:{credentials.email}:{client_ip}",
        max_requests=5,
        window_minutes=15
    )
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Please try again later."
        )
    
    # Verify credentials
    user = await verify_user_password(db, credentials.email, credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Get user's default organization (first membership)
    from sqlalchemy import select
    from app.models.organization import Membership
    
    result = await db.execute(
        select(Membership)
        .where(Membership.user_id == user.id)
        .order_by(Membership.joined_at)
        .limit(1)
    )
    membership = result.scalar_one_or_none()
    org_id = membership.org_id if membership else None
    
    # Generate tokens
    tokens = create_token_pair(user.id, org_id)
    
    # Reset rate limit on successful login
    rate_limiter.reset(f"login:{credentials.email}:{client_ip}")
    
    return LoginResponse(
        access_token=tokens["access_token"],
        refresh_token=tokens["refresh_token"],
        token_type=tokens["token_type"],
        user_id=user.id,
        email=user.email,
        full_name=user.full_name
    )


@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_token(token_data: TokenRefreshRequest):
    """
    Refresh access token using refresh token
    
    - Validates refresh token
    - Returns new access token
    """
    new_access_token = refresh_access_token(token_data.refresh_token)
    
    if not new_access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return TokenRefreshResponse(
        access_token=new_access_token,
        token_type="bearer"
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user information
    
    - Requires valid access token
    - Returns user profile
    """
    return current_user


@router.put("/password", response_model=MessageResponse)
async def change_password(
    password_data: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Change user password
    
    - Requires current password verification
    - Updates to new password
    """
    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Update password
    from app.schemas.user import UserUpdate
    await update_user(
        db,
        current_user.id,
        UserUpdate(password=password_data.new_password)
    )
    
    return MessageResponse(message="Password changed successfully")


@router.post("/logout", response_model=MessageResponse)
async def logout(current_user: User = Depends(get_current_user)):
    """
    Logout user
    
    Note: Since we're using stateless JWT tokens, actual token invalidation
    would require a token blacklist (Redis). For now, client should discard tokens.
    
    - Client should remove tokens from storage
    - Future: Implement token blacklist
    """
    return MessageResponse(
        message="Logged out successfully. Please discard your tokens."
    )


@router.post("/verify-email/{token}", response_model=MessageResponse)
async def verify_email(
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Verify user email with token
    
    - Validates email verification token
    - Marks user as verified
    
    Note: Email verification token generation will be implemented
    when email service is added.
    """
    # TODO: Implement email verification token validation
    # For now, this is a placeholder
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Email verification not yet implemented"
    )


@router.post("/resend-verification", response_model=MessageResponse)
async def resend_verification_email(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Resend email verification link
    
    - Generates new verification token
    - Sends email to user
    
    Note: Email service will be implemented later
    """
    if current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already verified"
        )
    
    # TODO: Generate verification token and send email
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Email service not yet implemented"
    )
