from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from sqlalchemy.orm import selectinload
from typing import List
from app.db.session import get_db
from app.models.models import Brain, User, Role, Department, Team, BrainVisibility
from app.schemas.schemas import BrainCreate, BrainUpdate, BrainResponse
from app.api.deps import get_current_user
from app.services.vector_store import vector_store

router = APIRouter()


async def check_brain_access(brain: Brain, user: User, db: AsyncSession) -> bool:
    """Check if user has access to brain."""
    # Owner always has access
    if brain.owner_id == user.id:
        return True
    
    # Superuser has access to all brains in organization
    if user.is_superuser and brain.organization_id == user.organization_id:
        return True
    
    # Check visibility settings
    if brain.visibility == BrainVisibility.ORGANIZATION:
        return brain.organization_id == user.organization_id
    
    elif brain.visibility == BrainVisibility.ROLE:
        # Load user roles
        result = await db.execute(
            select(User).options(selectinload(User.roles)).where(User.id == user.id)
        )
        user_with_roles = result.scalar_one()
        user_role_ids = [role.id for role in user_with_roles.roles]
        
        # Load brain roles
        result = await db.execute(
            select(Brain).options(selectinload(Brain.assigned_roles)).where(Brain.id == brain.id)
        )
        brain_with_roles = result.scalar_one()
        brain_role_ids = [role.id for role in brain_with_roles.assigned_roles]
        
        return any(role_id in brain_role_ids for role_id in user_role_ids)
    
    elif brain.visibility == BrainVisibility.DEPARTMENT:
        if user.department_id:
            result = await db.execute(
                select(Brain).options(selectinload(Brain.assigned_departments)).where(Brain.id == brain.id)
            )
            brain_with_depts = result.scalar_one()
            dept_ids = [dept.id for dept in brain_with_depts.assigned_departments]
            return user.department_id in dept_ids
    
    elif brain.visibility == BrainVisibility.TEAM:
        if user.team_id:
            result = await db.execute(
                select(Brain).options(selectinload(Brain.assigned_teams)).where(Brain.id == brain.id)
            )
            brain_with_teams = result.scalar_one()
            team_ids = [team.id for team in brain_with_teams.assigned_teams]
            return user.team_id in team_ids
    
    return False


@router.post("", response_model=BrainResponse, status_code=status.HTTP_201_CREATED)
async def create_brain(
    brain_data: BrainCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new brain."""
    brain = Brain(
        name=brain_data.name,
        description=brain_data.description,
        visibility=brain_data.visibility,
        settings=brain_data.settings,
        organization_id=current_user.organization_id,
        owner_id=current_user.id
    )
    
    db.add(brain)
    await db.flush()
    
    # Assign roles, departments, teams
    if brain_data.role_ids:
        result = await db.execute(
            select(Role).where(
                and_(
                    Role.id.in_(brain_data.role_ids),
                    Role.organization_id == current_user.organization_id
                )
            )
        )
        roles = result.scalars().all()
        brain.assigned_roles = list(roles)
    
    if brain_data.department_ids:
        result = await db.execute(
            select(Department).where(
                and_(
                    Department.id.in_(brain_data.department_ids),
                    Department.organization_id == current_user.organization_id
                )
            )
        )
        departments = result.scalars().all()
        brain.assigned_departments = list(departments)
    
    if brain_data.team_ids:
        result = await db.execute(
            select(Team).where(
                and_(
                    Team.id.in_(brain_data.team_ids),
                    Team.organization_id == current_user.organization_id
                )
            )
        )
        teams = result.scalars().all()
        brain.assigned_teams = list(teams)
    
    await db.commit()
    await db.refresh(brain)
    
    # Load relationships
    result = await db.execute(
        select(Brain)
        .options(
            selectinload(Brain.assigned_roles),
            selectinload(Brain.assigned_departments),
            selectinload(Brain.assigned_teams)
        )
        .where(Brain.id == brain.id)
    )
    brain = result.scalar_one()
    
    return brain


@router.get("", response_model=List[BrainResponse])
async def list_brains(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all brains accessible to current user."""
    # Get all brains in organization
    result = await db.execute(
        select(Brain)
        .options(
            selectinload(Brain.assigned_roles),
            selectinload(Brain.assigned_departments),
            selectinload(Brain.assigned_teams)
        )
        .where(
            and_(
                Brain.organization_id == current_user.organization_id,
                Brain.is_active == True
            )
        )
    )
    all_brains = result.scalars().all()
    
    # Filter based on access
    accessible_brains = []
    for brain in all_brains:
        if await check_brain_access(brain, current_user, db):
            accessible_brains.append(brain)
    
    return accessible_brains


@router.get("/{brain_id}", response_model=BrainResponse)
async def get_brain(
    brain_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get brain by ID."""
    result = await db.execute(
        select(Brain)
        .options(
            selectinload(Brain.assigned_roles),
            selectinload(Brain.assigned_departments),
            selectinload(Brain.assigned_teams)
        )
        .where(Brain.id == brain_id)
    )
    brain = result.scalar_one_or_none()
    
    if not brain:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brain not found"
        )
    
    if not await check_brain_access(brain, current_user, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    return brain


@router.put("/{brain_id}", response_model=BrainResponse)
async def update_brain(
    brain_id: int,
    brain_data: BrainUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update brain."""
    result = await db.execute(select(Brain).where(Brain.id == brain_id))
    brain = result.scalar_one_or_none()
    
    if not brain:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brain not found"
        )
    
    # Only owner or superuser can update
    if brain.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owner can update brain"
        )
    
    # Update fields
    update_data = brain_data.model_dump(exclude_unset=True)
    
    # Handle relationships separately
    role_ids = update_data.pop("role_ids", None)
    department_ids = update_data.pop("department_ids", None)
    team_ids = update_data.pop("team_ids", None)
    
    for field, value in update_data.items():
        setattr(brain, field, value)
    
    if role_ids is not None:
        result = await db.execute(
            select(Role).where(
                and_(
                    Role.id.in_(role_ids),
                    Role.organization_id == current_user.organization_id
                )
            )
        )
        roles = result.scalars().all()
        brain.assigned_roles = list(roles)
    
    if department_ids is not None:
        result = await db.execute(
            select(Department).where(
                and_(
                    Department.id.in_(department_ids),
                    Department.organization_id == current_user.organization_id
                )
            )
        )
        departments = result.scalars().all()
        brain.assigned_departments = list(departments)
    
    if team_ids is not None:
        result = await db.execute(
            select(Team).where(
                and_(
                    Team.id.in_(team_ids),
                    Team.organization_id == current_user.organization_id
                )
            )
        )
        teams = result.scalars().all()
        brain.assigned_teams = list(teams)
    
    await db.commit()
    await db.refresh(brain)
    
    # Load relationships
    result = await db.execute(
        select(Brain)
        .options(
            selectinload(Brain.assigned_roles),
            selectinload(Brain.assigned_departments),
            selectinload(Brain.assigned_teams)
        )
        .where(Brain.id == brain.id)
    )
    brain = result.scalar_one()
    
    return brain


@router.delete("/{brain_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_brain(
    brain_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete brain."""
    result = await db.execute(select(Brain).where(Brain.id == brain_id))
    brain = result.scalar_one_or_none()
    
    if not brain:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brain not found"
        )
    
    # Only owner or superuser can delete
    if brain.owner_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owner can delete brain"
        )
    
    # Delete vectors from vector store
    vector_store.delete_by_brain(brain_id)
    
    # Delete brain
    await db.delete(brain)
    await db.commit()
    
    return None
