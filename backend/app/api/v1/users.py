from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from sqlalchemy.orm import selectinload
from typing import List
from app.db.session import get_db
from app.models.models import User, Role, Department, Team, Organization
from app.schemas.schemas import (
    UserResponse, UserUpdate, UserCreate,
    RoleResponse, RoleCreate, RoleUpdate,
    DepartmentResponse, DepartmentCreate, DepartmentUpdate,
    TeamResponse, TeamCreate, TeamUpdate,
    OrganizationResponse, OrganizationUpdate
)
from app.api.deps import get_current_user, get_current_superuser, get_user_organization
from app.core.security import get_password_hash

router = APIRouter()


# User routes
@router.get("/users/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user information."""
    result = await db.execute(
        select(User)
        .options(selectinload(User.roles))
        .where(User.id == current_user.id)
    )
    user = result.scalar_one()
    return user


@router.put("/users/me", response_model=UserResponse)
async def update_current_user(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update current user."""
    update_data = user_data.model_dump(exclude_unset=True)
    role_ids = update_data.pop("role_ids", None)
    
    for field, value in update_data.items():
        if field not in ["is_active", "is_superuser"]:  # Users can't change these
            setattr(current_user, field, value)
    
    await db.commit()
    await db.refresh(current_user)
    
    result = await db.execute(
        select(User)
        .options(selectinload(User.roles))
        .where(User.id == current_user.id)
    )
    user = result.scalar_one()
    return user


@router.get("/users", response_model=List[UserResponse])
async def list_users(
    current_user: User = Depends(get_current_superuser),
    organization: Organization = Depends(get_user_organization),
    db: AsyncSession = Depends(get_db)
):
    """List all users in organization (superuser only)."""
    result = await db.execute(
        select(User)
        .options(selectinload(User.roles))
        .where(User.organization_id == organization.id)
    )
    users = result.scalars().all()
    return users


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_current_superuser),
    organization: Organization = Depends(get_user_organization),
    db: AsyncSession = Depends(get_db)
):
    """Create new user in organization (superuser only)."""
    # Check if email exists
    result = await db.execute(select(User).where(User.email == user_data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    hashed_password = get_password_hash(user_data.password)
    user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        full_name=user_data.full_name,
        avatar_url=user_data.avatar_url,
        organization_id=organization.id,
        department_id=user_data.department_id,
        team_id=user_data.team_id
    )
    
    db.add(user)
    await db.flush()
    
    # Assign roles
    if user_data.role_ids:
        result = await db.execute(
            select(Role).where(
                and_(
                    Role.id.in_(user_data.role_ids),
                    Role.organization_id == organization.id
                )
            )
        )
        roles = result.scalars().all()
        user.roles = list(roles)
    
    await db.commit()
    await db.refresh(user)
    
    result = await db.execute(
        select(User)
        .options(selectinload(User.roles))
        .where(User.id == user.id)
    )
    user = result.scalar_one()
    return user


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_superuser),
    organization: Organization = Depends(get_user_organization),
    db: AsyncSession = Depends(get_db)
):
    """Update user (superuser only)."""
    result = await db.execute(
        select(User).where(
            and_(
                User.id == user_id,
                User.organization_id == organization.id
            )
        )
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    update_data = user_data.model_dump(exclude_unset=True)
    role_ids = update_data.pop("role_ids", None)
    
    for field, value in update_data.items():
        setattr(user, field, value)
    
    if role_ids is not None:
        result = await db.execute(
            select(Role).where(
                and_(
                    Role.id.in_(role_ids),
                    Role.organization_id == organization.id
                )
            )
        )
        roles = result.scalars().all()
        user.roles = list(roles)
    
    await db.commit()
    await db.refresh(user)
    
    result = await db.execute(
        select(User)
        .options(selectinload(User.roles))
        .where(User.id == user.id)
    )
    user = result.scalar_one()
    return user


# Role routes
@router.get("/roles", response_model=List[RoleResponse])
async def list_roles(
    organization: Organization = Depends(get_user_organization),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all roles in organization."""
    result = await db.execute(
        select(Role).where(Role.organization_id == organization.id)
    )
    roles = result.scalars().all()
    return roles


@router.post("/roles", response_model=RoleResponse, status_code=status.HTTP_201_CREATED)
async def create_role(
    role_data: RoleCreate,
    current_user: User = Depends(get_current_superuser),
    organization: Organization = Depends(get_user_organization),
    db: AsyncSession = Depends(get_db)
):
    """Create new role (superuser only)."""
    role = Role(
        name=role_data.name,
        description=role_data.description,
        permissions=role_data.permissions,
        organization_id=organization.id
    )
    db.add(role)
    await db.commit()
    await db.refresh(role)
    return role


@router.put("/roles/{role_id}", response_model=RoleResponse)
async def update_role(
    role_id: int,
    role_data: RoleUpdate,
    current_user: User = Depends(get_current_superuser),
    organization: Organization = Depends(get_user_organization),
    db: AsyncSession = Depends(get_db)
):
    """Update role (superuser only)."""
    result = await db.execute(
        select(Role).where(
            and_(
                Role.id == role_id,
                Role.organization_id == organization.id
            )
        )
    )
    role = result.scalar_one_or_none()
    
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    
    update_data = role_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(role, field, value)
    
    await db.commit()
    await db.refresh(role)
    return role


# Department routes
@router.get("/departments", response_model=List[DepartmentResponse])
async def list_departments(
    organization: Organization = Depends(get_user_organization),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all departments in organization."""
    result = await db.execute(
        select(Department).where(Department.organization_id == organization.id)
    )
    departments = result.scalars().all()
    return departments


@router.post("/departments", response_model=DepartmentResponse, status_code=status.HTTP_201_CREATED)
async def create_department(
    dept_data: DepartmentCreate,
    current_user: User = Depends(get_current_superuser),
    organization: Organization = Depends(get_user_organization),
    db: AsyncSession = Depends(get_db)
):
    """Create new department (superuser only)."""
    department = Department(
        name=dept_data.name,
        description=dept_data.description,
        organization_id=organization.id
    )
    db.add(department)
    await db.commit()
    await db.refresh(department)
    return department


# Team routes
@router.get("/teams", response_model=List[TeamResponse])
async def list_teams(
    organization: Organization = Depends(get_user_organization),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List all teams in organization."""
    result = await db.execute(
        select(Team).where(Team.organization_id == organization.id)
    )
    teams = result.scalars().all()
    return teams


@router.post("/teams", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_team(
    team_data: TeamCreate,
    current_user: User = Depends(get_current_superuser),
    organization: Organization = Depends(get_user_organization),
    db: AsyncSession = Depends(get_db)
):
    """Create new team (superuser only)."""
    team = Team(
        name=team_data.name,
        description=team_data.description,
        department_id=team_data.department_id,
        organization_id=organization.id
    )
    db.add(team)
    await db.commit()
    await db.refresh(team)
    return team


# Organization routes
@router.get("/organization", response_model=OrganizationResponse)
async def get_organization(
    organization: Organization = Depends(get_user_organization)
):
    """Get current organization."""
    return organization


@router.put("/organization", response_model=OrganizationResponse)
async def update_organization(
    org_data: OrganizationUpdate,
    current_user: User = Depends(get_current_superuser),
    organization: Organization = Depends(get_user_organization),
    db: AsyncSession = Depends(get_db)
):
    """Update organization (superuser only)."""
    update_data = org_data.model_dump(exclude_unset=True)
    
    for field, value in update_data.items():
        setattr(organization, field, value)
    
    await db.commit()
    await db.refresh(organization)
    return organization
