"""
Automation API Endpoints

TASK-339: Create /automations GET endpoint
TASK-340: Create /automations POST endpoint
TASK-341: Create /automations/{id} GET endpoint
TASK-342: Create /automations/{id} PATCH endpoint
TASK-343: Create /automations/{id} DELETE endpoint
TASK-344: Create /automations/{id}/runs GET endpoint
TASK-345: Create /automations/{id}/test POST endpoint
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Header
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid
import json

from app.db.session import get_db
from app.models.user import User
from app.models.automation import (
    Automation, 
    AutomationRun, 
    TriggerType, 
    AutomationStatus,
    RunStatus
)
from app.auth import get_current_user
from app.services.schedule_service import (
    calculate_next_run,
    validate_cron_expression,
    test_schedule,
    validate_timezone
)
from app.services.trigger_service import (
    TriggerConditionEvaluator,
    WebhookAuthenticator,
    TriggerLogger,
    trigger_event
)
from app.tasks.automation_tasks import execute_automation, cancel_automation_run


router = APIRouter(prefix="/api/v1/automations", tags=["automations"])


# ==================== Pydantic Schemas ====================

class WorkflowStepSchema(BaseModel):
    """Workflow step schema"""
    type: str = Field(..., description="Step type (agent_task, http_request, condition, etc.)")
    config: Dict[str, Any] = Field(default_factory=dict, description="Step configuration")


class TriggerConfigSchema(BaseModel):
    """Trigger configuration schema"""
    event_type: Optional[str] = Field(None, description="Event type for EVENT triggers")
    conditions: Optional[List[Dict[str, Any]]] = Field(None, description="Trigger conditions")
    logic: Optional[str] = Field("AND", description="Condition logic (AND/OR)")
    webhook_secret: Optional[str] = Field(None, description="Webhook secret for authentication")
    auth_type: Optional[str] = Field("none", description="Auth type (none, signature, api_key)")


class AutomationCreateSchema(BaseModel):
    """Schema for creating automation"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    workflow: Dict[str, Any] = Field(..., description="Workflow definition (JSON)")
    trigger_type: TriggerType
    schedule: Optional[str] = Field(None, description="Cron expression for SCHEDULE triggers")
    trigger_config: Optional[TriggerConfigSchema] = None
    timezone: Optional[str] = Field("UTC", description="Timezone for scheduled runs")
    agent_id: Optional[uuid.UUID] = None
    enabled: bool = Field(True, description="Whether automation is enabled")


class AutomationUpdateSchema(BaseModel):
    """Schema for updating automation"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    workflow: Optional[Dict[str, Any]] = None
    schedule: Optional[str] = None
    trigger_config: Optional[TriggerConfigSchema] = None
    timezone: Optional[str] = None
    enabled: Optional[bool] = None
    status: Optional[AutomationStatus] = None


class AutomationResponse(BaseModel):
    """Automation response schema"""
    id: uuid.UUID
    org_id: uuid.UUID
    name: str
    description: Optional[str]
    status: AutomationStatus
    trigger_type: TriggerType
    schedule: Optional[str]
    timezone: str
    workflow: Dict[str, Any]
    trigger_config: Optional[Dict[str, Any]]
    agent_id: Optional[uuid.UUID]
    last_run_at: Optional[datetime]
    last_run_status: Optional[RunStatus]
    next_run_at: Optional[datetime]
    run_count: int
    success_count: int
    failure_count: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AutomationRunResponse(BaseModel):
    """Automation run response schema"""
    id: uuid.UUID
    automation_id: uuid.UUID
    status: RunStatus
    trigger_type: TriggerType
    trigger_data: Optional[Dict[str, Any]]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    current_step: int
    total_steps: int
    context: Optional[Dict[str, Any]]
    result: Optional[Dict[str, Any]]
    error: Optional[str]
    logs: List[Dict[str, Any]]
    duration_seconds: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


class TestAutomationRequest(BaseModel):
    """Test automation request"""
    trigger_data: Optional[Dict[str, Any]] = Field(default_factory=dict)


class WebhookTriggerRequest(BaseModel):
    """Webhook trigger request"""
    event_type: str
    event_data: Dict[str, Any] = Field(default_factory=dict)


# ==================== Endpoints ====================

@router.get("", response_model=List[AutomationResponse])
async def list_automations(
    status: Optional[AutomationStatus] = None,
    trigger_type: Optional[TriggerType] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List automations for current user's organization
    
    TASK-339: GET /automations endpoint
    """
    query = db.query(Automation).filter(
        Automation.org_id == current_user.org_id
    )
    
    # Apply filters
    if status:
        query = query.filter(Automation.status == status)
    
    if trigger_type:
        query = query.filter(Automation.trigger_type == trigger_type)
    
    # Order by updated_at descending
    query = query.order_by(desc(Automation.updated_at))
    
    # Pagination
    automations = query.offset(skip).limit(limit).all()
    
    return automations


