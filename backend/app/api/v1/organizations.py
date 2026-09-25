from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models import Organization, OrganizationUser, User, Role
from app.schemas.domain import OrganizationCreate, OrganizationResponse
from app.api.deps import get_current_user, get_current_organization_id, require_permission
from app.rbac.service import RBACService
import re

router = APIRouter(prefix="/organizations", tags=["Organizations"])

@router.get("", response_model=List[OrganizationResponse])
async def list_user_organizations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(Organization)
        .join(OrganizationUser, OrganizationUser.organization_id == Organization.id)
        .where(OrganizationUser.user_id == current_user.id)
    )
    res = await db.execute(stmt)
    return res.scalars().all()

@router.post("", response_model=OrganizationResponse)
async def create_organization(
    payload: OrganizationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    slug = re.sub(r'[-\s]+', '-', re.sub(r'[^\w\s-]', '', payload.name.lower().strip()))
    org = Organization(name=payload.name, slug=slug)
    db.add(org)
    await db.flush()

    await RBACService.init_organization_roles(db, org.id)
    admin_role = (await db.execute(select(Role).where(Role.organization_id == org.id, Role.name == "Organization Admin"))).scalar_one_or_none()

    membership = OrganizationUser(
        organization_id=org.id,
        user_id=current_user.id,
        role_id=admin_role.id if admin_role else None,
        status="ACTIVE"
    )
    db.add(membership)
    await db.commit()
    await db.refresh(org)
    return org

@router.get("/users")
async def list_organization_users(
    org_id: str = Depends(get_current_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = (
        select(User, Role, OrganizationUser.status, OrganizationUser.created_at)
        .join(OrganizationUser, OrganizationUser.user_id == User.id)
        .outerjoin(Role, Role.id == OrganizationUser.role_id)
        .where(OrganizationUser.organization_id == org_id)
    )
    res = await db.execute(stmt)
    rows = res.all()
    return [
        {
            "id": u.id,
            "name": u.name,
            "email": u.email,
            "status": status,
            "role": {"id": r.id, "name": r.name} if r else None,
            "joined_at": created_at.isoformat() if created_at else None
        }
        for u, r, status, created_at in rows
    ]
