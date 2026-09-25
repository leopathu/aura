from typing import Optional
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import decode_token
from app.models import User, OrganizationUser, Organization
from app.rbac.service import RBACService

security = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication credentials not provided",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

    res = await db.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return user

async def get_current_organization_id(
    x_organization_id: Optional[str] = Header(None, alias="X-Organization-Id"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> str:
    """Extracts target organization from X-Organization-Id header or defaults to user's first org."""
    if x_organization_id:
        res = await db.execute(
            select(OrganizationUser).where(
                OrganizationUser.user_id == current_user.id,
                OrganizationUser.organization_id == x_organization_id,
                OrganizationUser.status == "ACTIVE"
            )
        )
        membership = res.scalar_one_or_none()
        if membership or current_user.is_superuser:
            return x_organization_id

    # Fallback to user's first active organization
    res = await db.execute(
        select(OrganizationUser.organization_id).where(
            OrganizationUser.user_id == current_user.id,
            OrganizationUser.status == "ACTIVE"
        )
    )
    first_org_id = res.scalar_one_or_none()
    if not first_org_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User does not belong to any active organization")
    return first_org_id

def require_permission(permission_code: str):
    """Enforces that the current user possesses the required permission within the active organization."""
    async def _dependency(
        current_user: User = Depends(get_current_user),
        org_id: str = Depends(get_current_organization_id),
        db: AsyncSession = Depends(get_db)
    ):
        if current_user.is_superuser:
            return True
        has_perm = await RBACService.has_permission(db, current_user.id, org_id, permission_code)
        if not has_perm:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: Requires '{permission_code}'"
            )
        return True
    return _dependency