@router.post("", response_model=AutomationResponse, status_code=status.HTTP_201_CREATED)
async def create_automation(
    automation_data: AutomationCreateSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create new automation
    
    TASK-340: POST /automations endpoint
    """
    # Validate schedule if SCHEDULE trigger
    if automation_data.trigger_type == TriggerType.SCHEDULE:
        if not automation_data.schedule:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Schedule is required for SCHEDULE trigger type"
            )
        
        if not validate_cron_expression(automation_data.schedule):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid cron expression"
            )
        
        # Validate timezone
        if automation_data.timezone and not validate_timezone(automation_data.timezone):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid timezone: {automation_data.timezone}"
            )
    
    # Calculate next run for scheduled automations
    next_run_at = None
    if automation_data.trigger_type == TriggerType.SCHEDULE and automation_data.schedule:
        try:
            next_run_at = calculate_next_run(
                automation_data.schedule,
                timezone=automation_data.timezone
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error calculating next run: {e}"
            )
    
    # Create automation
    automation = Automation(
        id=uuid.uuid4(),
        org_id=current_user.org_id,
        name=automation_data.name,
        description=automation_data.description,
        workflow=automation_data.workflow,
        trigger_type=automation_data.trigger_type,
        schedule=automation_data.schedule,
        timezone=automation_data.timezone or "UTC",
        trigger_config=automation_data.trigger_config.dict() if automation_data.trigger_config else None,
        agent_id=automation_data.agent_id,
        status=AutomationStatus.ACTIVE if automation_data.enabled else AutomationStatus.PAUSED,
        next_run_at=next_run_at,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(automation)
    db.commit()
    db.refresh(automation)
    
    return automation


@router.get("/{automation_id}", response_model=AutomationResponse)
async def get_automation(
    automation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get automation by ID
    
    TASK-341: GET /automations/{id} endpoint
    """
    automation = db.query(Automation).filter(
        and_(
            Automation.id == automation_id,
            Automation.org_id == current_user.org_id
        )
    ).first()
    
    if not automation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Automation not found"
        )
    
    return automation


@router.patch("/{automation_id}", response_model=AutomationResponse)
async def update_automation(
    automation_id: uuid.UUID,
    update_data: AutomationUpdateSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update automation
    
    TASK-342: PATCH /automations/{id} endpoint
    """
    automation = db.query(Automation).filter(
        and_(
            Automation.id == automation_id,
            Automation.org_id == current_user.org_id
        )
    ).first()
    
    if not automation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Automation not found"
        )
    
    # Update fields
    update_dict = update_data.dict(exclude_unset=True)
    
    # Validate schedule if updated
    if "schedule" in update_dict and update_dict["schedule"]:
        if not validate_cron_expression(update_dict["schedule"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid cron expression"
            )
    
    # Validate timezone if updated
    if "timezone" in update_dict and update_dict["timezone"]:
        if not validate_timezone(update_dict["timezone"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid timezone: {update_dict['timezone']}"
            )
    
    # Handle enabled field (maps to status)
    if "enabled" in update_dict:
        enabled = update_dict.pop("enabled")
        if enabled:
            update_dict["status"] = AutomationStatus.ACTIVE
        else:
            update_dict["status"] = AutomationStatus.PAUSED
    
    # Convert trigger_config if present
    if "trigger_config" in update_dict and update_dict["trigger_config"]:
        update_dict["trigger_config"] = update_dict["trigger_config"].dict()
    
    # Update automation
    for key, value in update_dict.items():
        setattr(automation, key, value)
    
    automation.updated_at = datetime.utcnow()
    
    # Recalculate next_run_at if schedule changed
    if automation.trigger_type == TriggerType.SCHEDULE and automation.schedule:
        try:
            automation.next_run_at = calculate_next_run(
                automation.schedule,
                timezone=automation.timezone
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Error calculating next run: {e}"
            )
    
    db.commit()
    db.refresh(automation)
    
    return automation


@router.delete("/{automation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_automation(
    automation_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete automation
    
    TASK-343: DELETE /automations/{id} endpoint
    """
    automation = db.query(Automation).filter(
        and_(
            Automation.id == automation_id,
            Automation.org_id == current_user.org_id
        )
    ).first()
    
    if not automation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Automation not found"
        )
    
    # Archive instead of hard delete
    automation.status = AutomationStatus.ARCHIVED
    automation.updated_at = datetime.utcnow()
    
    db.commit()
    
    return None


