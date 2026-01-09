from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models.user import User
from app.db.models.organization import Organization, Membership, MemberRole
from app.schemas.organization import (
    OrganizationCreate, OrganizationResponse, OrganizationUpdate,
    MembershipCreate, MembershipResponse, OrganizationWithRole
)
from app.api.dependencies import get_current_user, require_org_admin
from typing import List
from uuid import UUID

router = APIRouter()

@router.post("/", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    org_data: OrganizationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new organization."""
    # Check if slug is unique
    existing = db.query(Organization).filter(Organization.slug == org_data.slug).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization slug already exists"
        )
    
    # Create organization
    org = Organization(**org_data.dict())
    db.add(org)
    db.flush()
    
    # Add creator as owner
    membership = Membership(
        user_id=current_user.id,
        org_id=org.id,
        role=MemberRole.OWNER
    )
    db.add(membership)
    db.commit()
    db.refresh(org)
    
    return org

@router.get("/", response_model=List[OrganizationWithRole])
async def list_organizations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all organizations the user belongs to."""
    memberships = db.query(Membership).filter(
        Membership.user_id == current_user.id
    ).all()
    
    result = []
    for membership in memberships:
        org = db.query(Organization).filter(Organization.id == membership.org_id).first()
        if org:
            org_dict = {
                "id": org.id,
                "name": org.name,
                "slug": org.slug,
                "description": org.description,
                "created_at": org.created_at,
                "updated_at": org.updated_at,
                "role": membership.role
            }
            result.append(org_dict)
    
    return result

@router.get("/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get organization details."""
    # Verify access
    membership = db.query(Membership).filter(
        Membership.user_id == current_user.id,
        Membership.org_id == org_id
    ).first()
    
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    return org

@router.post("/{org_id}/members", response_model=MembershipResponse)
async def add_member(
    org_id: UUID,
    member_data: MembershipCreate,
    membership: Membership = Depends(require_org_admin),
    db: Session = Depends(get_db)
):
    """Add a member to organization (admin only)."""
    # Find user by email
    user = db.query(User).filter(User.email == member_data.user_email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if already a member
    existing = db.query(Membership).filter(
        Membership.user_id == user.id,
        Membership.org_id == org_id
    ).first()
    
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is already a member"
        )
    
    # Add membership
    new_membership = Membership(
        user_id=user.id,
        org_id=org_id,
        role=member_data.role
    )
    db.add(new_membership)
    db.commit()
    db.refresh(new_membership)
    
    return new_membership

@router.get("/{org_id}/members", response_model=List[MembershipResponse])
async def list_members(
    org_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all members of an organization."""
    # Verify access
    membership = db.query(Membership).filter(
        Membership.user_id == current_user.id,
        Membership.org_id == org_id
    ).first()
    
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    members = db.query(Membership).filter(Membership.org_id == org_id).all()
    return members
