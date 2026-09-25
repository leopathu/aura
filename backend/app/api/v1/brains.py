from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models import Brain, BrainRole, DataSource, Document, Role, User, AuditLog
from app.schemas.domain import (
    BrainCreate,
    BrainResponse,
    AssignBrainRolesRequest,
    ConnectBrainResourcesRequest,
)
from app.api.deps import get_current_user, get_current_organization_id, require_permission
from app.brains.service import BrainService

router = APIRouter(prefix="/brains", tags=["Brains & Knowledge Scoping"])

@router.get("", response_model=List[BrainResponse])
async def list_brains(
    org_id: str = Depends(get_current_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns brains accessible by the current user based on their assigned role.
    Organization Admins and Superusers have access to all brains.
    """
    accessible_ids = await BrainService.get_user_accessible_brain_ids(db, current_user.id, org_id)

    stmt = select(Brain).where(Brain.organization_id == org_id)
    if accessible_ids is not None:
        stmt = stmt.where(Brain.id.in_(accessible_ids))

    res = await db.execute(stmt)
    brains = res.scalars().all()

    output = []
    for b in brains:
        # Count connected sources
        src_cnt = await db.scalar(
            select(func.count(DataSource.id)).where(DataSource.brain_id == b.id)
        )
        # Count connected documents
        doc_cnt = await db.scalar(
            select(func.count(Document.id)).where(Document.brain_id == b.id)
        )
        # Fetch assigned role names
        r_stmt = (
            select(Role.name)
            .join(BrainRole, BrainRole.role_id == Role.id)
            .where(BrainRole.brain_id == b.id)
        )
        r_res = await db.execute(r_stmt)
        role_names = r_res.scalars().all()

        output.append(
            BrainResponse(
                id=b.id,
                organization_id=b.organization_id,
                name=b.name,
                description=b.description,
                created_at=b.created_at,
                sources_count=src_cnt or 0,
                documents_count=doc_cnt or 0,
                assigned_roles=list(role_names)
            )
        )
    return output

@router.post("", dependencies=[Depends(require_permission("brain.create"))])
async def create_brain(
    payload: BrainCreate,
    org_id: str = Depends(get_current_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    brain = await BrainService.create_brain(
        db=db,
        organization_id=org_id,
        name=payload.name,
        description=payload.description,
        role_ids=payload.role_ids,
        source_ids=payload.source_ids,
        document_ids=payload.document_ids,
    )

    audit = AuditLog(
        organization_id=org_id,
        user_id=current_user.id,
        action="BRAIN_CREATED",
        resource_type="BRAIN",
        resource_id=brain.id,
        status="SUCCESS",
        metadata_json={"brain_name": brain.name}
    )
    db.add(audit)
    await db.commit()

    return {"id": brain.id, "name": brain.name, "message": "Brain created successfully"}

@router.get("/{id}")
async def get_brain_details(
    id: str,
    org_id: str = Depends(get_current_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify access
    accessible_ids = await BrainService.get_user_accessible_brain_ids(db, current_user.id, org_id)
    if accessible_ids is not None and id not in accessible_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your assigned role does not have permission to access this Brain"
        )

    res = await db.execute(select(Brain).where(Brain.id == id, Brain.organization_id == org_id))
    brain = res.scalar_one_or_none()
    if not brain:
        raise HTTPException(status_code=404, detail="Brain not found")

    # Sources
    s_res = await db.execute(select(DataSource).where(DataSource.brain_id == brain.id))
    sources = s_res.scalars().all()

    # Documents
    d_res = await db.execute(select(Document).where(Document.brain_id == brain.id))
    documents = d_res.scalars().all()

    # Roles
    r_stmt = (
        select(Role)
        .join(BrainRole, BrainRole.role_id == Role.id)
        .where(BrainRole.brain_id == brain.id)
    )
    r_res = await db.execute(r_stmt)
    roles = r_res.scalars().all()

    return {
        "id": brain.id,
        "name": brain.name,
        "description": brain.description,
        "created_at": brain.created_at.isoformat(),
        "sources": [
            {
                "id": s.id,
                "name": s.name,
                "type": s.type,
                "description": s.description,
                "is_active": s.is_active,
                "is_read_only": s.is_read_only,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in sources
        ],
        "documents": [
            {
                "id": d.id,
                "title": d.title,
                "file_name": d.file_name,
                "file_type": d.file_type,
                "file_size": d.file_size,
                "status": d.status,
                "chunk_count": d.chunk_count,
                "created_at": d.created_at.isoformat() if d.created_at else None,
            }
            for d in documents
        ],
        "roles": [
            {"id": r.id, "name": r.name, "description": r.description, "is_system": r.is_system}
            for r in roles
        ]
    }

@router.put("/{id}", dependencies=[Depends(require_permission("brain.update"))])
async def update_brain(
    id: str,
    payload: BrainCreate,
    org_id: str = Depends(get_current_organization_id),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(Brain).where(Brain.id == id, Brain.organization_id == org_id))
    brain = res.scalar_one_or_none()
    if not brain:
        raise HTTPException(status_code=404, detail="Brain not found")

    brain.name = payload.name
    brain.description = payload.description
    await db.commit()
    return {"status": "success", "message": "Brain updated"}

@router.post("/{id}/assign-roles", dependencies=[Depends(require_permission("brain.update"))])
async def assign_brain_roles(
    id: str,
    payload: AssignBrainRolesRequest,
    org_id: str = Depends(get_current_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(Brain).where(Brain.id == id, Brain.organization_id == org_id))
    brain = res.scalar_one_or_none()
    if not brain:
        raise HTTPException(status_code=404, detail="Brain not found")

    await BrainService.update_brain_roles(db, brain.id, payload.role_ids)

    audit = AuditLog(
        organization_id=org_id,
        user_id=current_user.id,
        action="BRAIN_ROLES_ASSIGNED",
        resource_type="BRAIN",
        resource_id=brain.id,
        status="SUCCESS",
        metadata_json={"role_ids": payload.role_ids}
    )
    db.add(audit)
    await db.commit()

    return {"status": "success", "message": "Brain roles updated"}

@router.post("/{id}/connect-resources", dependencies=[Depends(require_permission("brain.update"))])
async def connect_brain_resources(
    id: str,
    payload: ConnectBrainResourcesRequest,
    org_id: str = Depends(get_current_organization_id),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(Brain).where(Brain.id == id, Brain.organization_id == org_id))
    brain = res.scalar_one_or_none()
    if not brain:
        raise HTTPException(status_code=404, detail="Brain not found")

    if payload.source_ids is not None:
        await db.execute(
            update(DataSource)
            .where(DataSource.id.in_(payload.source_ids), DataSource.organization_id == org_id)
            .values(brain_id=brain.id)
        )

    if payload.document_ids is not None:
        await db.execute(
            update(Document)
            .where(Document.id.in_(payload.document_ids), Document.organization_id == org_id)
            .values(brain_id=brain.id)
        )

    await db.commit()
    return {"status": "success", "message": "Resources attached to Brain"}

@router.delete("/{id}", dependencies=[Depends(require_permission("brain.delete"))])
async def delete_brain(
    id: str,
    org_id: str = Depends(get_current_organization_id),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(Brain).where(Brain.id == id, Brain.organization_id == org_id))
    brain = res.scalar_one_or_none()
    if not brain:
        raise HTTPException(status_code=404, detail="Brain not found")

    await db.delete(brain)
    await db.commit()
    return {"status": "success", "message": "Brain removed"}

@router.post("/{id}/sources/{source_id}/detach", dependencies=[Depends(require_permission("brain.update"))])
async def detach_source(
    id: str,
    source_id: str,
    org_id: str = Depends(get_current_organization_id),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(
        select(DataSource).where(
            DataSource.id == source_id,
            DataSource.brain_id == id,
            DataSource.organization_id == org_id
        )
    )
    source = res.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=404, detail="Data source not found in this brain")
    source.brain_id = None
    await db.commit()
    return {"status": "success", "message": f"Data source '{source.name}' detached from brain"}

@router.post("/{id}/documents/{doc_id}/detach", dependencies=[Depends(require_permission("brain.update"))])
async def detach_document(
    id: str,
    doc_id: str,
    org_id: str = Depends(get_current_organization_id),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(
        select(Document).where(
            Document.id == doc_id,
            Document.brain_id == id,
            Document.organization_id == org_id
        )
    )
    doc = res.scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found in this brain")
    doc.brain_id = None
    await db.commit()
    return {"status": "success", "message": f"Document '{doc.title}' detached from brain"}
