from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models import Role, Permission, RolePermission, OrganizationUser, User
from app.schemas.domain import RoleCreate, RoleResponse, AssignRoleRequest
from app.api.deps import get_current_user, get_current_organization_id, require_permission

router = APIRouter(prefix="/rbac", tags=["RBAC & Permissions"])

@router.get("/permissions")
async def list_permissions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(Permission).order_by(Permission.category, Permission.name))
    perms = res.scalars().all()
    return [{"id": p.id, "code": p.code, "name": p.name, "category": p.category, "description": p.description} for p in perms]

@router.get("/roles")
async def list_roles(
    org_id: str = Depends(get_current_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(Role).where(Role.organization_id == org_id))
    roles = res.scalars().all()
    output = []
    for r in roles:
        p_res = await db.execute(
            select(Permission.code)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .where(RolePermission.role_id == r.id)
        )
        p_codes = p_res.scalars().all()
        output.append({
            "id": r.id,
            "organization_id": r.organization_id,
            "name": r.name,
            "description": r.description,
            "is_system": r.is_system,
            "permissions": list(p_codes)
        })
    return output

@router.post("/roles", dependencies=[Depends(require_permission("admin.roles"))])
async def create_custom_role(
    payload: RoleCreate,
    org_id: str = Depends(get_current_organization_id),
    db: AsyncSession = Depends(get_db)
):
    role = Role(
        organization_id=org_id,
        name=payload.name,
        description=payload.description,
        is_system=False
    )
    db.add(role)
    await db.flush()

    if payload.permission_codes:
        p_res = await db.execute(select(Permission).where(Permission.code.in_(payload.permission_codes)))
        perms = p_res.scalars().all()
        for p in perms:
            rp = RolePermission(role_id=role.id, permission_id=p.id)
            db.add(rp)

    await db.commit()
    await db.refresh(role)
    return {"id": role.id, "name": role.name, "description": role.description}

@router.post("/assign", dependencies=[Depends(require_permission("admin.roles"))])
async def assign_role(
    payload: AssignRoleRequest,
    org_id: str = Depends(get_current_organization_id),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(
        select(OrganizationUser).where(
            OrganizationUser.organization_id == org_id,
            OrganizationUser.user_id == payload.user_id
        )
    )
    m = res.scalar_one_or_none()
    if not m:
        raise HTTPException(status_code=404, detail="User membership not found in this organization")

    # Verify role belongs to this org
    r_res = await db.execute(select(Role).where(Role.id == payload.role_id, Role.organization_id == org_id))
    role = r_res.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found in this organization")

    m.role_id = role.id
    await db.commit()
    return {"status": "success", "message": f"Assigned role {role.name}"}
