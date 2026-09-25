import re
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.security import get_password_hash, verify_password, create_access_token, create_refresh_token, decode_token
from app.models import User, Organization, OrganizationUser, Role, AuditLog
from app.schemas.domain import UserRegisterRequest, UserLoginRequest, TokenResponse, UserResponse
from app.rbac.service import RBACService
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])

def slugify(text: str) -> str:
    s = text.lower().strip()
    s = re.sub(r'[^\w\s-]', '', s)
    return re.sub(r'[-\s]+', '-', s)

@router.post("/register", response_model=TokenResponse)
async def register(payload: UserRegisterRequest, db: AsyncSession = Depends(get_db)):
    # 1. Check if user already exists
    res = await db.execute(select(User).where(User.email == payload.email.lower()))
    if res.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User with this email already exists")

    # 2. Create User
    user = User(
        email=payload.email.lower(),
        password_hash=get_password_hash(payload.password),
        name=payload.name,
        is_active=True,
    )
    db.add(user)
    await db.flush()

    # 3. Create Organization
    base_slug = slugify(payload.organization_name)
    slug = base_slug
    counter = 1
    while True:
        s_res = await db.execute(select(Organization).where(Organization.slug == slug))
        if not s_res.scalar_one_or_none():
            break
        slug = f"{base_slug}-{counter}"
        counter += 1

    org = Organization(name=payload.organization_name, slug=slug)
    db.add(org)
    await db.flush()

    # 4. Initialize Organization Roles and System Permissions
    await RBACService.init_organization_roles(db, org.id)

    # 5. Fetch "Organization Admin" role and assign to user
    admin_role_res = await db.execute(
        select(Role).where(Role.organization_id == org.id, Role.name == "Organization Admin")
    )
    admin_role = admin_role_res.scalar_one_or_none()

    membership = OrganizationUser(
        organization_id=org.id,
        user_id=user.id,
        role_id=admin_role.id if admin_role else None,
        status="ACTIVE"
    )
    db.add(membership)

    # 6. Audit log
    audit = AuditLog(
        organization_id=org.id,
        user_id=user.id,
        action="USER_REGISTERED",
        resource_type="ORGANIZATION",
        resource_id=org.id,
        status="SUCCESS",
        metadata_json={"org_name": org.name}
    )
    db.add(audit)
    await db.commit()

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user={"id": user.id, "email": user.email, "name": user.name},
        organization={"id": org.id, "name": org.name, "slug": org.slug}
    )

@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLoginRequest, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(User).where(User.email == payload.email.lower()))
    user = res.scalar_one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    if not user.is_active:
        raise HTTPException(status_code=400, detail="Account is deactivated")

    # Fetch user's organization
    m_res = await db.execute(
        select(Organization)
        .join(OrganizationUser, OrganizationUser.organization_id == Organization.id)
        .where(OrganizationUser.user_id == user.id, OrganizationUser.status == "ACTIVE")
    )
    org = m_res.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=400, detail="User does not belong to any active organization")

    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)

    audit = AuditLog(
        organization_id=org.id,
        user_id=user.id,
        action="USER_LOGIN",
        resource_type="USER",
        resource_id=user.id,
        status="SUCCESS"
    )
    db.add(audit)
    await db.commit()

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user={"id": user.id, "email": user.email, "name": user.name},
        organization={"id": org.id, "name": org.name, "slug": org.slug}
    )

@router.get("/me")
async def get_me(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(
        select(Organization, Role.name)
        .join(OrganizationUser, OrganizationUser.organization_id == Organization.id)
        .outerjoin(Role, Role.id == OrganizationUser.role_id)
        .where(OrganizationUser.user_id == current_user.id)
    )
    orgs = [{"id": o.id, "name": o.name, "slug": o.slug, "role": rname} for o, rname in res.all()]

    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "is_superuser": current_user.is_superuser,
        "organizations": orgs
    }
