from typing import List, Optional
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Brain, BrainRole, DataSource, Document, OrganizationUser, Role, User

class BrainService:
    @staticmethod
    async def get_user_accessible_brain_ids(
        db: AsyncSession,
        user_id: str,
        organization_id: str
    ) -> Optional[List[str]]:
        """
        Determines the list of Brain IDs accessible to the user based on their assigned role.
        Returns None if user is an Organization Admin / Superuser (unrestricted access to all brains).
        """
        user_res = await db.execute(select(User).where(User.id == user_id))
        user = user_res.scalar_one_or_none()
        if user and user.is_superuser:
            return None

        # Check membership and role
        stmt = (
            select(Role.name, OrganizationUser.role_id)
            .join(Role, Role.id == OrganizationUser.role_id)
            .where(
                OrganizationUser.user_id == user_id,
                OrganizationUser.organization_id == organization_id,
                OrganizationUser.status == "ACTIVE"
            )
        )
        res = await db.execute(stmt)
        row = res.first()
        if not row:
            return []

        role_name, role_id = row
        # Organization Admin has full visibility into all brains
        if role_name in ["Organization Admin", "Super Admin"]:
            return None

        # Query brains assigned to this role
        b_stmt = select(BrainRole.brain_id).where(BrainRole.role_id == role_id)
        b_res = await db.execute(b_stmt)
        return list(b_res.scalars().all())

    @staticmethod
    async def create_brain(
        db: AsyncSession,
        organization_id: str,
        name: str,
        description: Optional[str] = None,
        role_ids: Optional[List[str]] = None,
        source_ids: Optional[List[str]] = None,
        document_ids: Optional[List[str]] = None,
    ) -> Brain:
        brain = Brain(
            organization_id=organization_id,
            name=name,
            description=description,
        )
        db.add(brain)
        await db.flush()

        # Link Roles
        if role_ids:
            for r_id in role_ids:
                db.add(BrainRole(brain_id=brain.id, role_id=r_id))

        # Link Sources
        if source_ids:
            await db.execute(
                update(DataSource)
                .where(DataSource.id.in_(source_ids), DataSource.organization_id == organization_id)
                .values(brain_id=brain.id)
            )

        # Link Documents
        if document_ids:
            await db.execute(
                update(Document)
                .where(Document.id.in_(document_ids), Document.organization_id == organization_id)
                .values(brain_id=brain.id)
            )

        await db.commit()
        await db.refresh(brain)
        return brain

    @staticmethod
    async def update_brain_roles(
        db: AsyncSession,
        brain_id: str,
        role_ids: List[str]
    ) -> None:
        # Delete existing role links
        await db.execute(delete(BrainRole).where(BrainRole.brain_id == brain_id))
        # Insert updated role links
        for r_id in role_ids:
            db.add(BrainRole(brain_id=brain_id, role_id=r_id))
        await db.commit()
