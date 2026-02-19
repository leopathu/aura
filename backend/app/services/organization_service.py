"""
Organization Service
Business logic for organization and membership management
"""

from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_, or_, select
from typing import List, Optional
from uuid import UUID
import re

from app.models.organization import Organization, Membership, MemberRole
from app.models.user import User
from app.schemas.organization import OrganizationCreate, OrganizationUpdate


def generate_slug(name: str) -> str:
    """
    Generate URL-friendly slug from organization name
    
    Args:
        name: Organization name
        
    Returns:
        URL-friendly slug
    """
    # Convert to lowercase and replace spaces with hyphens
    slug = name.lower().strip()
    # Remove special characters, keep only alphanumeric and hyphens
    slug = re.sub(r'[^a-z0-9-]', '-', slug)
    # Remove multiple consecutive hyphens
    slug = re.sub(r'-+', '-', slug)
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    return slug


def ensure_unique_slug(db: Session, base_slug: str, org_id: Optional[UUID] = None) -> str:
    """
    Ensure slug is unique by appending number if necessary
    
    Args:
        db: Database session
        base_slug: Base slug to make unique
        org_id: Organization ID to exclude from uniqueness check (for updates)
        
    Returns:
        Unique slug
    """
    slug = base_slug
    counter = 1
    
    while True:
        query = db.query(Organization).filter(Organization.slug == slug)
        if org_id:
            query = query.filter(Organization.id != org_id)
        
        if not query.first():
            return slug
        
        slug = f"{base_slug}-{counter}"
        counter += 1


async def create_organization(
    db: Session,
    org_data: OrganizationCreate,
    owner_id: UUID
) -> Organization:
    """
    Create a new organization with the creator as owner
    
    Args:
        db: Database session
        org_data: Organization creation data
        owner_id: User ID who will be the owner
        
    Returns:
        Created organization
    """
    # Generate unique slug
    base_slug = generate_slug(org_data.name)
    unique_slug = ensure_unique_slug(db, base_slug)
    
    # Create organization
    org = Organization(
        name=org_data.name,
        slug=unique_slug
    )
    db.add(org)
    db.flush()  # Get org.id without committing
    
    # Create owner membership
    membership = Membership(
        user_id=owner_id,
        org_id=org.id,
        role=MemberRole.OWNER
    )
    db.add(membership)
    db.commit()
    db.refresh(org)
    
    return org


async def get_organization_by_id(db: Session, org_id: UUID) -> Optional[Organization]:
    """
    Get organization by ID
    
    Args:
        db: Database session
        org_id: Organization ID
        
    Returns:
        Organization or None
    """
    return db.query(Organization).filter(Organization.id == org_id).first()


async def get_organization_by_slug(db: Session, slug: str) -> Optional[Organization]:
    """
    Get organization by slug
    
    Args:
        db: Database session
        slug: Organization slug
        
    Returns:
        Organization or None
    """
    return db.query(Organization).filter(Organization.slug == slug).first()


async def get_user_organizations(db: AsyncSession, user_id: UUID) -> List[tuple[Organization, str]]:
    """
    Get all organizations a user belongs to with their role
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        List of (Organization, role) tuples
    """
    stmt = (
        select(Organization, Membership.role)
        .join(Membership, Membership.org_id == Organization.id)
        .filter(Membership.user_id == user_id)
        .order_by(Organization.created_at.desc())
    )
    
    result = await db.execute(stmt)
    results = result.all()
    
    return [(org, role.value) for org, role in results]


async def update_organization(
    db: Session,
    org_id: UUID,
    org_data: OrganizationUpdate
) -> Optional[Organization]:
    """
    Update organization details
    
    Args:
        db: Database session
        org_id: Organization ID
        org_data: Update data
        
    Returns:
        Updated organization or None
    """
    org = await get_organization_by_id(db, org_id)
    if not org:
        return None
    
    # Update name and regenerate slug if name changed
    if org_data.name is not None:
        org.name = org_data.name
        base_slug = generate_slug(org_data.name)
        org.slug = ensure_unique_slug(db, base_slug, org_id)
    
    db.commit()
    db.refresh(org)
    return org


async def delete_organization(db: Session, org_id: UUID) -> bool:
    """
    Delete organization (cascades to memberships)
    
    Args:
        db: Database session
        org_id: Organization ID
        
    Returns:
        True if deleted, False if not found
    """
    org = await get_organization_by_id(db, org_id)
    if not org:
        return False
    
    db.delete(org)
    db.commit()
    return True