@router.get("/{automation_id}/runs", response_model=List[AutomationRunResponse])
async def list_automation_runs(
    automation_id: uuid.UUID,
    status_filter: Optional[RunStatus] = None,
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List automation runs
    
    TASK-344: GET /automations/{id}/runs endpoint
    """
    # Verify automation belongs to user's org
    automation = db.query(Automation).filter(
        and_(
            Automation.id == automation_id,
            Automation.org_id == current_user.org_id
        )
    ).first()
    
    if not automation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Automation not found"
        )
    
    # Query runs
    query = db.query(AutomationRun).filter(
        AutomationRun.automation_id == automation_id
    )
    
    # Apply status filter
    if status_filter:
        query = query.filter(AutomationRun.status == status_filter)
    
    # Order by created_at descending
    query = query.order_by(desc(AutomationRun.created_at))
    
    # Pagination
    runs = query.offset(skip).limit(limit).all()
    
    return runs


@router.post("/{automation_id}/test", response_model=Dict[str, Any])
async def test_automation(
    automation_id: uuid.UUID,
    test_data: TestAutomationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Test automation execution
    
    TASK-345: POST /automations/{id}/test endpoint
    """
    # Verify automation belongs to user's org
    automation = db.query(Automation).filter(
        and_(
            Automation.id == automation_id,
            Automation.org_id == current_user.org_id
        )
    ).first()
    
    if not automation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Automation not found"
        )
    
    # Queue test execution
    task = execute_automation.delay(
        str(automation_id),
        trigger_type=TriggerType.MANUAL.value,
        trigger_data=test_data.trigger_data
    )
    
    return {
        "task_id": task.id,
        "automation_id": str(automation_id),
        "status": "queued",
        "message": "Test execution queued successfully"
    }


@router.post("/{automation_id}/cancel", response_model=Dict[str, Any])
async def cancel_automation(
    automation_id: uuid.UUID,
    run_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cancel running automation
    """
    # Verify automation belongs to user's org
    automation = db.query(Automation).filter(
        and_(
            Automation.id == automation_id,
            Automation.org_id == current_user.org_id
        )
    ).first()
    
    if not automation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Automation not found"
        )
    
    # Verify run exists
    run = db.query(AutomationRun).filter(
        and_(
            AutomationRun.id == run_id,
            AutomationRun.automation_id == automation_id
        )
    ).first()
    
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found"
        )
    
    # Cancel task
    cancel_automation_run(str(run_id))
    
    return {
        "run_id": str(run_id),
        "status": "cancelled",
        "message": "Automation run cancelled"
    }


# ==================== Webhook Endpoint ====================

@router.post("/webhook/{automation_id}", response_model=Dict[str, Any])
async def webhook_trigger(
    automation_id: uuid.UUID,
    request: Request,
    webhook_data: WebhookTriggerRequest,
    x_signature: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None),
    db: Session = Depends(get_db)
):
    """
    Webhook endpoint for triggering automations
    
    TASK-334: Webhook endpoint for triggers
    TASK-337: Trigger authentication
    """
    # Find automation
    automation = db.query(Automation).filter(
        Automation.id == automation_id
    ).first()
    
    if not automation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Automation not found"
        )
    
    # Verify trigger type
    if automation.trigger_type != TriggerType.WEBHOOK:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Automation is not configured for webhook triggers"
        )
    
    # Verify status
    if automation.status != AutomationStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Automation is not active"
        )
    
    # Authenticate request
    trigger_config = automation.trigger_config or {}
    auth_type = trigger_config.get("auth_type", "none")
    authenticated = False
    
    if auth_type == "signature" and x_signature:
        # Verify HMAC signature
        secret = trigger_config.get("webhook_secret")
        if secret:
            body = await request.body()
            authenticated = WebhookAuthenticator.verify_signature(
                body, x_signature, secret
            )
    elif auth_type == "api_key" and x_api_key:
        # Verify API key
        expected_key = trigger_config.get("api_key")
        if expected_key:
            authenticated = WebhookAuthenticator.verify_api_key(
                x_api_key, expected_key
            )
    elif auth_type == "none":
        authenticated = True
    
    if not authenticated:
        # Log failed authentication
        TriggerLogger.log_trigger_failed(
            str(automation_id),
            webhook_data.event_type,
            "Authentication failed",
            authenticated=False
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )
    
    # Log webhook received
    client_ip = request.client.host if request.client else None
    TriggerLogger.log_webhook_received(
        str(automation_id),
        webhook_data.event_type,
        webhook_data.event_data,
        source_ip=client_ip,
        authenticated=authenticated
    )
    
    # Queue automation execution
    task = execute_automation.delay(
        str(automation_id),
        trigger_type=TriggerType.WEBHOOK.value,
        trigger_data={
            "event_type": webhook_data.event_type,
            "event_data": webhook_data.event_data,
            "triggered_at": datetime.utcnow().isoformat(),
            "source_ip": client_ip
        }
    )
    
    return {
        "task_id": task.id,
        "automation_id": str(automation_id),
        "status": "queued",
        "message": "Webhook received and automation queued"
    }


# ==================== Schedule Testing Endpoint ====================

@router.post("/test-schedule", response_model=Dict[str, Any])
async def test_cron_schedule(
    cron_expression: str,
    timezone: str = "UTC",
    test_count: int = 5,
    current_user: User = Depends(get_current_user)
):
    """
    Test cron schedule expression
    
    Returns next N run times and human-readable description
    """
    return test_schedule(cron_expression, timezone, test_count)
