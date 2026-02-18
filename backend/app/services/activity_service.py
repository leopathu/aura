"""
Activity Log Service

Provides functions for querying, filtering, and managing activity logs.

TASK-296: Create activity log query functions
TASK-297: Add log filtering by date/type
TASK-298: Create log cleanup job (old logs)
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID

from app.models.activity_log import ActivityLog
from app.models.user import User
from app.models.agent import Agent


# ===== LOGGING FUNCTIONS (TASK-295) =====

async def log_activity(
    db: Session,
    org_id: UUID,
    action: str,
    details: Dict[str, Any],
    agent_id: Optional[UUID] = None,
    user_id: Optional[UUID] = None
) -> ActivityLog:
    """
    Log an activity
    
    Args:
        db: Database session
        org_id: Organization ID
        action: Action name (e.g., "agent.created", "message.sent")
        details: Additional details as JSON
        agent_id: Optional agent ID
        user_id: Optional user ID
    
    Returns:
        Created ActivityLog instance
    """
    activity = ActivityLog(
        org_id=org_id,
        agent_id=agent_id,
        user_id=user_id,
        action=action,
        details=details
    )
    
    db.add(activity)
    db.commit()
    db.refresh(activity)
    
    return activity


# ===== QUERY FUNCTIONS (TASK-296) =====

async def get_activity_logs(
    db: Session,
    org_id: UUID,
    limit: int = 100,
    offset: int = 0,
    agent_id: Optional[UUID] = None,
    user_id: Optional[UUID] = None,
    action: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    action_types: Optional[List[str]] = None
) -> List[ActivityLog]:
    """
    Query activity logs with filters
    
    TASK-296: Query functions
    TASK-297: Filtering by date/type
    
    Args:
        db: Database session
        org_id: Organization ID
        limit: Maximum number of results
        offset: Offset for pagination
        agent_id: Filter by agent ID
        user_id: Filter by user ID
        action: Filter by specific action
        start_date: Filter by start date
        end_date: Filter by end date
        action_types: Filter by action types (list of patterns)
    
    Returns:
        List of ActivityLog instances
    """
    query = db.query(ActivityLog).filter(ActivityLog.org_id == org_id)
    
    # Filter by agent
    if agent_id:
        query = query.filter(ActivityLog.agent_id == agent_id)
    
    # Filter by user
    if user_id:
        query = query.filter(ActivityLog.user_id == user_id)
    
    # Filter by specific action
    if action:
        query = query.filter(ActivityLog.action == action)
    
    # Filter by action types (pattern matching)
    if action_types:
        action_filters = [ActivityLog.action.like(f"{action_type}%") for action_type in action_types]
        query = query.filter(or_(*action_filters))
    
    # Filter by date range
    if start_date:
        query = query.filter(ActivityLog.created_at >= start_date)
    
    if end_date:
        query = query.filter(ActivityLog.created_at <= end_date)
    
    # Order by most recent first
    query = query.order_by(desc(ActivityLog.created_at))
    
    # Pagination
    query = query.limit(limit).offset(offset)
    
    return query.all()


async def get_activity_log_by_id(
    db: Session,
    activity_id: UUID,
    org_id: UUID
) -> Optional[ActivityLog]:
    """Get a single activity log by ID"""
    return db.query(ActivityLog).filter(
        ActivityLog.id == activity_id,
        ActivityLog.org_id == org_id
    ).first()


async def count_activity_logs(
    db: Session,
    org_id: UUID,
    agent_id: Optional[UUID] = None,
    user_id: Optional[UUID] = None,
    action: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    action_types: Optional[List[str]] = None
) -> int:
    """Count activity logs with filters"""
    query = db.query(ActivityLog).filter(ActivityLog.org_id == org_id)
    
    if agent_id:
        query = query.filter(ActivityLog.agent_id == agent_id)
    
    if user_id:
        query = query.filter(ActivityLog.user_id == user_id)
    
    if action:
        query = query.filter(ActivityLog.action == action)
    
    if action_types:
        action_filters = [ActivityLog.action.like(f"{action_type}%") for action_type in action_types]
        query = query.filter(or_(*action_filters))
    
    if start_date:
        query = query.filter(ActivityLog.created_at >= start_date)
    
    if end_date:
        query = query.filter(ActivityLog.created_at <= end_date)
    
    return query.count()


# ===== FILTERING HELPERS (TASK-297) =====

async def get_activity_logs_by_date_range(
    db: Session,
    org_id: UUID,
    start_date: datetime,
    end_date: datetime,
    limit: int = 100
) -> List[ActivityLog]:
    """Get activity logs within a date range"""
    return await get_activity_logs(
        db=db,
        org_id=org_id,
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )


async def get_activity_logs_by_action_type(
    db: Session,
    org_id: UUID,
    action_type: str,
    limit: int = 100
) -> List[ActivityLog]:
    """
    Get activity logs by action type prefix
    
    Example: action_type="agent" returns all logs with actions starting with "agent."
    """
    return await get_activity_logs(
        db=db,
        org_id=org_id,
        action_types=[action_type],
        limit=limit
    )


async def get_recent_activity_logs(
    db: Session,
    org_id: UUID,
    hours: int = 24,
    limit: int = 100
) -> List[ActivityLog]:
    """Get recent activity logs from the last N hours"""
    start_date = datetime.utcnow() - timedelta(hours=hours)
    return await get_activity_logs(
        db=db,
        org_id=org_id,
        start_date=start_date,
        limit=limit
    )


async def get_agent_activity_logs(
    db: Session,
    agent_id: UUID,
    org_id: UUID,
    limit: int = 100
) -> List[ActivityLog]:
    """Get all activity logs for a specific agent"""
    return await get_activity_logs(
        db=db,
        org_id=org_id,
        agent_id=agent_id,
        limit=limit
    )


async def get_user_activity_logs(
    db: Session,
    user_id: UUID,
    org_id: UUID,
    limit: int = 100
) -> List[ActivityLog]:
    """Get all activity logs for a specific user"""
    return await get_activity_logs(
        db=db,
        org_id=org_id,
        user_id=user_id,
        limit=limit
    )


# ===== STATISTICS =====

async def get_activity_statistics(
    db: Session,
    org_id: UUID,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Get activity statistics
    
    Returns:
        Dictionary with counts by action type
    """
    query = db.query(ActivityLog).filter(ActivityLog.org_id == org_id)
    
    if start_date:
        query = query.filter(ActivityLog.created_at >= start_date)
    
    if end_date:
        query = query.filter(ActivityLog.created_at <= end_date)
    
    logs = query.all()
    
    # Count by action prefix
    stats = {
        "total": len(logs),
        "by_type": {},
        "by_agent": {},
        "by_user": {}
    }
    
    for log in logs:
        # Extract action type (prefix before first dot)
        action_type = log.action.split('.')[0] if '.' in log.action else log.action
        stats["by_type"][action_type] = stats["by_type"].get(action_type, 0) + 1
        
        # Count by agent
        if log.agent_id:
            agent_id_str = str(log.agent_id)
            stats["by_agent"][agent_id_str] = stats["by_agent"].get(agent_id_str, 0) + 1
        
        # Count by user
        if log.user_id:
            user_id_str = str(log.user_id)
            stats["by_user"][user_id_str] = stats["by_user"].get(user_id_str, 0) + 1
    
    return stats


