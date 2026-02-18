"""
Activity Log API Endpoints

Provides REST API for querying and exporting activity logs.

TASK-296: Activity log query endpoints
TASK-297: Filtering by date/type
TASK-309: Export functionality
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from uuid import UUID
import csv
import io

from app.database import get_db
from app.models.user import User
from app.services.auth_service import get_current_user
from app.services import activity_service
from pydantic import BaseModel


router = APIRouter(prefix="/activity", tags=["activity"])


# ===== SCHEMAS =====

class ActivityLogResponse(BaseModel):
    id: str
    org_id: str
    agent_id: Optional[str]
    user_id: Optional[str]
    action: str
    details: dict
    created_at: datetime
    
    class Config:
        from_attributes = True


class ActivityLogsResponse(BaseModel):
    logs: List[ActivityLogResponse]
    total: int
    limit: int
    offset: int


class ActivityStatsResponse(BaseModel):
    total: int
    by_type: dict
    by_agent: dict
    by_user: dict


# ===== ENDPOINTS =====

@router.get("/logs", response_model=ActivityLogsResponse)
async def get_activity_logs(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    agent_id: Optional[UUID] = None,
    user_id: Optional[UUID] = None,
    action: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    action_types: Optional[str] = Query(None, description="Comma-separated action type prefixes"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get activity logs with filters
    
    TASK-296: Query activity logs
    TASK-297: Filter by date/type
    """
    # Parse action types
    action_types_list = None
    if action_types:
        action_types_list = [t.strip() for t in action_types.split(',')]
    
    # Get logs
    logs = await activity_service.get_activity_logs(
        db=db,
        org_id=current_user.org_id,
        limit=limit,
        offset=offset,
        agent_id=agent_id,
        user_id=user_id,
        action=action,
        start_date=start_date,
        end_date=end_date,
        action_types=action_types_list
    )
    
    # Get total count
    total = await activity_service.count_activity_logs(
        db=db,
        org_id=current_user.org_id,
        agent_id=agent_id,
        user_id=user_id,
        action=action,
        start_date=start_date,
        end_date=end_date,
        action_types=action_types_list
    )
    
    return ActivityLogsResponse(
        logs=[ActivityLogResponse.from_orm(log) for log in logs],
        total=total,
        limit=limit,
        offset=offset
    )


@router.get("/logs/{activity_id}", response_model=ActivityLogResponse)
async def get_activity_log(
    activity_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a single activity log by ID"""
    log = await activity_service.get_activity_log_by_id(
        db=db,
        activity_id=activity_id,
        org_id=current_user.org_id
    )
    
    if not log:
        raise HTTPException(status_code=404, detail="Activity log not found")
    
    return ActivityLogResponse.from_orm(log)


@router.get("/stats", response_model=ActivityStatsResponse)
async def get_activity_statistics(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get activity statistics"""
    stats = await activity_service.get_activity_statistics(
        db=db,
        org_id=current_user.org_id,
        start_date=start_date,
        end_date=end_date
    )
    
    return ActivityStatsResponse(**stats)


@router.get("/export")
async def export_activity_logs(
    format: str = Query("json", regex="^(json|csv)$"),
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    action_types: Optional[str] = Query(None),
    agent_id: Optional[UUID] = None,
    user_id: Optional[UUID] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Export activity logs
    
    TASK-309: Export functionality
    """
    # Parse action types
    action_types_list = None
    if action_types:
        action_types_list = [t.strip() for t in action_types.split(',')]
    
    # Get logs
    logs = await activity_service.get_activity_logs(
        db=db,
        org_id=current_user.org_id,
        limit=10000,  # High limit for export
        offset=0,
        agent_id=agent_id,
        user_id=user_id,
        start_date=start_date,
        end_date=end_date,
        action_types=action_types_list
    )
    
    if format == "json":
        # Export as JSON
        from fastapi.responses import JSONResponse
        
        data = await activity_service.export_activity_logs(
            db=db,
            org_id=current_user.org_id,
            start_date=start_date,
            end_date=end_date,
            format="json"
        )
        
        return JSONResponse(content=data)
    
    elif format == "csv":
        # Export as CSV
        from fastapi.responses import StreamingResponse
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow([
            "ID",
            "Organization ID",
            "Agent ID",
            "User ID",
            "Action",
            "Details",
            "Created At"
        ])
        
        # Write rows
        for log in logs:
            writer.writerow([
                str(log.id),
                str(log.org_id),
                str(log.agent_id) if log.agent_id else "",
                str(log.user_id) if log.user_id else "",
                log.action,
                str(log.details),
                log.created_at.isoformat()
            ])
        
        output.seek(0)
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename=activity-logs-{datetime.utcnow().strftime('%Y%m%d')}.csv"
            }
        )


@router.get("/recent")
async def get_recent_activity(
    hours: int = Query(24, ge=1, le=168),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get recent activity logs"""
    logs = await activity_service.get_recent_activity_logs(
        db=db,
        org_id=current_user.org_id,
        hours=hours,
        limit=limit
    )
    
    return [ActivityLogResponse.from_orm(log) for log in logs]


@router.get("/agent/{agent_id}")
async def get_agent_activity(
    agent_id: UUID,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get activity logs for a specific agent"""
    logs = await activity_service.get_agent_activity_logs(
        db=db,
        agent_id=agent_id,
        org_id=current_user.org_id,
        limit=limit
    )
    
    return [ActivityLogResponse.from_orm(log) for log in logs]


@router.get("/user/{user_id}")
async def get_user_activity(
    user_id: UUID,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get activity logs for a specific user"""
    logs = await activity_service.get_user_activity_logs(
        db=db,
        user_id=user_id,
        org_id=current_user.org_id,
        limit=limit
    )
    
    return [ActivityLogResponse.from_orm(log) for log in logs]
