"""Auth routes: register, login, and current-user."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.exceptions import AuraException
from app.db.session import get_db
from app.models.user import User
from app.schemas.auth import Token, UserCreate, UserLogin, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    payload: UserCreate,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    """Register a new user account."""
    try:
        svc = AuthService(db)
        user = await svc.register(payload)
        return UserResponse.model_validate(user)
    except AuraException as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=exc.detail)


@router.post("/login", response_model=Token)
async def login(
    payload: UserLogin,
    db: AsyncSession = Depends(get_db),
) -> Token:
    """Authenticate and receive a JWT access token."""
    try:
        svc = AuthService(db)
        return await svc.login(payload)
    except AuraException as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=exc.detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    """Return the profile of the currently authenticated user."""
    return UserResponse.model_validate(current_user)