# ===== CLEANUP JOB (TASK-298) =====

async def cleanup_old_activity_logs(
    db: Session,
    org_id: UUID,
    days_to_keep: int = 90,
    dry_run: bool = False
) -> Dict[str, Any]:
    """
    Delete activity logs older than specified days
    
    TASK-298: Log cleanup job
    
    Args:
        db: Database session
        org_id: Organization ID
        days_to_keep: Number of days to keep (default: 90)
        dry_run: If True, only count without deleting
    
    Returns:
        Dictionary with cleanup results
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
    
    query = db.query(ActivityLog).filter(
        ActivityLog.org_id == org_id,
        ActivityLog.created_at < cutoff_date
    )
    
    count = query.count()
    
    if not dry_run and count > 0:
        query.delete(synchronize_session=False)
        db.commit()
    
    return {
        "org_id": str(org_id),
        "cutoff_date": cutoff_date.isoformat(),
        "deleted_count": count if not dry_run else 0,
        "would_delete_count": count if dry_run else 0,
        "dry_run": dry_run
    }


async def cleanup_all_old_activity_logs(
    db: Session,
    days_to_keep: int = 90,
    dry_run: bool = False
) -> List[Dict[str, Any]]:
    """
    Cleanup old activity logs for all organizations
    
    This should be run as a scheduled job (e.g., daily cron job)
    """
    from app.models.organization import Organization
    
    organizations = db.query(Organization).all()
    results = []
    
    for org in organizations:
        result = await cleanup_old_activity_logs(
            db=db,
            org_id=org.id,
            days_to_keep=days_to_keep,
            dry_run=dry_run
        )
        results.append(result)
    
    return results


# ===== EXPORT =====

async def export_activity_logs(
    db: Session,
    org_id: UUID,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    format: str = "json"
) -> List[Dict[str, Any]]:
    """
    Export activity logs to JSON format
    
    Args:
        db: Database session
        org_id: Organization ID
        start_date: Optional start date
        end_date: Optional end date
        format: Export format (json, csv)
    
    Returns:
        List of activity log dictionaries
    """
    logs = await get_activity_logs(
        db=db,
        org_id=org_id,
        start_date=start_date,
        end_date=end_date,
        limit=10000  # High limit for export
    )
    
    return [
        {
            "id": str(log.id),
            "org_id": str(log.org_id),
            "agent_id": str(log.agent_id) if log.agent_id else None,
            "user_id": str(log.user_id) if log.user_id else None,
            "action": log.action,
            "details": log.details,
            "created_at": log.created_at.isoformat()
        }
        for log in logs
    ]


# ===== COMMON LOGGING ACTIONS =====

class ActivityActions:
    """Common activity action names for consistency"""
    
    # Agent actions
    AGENT_CREATED = "agent.created"
    AGENT_UPDATED = "agent.updated"
    AGENT_DELETED = "agent.deleted"
    AGENT_EXECUTED = "agent.executed"
    
    # Message actions
    MESSAGE_SENT = "message.sent"
    MESSAGE_RECEIVED = "message.received"
    
    # Tool actions
    TOOL_EXECUTED = "tool.executed"
    TOOL_FAILED = "tool.failed"
    
    # Credential actions
    CREDENTIAL_CREATED = "credential.created"
    CREDENTIAL_UPDATED = "credential.updated"
    CREDENTIAL_DELETED = "credential.deleted"
    
    # Integration actions
    INTEGRATION_CONNECTED = "integration.connected"
    INTEGRATION_DISCONNECTED = "integration.disconnected"
    
    # User actions
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_INVITED = "user.invited"
    
    # Organization actions
    ORG_CREATED = "org.created"
    ORG_UPDATED = "org.updated"
    
    # Approval actions
    APPROVAL_REQUESTED = "approval.requested"
    APPROVAL_APPROVED = "approval.approved"
    APPROVAL_REJECTED = "approval.rejected"
    APPROVAL_TIMEOUT = "approval.timeout"


# Export all functions
__all__ = [
    "log_activity",
    "get_activity_logs",
    "get_activity_log_by_id",
    "count_activity_logs",
    "get_activity_logs_by_date_range",
    "get_activity_logs_by_action_type",
    "get_recent_activity_logs",
    "get_agent_activity_logs",
    "get_user_activity_logs",
    "get_activity_statistics",
    "cleanup_old_activity_logs",
    "cleanup_all_old_activity_logs",
    "export_activity_logs",
    "ActivityActions"
]
