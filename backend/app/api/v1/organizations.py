"""
Organization API Endpoints
Handles organization and membership operations
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.organization import Organization
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationResponse,
    OrganizationWithRole,
    MemberResponse,
    MemberInvite,
    MembershipResponse
)
from app.services import organization_service
from app.services.user_service import get_user_by_email


router = APIRouter(prefix="/organizations", tags=["organizations"])


@router.get("", response_model=List[OrganizationWithRole])
async def list_user_organizations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all organizations the current user belongs to
    
    Returns list of organizations with user's role in each
    """
    orgs_with_roles = await organization_service.get_user_organizations(db, current_user.id)
    
    return [
        OrganizationWithRole(
            id=org.id,
            name=org.name,
            slug=org.slug,
            created_at=org.created_at,
            updated_at=org.updated_at,
            role=role
        )
        for org, role in orgs_with_roles
    ]


@router.post("", response_model=OrganizationResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    org_data: OrganizationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new organization
    
    The current user will be set as the owner
    """
    org = await organization_service.create_organization(db, org_data, current_user.id)
    return org


@router.get("/{org_id}", response_model=OrganizationWithRole)
async def get_organization(
    org_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get organization details
    
    User must be a member to view organization
    """
    # Check if user is a member
    role = await organization_service.get_user_role_in_org(db, current_user.id, org_id)
    if not role:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this organization"
        )
    
    # Get organization
    org = await organization_service.get_organization_by_id(db, org_id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    return OrganizationWithRole(
        id=org.id,
        name=org.name,
        slug=org.slug,
        created_at=org.created_at,
        updated_at=org.updated_at,
        role=role
    )


@router.patch("/{org_id}", response_model=OrganizationResponse)
async def update_organization(
    org_id: UUID,
    org_data: OrganizationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update organization details
    
    Only admins and owners can update
    """
    # Check if user is admin/owner
    is_admin = await organization_service.is_org_admin(db, current_user.id, org_id)
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and owners can update organization"
        )
    
    # Update organization
    org = await organization_service.update_organization(db, org_id, org_data)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    return org


@router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(
    org_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete organization
    
    Only owners can delete organizations
    """
    # Check if user is owner
    role = await organization_service.get_user_role_in_org(db, current_user.id, org_id)
    if role != "owner":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners can delete organization"
        )
    
    # Delete organization
    deleted = await organization_service.delete_organization(db, org_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    return None


@router.get("/{org_id}/members", response_model=List[MemberResponse])
async def list_organization_members(
    org_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all members of an organization
    
    User must be a member to view members
    """
    # Check if user is a member
    is_member = await organization_service.is_org_member(db, current_user.id, org_id)
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this organization"
        )
    
    # Get members
    members = await organization_service.get_organization_members(db, org_id)
    
    return [
        MemberResponse(
            id=membership.id,
            user_id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=membership.role.value,
            joined_at=membership.joined_at
        )
        for membership, user in members
    ]


@router.post("/{org_id}/members", response_model=MembershipResponse, status_code=status.HTTP_201_CREATED)
async def add_organization_member(
    org_id: UUID,
    invite_data: MemberInvite,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Invite a user to the organization
    
    Only admins and owners can invite members
    """
    # Check if user is admin/owner
    is_admin = await organization_service.is_org_admin(db, current_user.id, org_id)
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and owners can invite members"
        )
    
    # Check if organization exists
    org = await organization_service.get_organization_by_id(db, org_id)
    if not org:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found"
        )
    
    # Get user by email
    user = await get_user_by_email(db, invite_data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No user found with email {invite_data.email}"
        )
    
    # Add member
    try:
        membership = await organization_service.add_organization_member(
            db, org_id, user.id, invite_data.role
        )
        return membership
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/{org_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_organization_member(
    org_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Remove a member from the organization
    
    Admins and owners can remove members.
    Members can remove themselves.
    Cannot remove the last owner.
    """
    # Check permissions
    is_admin = await organization_service.is_org_admin(db, current_user.id, org_id)
    is_self = current_user.id == user_id
    
    if not (is_admin or is_self):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to remove this member"
        )
    
    # Remove member
    try:
        removed = await organization_service.remove_organization_member(db, org_id, user_id)
        if not removed:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Member not found in organization"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
    return None
