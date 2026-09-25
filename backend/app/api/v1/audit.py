from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models import AuditLog, User
from app.schemas.domain import AuditLogResponse
from app.api.deps import get_current_user, get_current_organization_id, require_permission

router = APIRouter(prefix="/audit", tags=["Compliance & Audit Logs"])

@router.get("", dependencies=[Depends(require_permission("admin.audit"))])
async def list_audit_logs(
    action: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, le=200),
    org_id: str = Depends(get_current_organization_id),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(AuditLog).where(AuditLog.organization_id == org_id)
    if action:
        stmt = stmt.where(AuditLog.action == action)
    if status:
        stmt = stmt.where(AuditLog.status == status)

    stmt = stmt.order_by(AuditLog.created_at.desc()).limit(limit)
    res = await db.execute(stmt)
    logs = res.scalars().all()

    return [
        {
            "id": l.id,
            "action": l.action,
            "user_id": l.user_id,
            "resource_type": l.resource_type,
            "resource_id": l.resource_id,
            "status": l.status,
            "metadata": l.metadata_json or {},
            "created_at": l.created_at.isoformat()
        }
        for l in logs
    ]
