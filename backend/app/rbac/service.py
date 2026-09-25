from typing import List, Set, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Permission, Role, RolePermission, OrganizationUser
from app.rbac.constants import SYSTEM_PERMISSIONS, DEFAULT_ROLE_DEFINITIONS

class RBACService:
    @staticmethod
    async def init_system_permissions(db: AsyncSession) -> None:
        """Seed all system permissions into the database if not present."""
        for perm_def in SYSTEM_PERMISSIONS:
            result = await db.execute(select(Permission).where(Permission.code == perm_def["code"]))
            existing = result.scalar_one_or_none()
            if not existing:
                perm = Permission(
                    code=perm_def["code"],
                    name=perm_def["name"],
                    category=perm_def["category"],
                    description=perm_def["description"],
                )
                db.add(perm)
        await db.commit()

    @staticmethod
    async def init_organization_roles(db: AsyncSession, organization_id: str) -> None:
        """Create standard roles and bind permissions for a new organization."""
        # Ensure system permissions exist
        await RBACService.init_system_permissions(db)
        
        # Load all permissions map
        res = await db.execute(select(Permission))
        all_perms = {p.code: p.id for p in res.scalars().all()}

        for role_name, perm_codes in DEFAULT_ROLE_DEFINITIONS.items():
            result = await db.execute(
                select(Role).where(
                    Role.organization_id == organization_id,
                    Role.name == role_name
                )
            )
            role = result.scalar_one_or_none()
            if not role:
                role = Role(
                    organization_id=organization_id,
                    name=role_name,
                    description=f"Standard {role_name} role",
                    is_system=True
                )
                db.add(role)
                await db.flush()

                for code in perm_codes:
                    if code in all_perms:
                        rp = RolePermission(
                            role_id=role.id,
                            permission_id=all_perms[code]
                        )
                        db.add(rp)
        await db.commit()

    @staticmethod
    async def get_user_permissions(db: AsyncSession, user_id: str, organization_id: str) -> Set[str]:
        """Fetch all permission codes granted to the user within an organization."""
        # Check if user has an active membership and role
        stmt = (
            select(Permission.code)
            .join(RolePermission, RolePermission.permission_id == Permission.id)
            .join(Role, Role.id == RolePermission.role_id)
            .join(OrganizationUser, OrganizationUser.role_id == Role.id)
            .where(
                OrganizationUser.user_id == user_id,
                OrganizationUser.organization_id == organization_id,
                OrganizationUser.status == "ACTIVE"
            )
        )
        result = await db.execute(stmt)
        return set(result.scalars().all())

    @staticmethod
    async def has_permission(db: AsyncSession, user_id: str, organization_id: str, permission_code: str) -> bool:
        """Check if user has a specific permission."""
        perms = await RBACService.get_user_permissions(db, user_id, organization_id)
        return permission_code in perms