async def get_user_role_in_org(db: Session, user_id: UUID, org_id: UUID) -> Optional[str]:
    """
    Get user's role in an organization
    
    Args:
        db: Database session
        user_id: User ID
        org_id: Organization ID
        
    Returns:
        Role string or None if not a member
    """
    membership = (
        db.query(Membership)
        .filter(
            and_(
                Membership.user_id == user_id,
                Membership.org_id == org_id
            )
        )
        .first()
    )
    
    return membership.role.value if membership else None


async def is_org_member(db: Session, user_id: UUID, org_id: UUID) -> bool:
    """
    Check if user is a member of organization
    
    Args:
        db: Database session
        user_id: User ID
        org_id: Organization ID
        
    Returns:
        True if member, False otherwise
    """
    return await get_user_role_in_org(db, user_id, org_id) is not None


async def is_org_admin(db: Session, user_id: UUID, org_id: UUID) -> bool:
    """
    Check if user is an admin or owner of organization
    
    Args:
        db: Database session
        user_id: User ID
        org_id: Organization ID
        
    Returns:
        True if admin/owner, False otherwise
    """
    role = await get_user_role_in_org(db, user_id, org_id)
    return role in [MemberRole.ADMIN.value, MemberRole.OWNER.value] if role else False


async def get_organization_members(db: Session, org_id: UUID) -> List[tuple[Membership, User]]:
    """
    Get all members of an organization with user details
    
    Args:
        db: Database session
        org_id: Organization ID
        
    Returns:
        List of (Membership, User) tuples
    """
    results = (
        db.query(Membership, User)
        .join(User, User.id == Membership.user_id)
        .filter(Membership.org_id == org_id)
        .order_by(Membership.joined_at.asc())
        .all()
    )
    
    return results


async def add_organization_member(
    db: Session,
    org_id: UUID,
    user_id: UUID,
    role: str = "member"
) -> Membership:
    """
    Add a user to an organization
    
    Args:
        db: Database session
        org_id: Organization ID
        user_id: User ID to add
        role: Member role (default: member)
        
    Returns:
        Created membership
    """
    # Check if already a member
    existing = (
        db.query(Membership)
        .filter(
            and_(
                Membership.user_id == user_id,
                Membership.org_id == org_id
            )
        )
        .first()
    )
    
    if existing:
        raise ValueError("User is already a member of this organization")
    
    # Create membership
    membership = Membership(
        user_id=user_id,
        org_id=org_id,
        role=MemberRole(role)
    )
    db.add(membership)
    db.commit()
    db.refresh(membership)
    
    return membership


async def remove_organization_member(
    db: Session,
    org_id: UUID,
    user_id: UUID
) -> bool:
    """
    Remove a user from an organization
    
    Args:
        db: Database session
        org_id: Organization ID
        user_id: User ID to remove
        
    Returns:
        True if removed, False if not found
    """
    membership = (
        db.query(Membership)
        .filter(
            and_(
                Membership.user_id == user_id,
                Membership.org_id == org_id
            )
        )
        .first()
    )
    
    if not membership:
        return False
    
    # Don't allow removing the last owner
    if membership.role == MemberRole.OWNER:
        owner_count = (
            db.query(Membership)
            .filter(
                and_(
                    Membership.org_id == org_id,
                    Membership.role == MemberRole.OWNER
                )
            )
            .count()
        )
        
        if owner_count <= 1:
            raise ValueError("Cannot remove the last owner of the organization")
    
    db.delete(membership)
    db.commit()
    return True


async def update_member_role(
    db: Session,
    org_id: UUID,
    user_id: UUID,
    new_role: str
) -> Optional[Membership]:
    """
    Update a member's role in an organization
    
    Args:
        db: Database session
        org_id: Organization ID
        user_id: User ID
        new_role: New role to assign
        
    Returns:
        Updated membership or None
    """
    membership = (
        db.query(Membership)
        .filter(
            and_(
                Membership.user_id == user_id,
                Membership.org_id == org_id
            )
        )
        .first()
    )
    
    if not membership:
        return None
    
    # Don't allow changing the last owner
    if membership.role == MemberRole.OWNER and new_role != MemberRole.OWNER.value:
        owner_count = (
            db.query(Membership)
            .filter(
                and_(
                    Membership.org_id == org_id,
                    Membership.role == MemberRole.OWNER
                )
            )
            .count()
        )
        
        if owner_count <= 1:
            raise ValueError("Cannot change role of the last owner")
    
    membership.role = MemberRole(new_role)
    db.commit()
    db.refresh(membership)
    
    return membership
