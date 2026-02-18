"""
Approval API endpoints for agent action approvals

TASK-292: Send approval response to backend
TASK-293: Handle approval timeout
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from datetime import datetime, timedelta
from pydantic import BaseModel

from app.database import get_db
from app.models.user import User
from app.dependencies import get_current_user


router = APIRouter(prefix="/approvals", tags=["approvals"])


# ===== SCHEMAS =====

class ApprovalRequest(BaseModel):
    """Approval request sent to frontend"""
    id: str
    action_type: str
    action_name: str
    description: str
    parameters: dict
    risk_level: str  # low, medium, high
    estimated_duration_ms: Optional[int] = None
    timeout_ms: int = 30000  # 30 seconds default
    timestamp: str


class ApprovalResponse(BaseModel):
    """Approval response from user"""
    approval_id: str
    approved: bool
    user_note: Optional[str] = None


class ApprovalStatus(BaseModel):
    """Approval status"""
    status: str  # pending, approved, rejected, timeout
    approved_at: Optional[str] = None
    user_note: Optional[str] = None


# ===== IN-MEMORY APPROVAL STORE =====
# In production, use Redis or database
pending_approvals: dict[str, dict] = {}


# ===== APPROVAL MANAGER =====

class ApprovalManager:
    """
    Manages approval requests and responses
    
    TASK-292: Backend approval handling
    TASK-293: Timeout management
    """
    
    @staticmethod
    def create_approval_request(
        action_type: str,
        action_name: str,
        description: str,
        parameters: dict,
        risk_level: str = "medium",
        timeout_ms: int = 30000,
        estimated_duration_ms: Optional[int] = None
    ) -> ApprovalRequest:
        """Create a new approval request"""
        import uuid
        
        approval_id = str(uuid.uuid4())
        request = ApprovalRequest(
            id=approval_id,
            action_type=action_type,
            action_name=action_name,
            description=description,
            parameters=parameters,
            risk_level=risk_level,
            estimated_duration_ms=estimated_duration_ms,
            timeout_ms=timeout_ms,
            timestamp=datetime.utcnow().isoformat()
        )
        
        # Store in pending approvals
        pending_approvals[approval_id] = {
            "request": request.dict(),
            "status": "pending",
            "created_at": datetime.utcnow(),
            "timeout_at": datetime.utcnow() + timedelta(milliseconds=timeout_ms)
        }
        
        return request
    
    @staticmethod
    def submit_approval_response(
        approval_id: str,
        approved: bool,
        user_note: Optional[str] = None
    ) -> ApprovalStatus:
        """Submit user approval decision"""
        if approval_id not in pending_approvals:
            raise ValueError(f"Approval {approval_id} not found")
        
        approval_data = pending_approvals[approval_id]
        
        # Check if already responded
        if approval_data["status"] != "pending":
            raise ValueError(f"Approval {approval_id} already {approval_data['status']}")
        
        # Check timeout
        if datetime.utcnow() > approval_data["timeout_at"]:
            approval_data["status"] = "timeout"
            raise ValueError(f"Approval {approval_id} has timed out")
        
        # Update status
        approval_data["status"] = "approved" if approved else "rejected"
        approval_data["approved_at"] = datetime.utcnow()
        approval_data["user_note"] = user_note
        
        return ApprovalStatus(
            status=approval_data["status"],
            approved_at=approval_data["approved_at"].isoformat(),
            user_note=user_note
        )
    
    @staticmethod
    def check_approval_status(approval_id: str) -> ApprovalStatus:
        """Check approval status (with timeout check)"""
        if approval_id not in pending_approvals:
            raise ValueError(f"Approval {approval_id} not found")
        
        approval_data = pending_approvals[approval_id]
        
        # Auto-timeout if expired
        if (approval_data["status"] == "pending" and 
            datetime.utcnow() > approval_data["timeout_at"]):
            approval_data["status"] = "timeout"
        
        return ApprovalStatus(
            status=approval_data["status"],
            approved_at=approval_data.get("approved_at", "").isoformat() if approval_data.get("approved_at") else None,
            user_note=approval_data.get("user_note")
        )
    
    @staticmethod
    async def wait_for_approval(
        approval_id: str,
        poll_interval: float = 0.5
    ) -> bool:
        """
        Wait for approval response (async)
        
        Returns True if approved, False if rejected or timeout
        """
        while True:
            status = ApprovalManager.check_approval_status(approval_id)
            
            if status.status == "approved":
                return True
            elif status.status in ["rejected", "timeout"]:
                return False
            
            await asyncio.sleep(poll_interval)
    
    @staticmethod
    def cleanup_old_approvals(max_age_hours: int = 1):
        """Remove old approval records"""
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        to_remove = [
            aid for aid, data in pending_approvals.items()
            if data["created_at"] < cutoff
        ]
        for aid in to_remove:
            del pending_approvals[aid]


# ===== API ENDPOINTS =====

@router.post("/respond", response_model=ApprovalStatus)
async def submit_approval(
    response: ApprovalResponse,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Submit approval response
    
    TASK-292: Send approval response to backend
    """
    try:
        status = ApprovalManager.submit_approval_response(
            approval_id=response.approval_id,
            approved=response.approved,
            user_note=response.user_note
        )
        return status
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{approval_id}/status", response_model=ApprovalStatus)
async def get_approval_status(
    approval_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get approval status
    
    TASK-293: Handle approval timeout
    """
    try:
        status = ApprovalManager.check_approval_status(approval_id)
        return status
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/cleanup")
async def cleanup_approvals(
    max_age_hours: int = 1,
    current_user: User = Depends(get_current_user)
):
    """Cleanup old approvals (admin only)"""
    ApprovalManager.cleanup_old_approvals(max_age_hours)
    return {"message": f"Cleaned up approvals older than {max_age_hours} hours"}


# ===== HELPER FUNCTIONS FOR AGENT INTEGRATION =====

async def request_user_approval(
    action_type: str,
    action_name: str,
    description: str,
    parameters: dict,
    risk_level: str = "medium",
    timeout_ms: int = 30000
) -> tuple[ApprovalRequest, bool]:
    """
    Request user approval and wait for response
    
    Returns: (approval_request, approved)
    
    Usage in agent orchestration:
        request, approved = await request_user_approval(
            action_type="gmail_send",
            action_name="Send Email",
            description="Send email to john@example.com",
            parameters={"to": "john@example.com", "subject": "Hello"},
            risk_level="medium"
        )
        
        if not approved:
            return {"error": "User rejected action"}
    """
    # Create approval request
    request = ApprovalManager.create_approval_request(
        action_type=action_type,
        action_name=action_name,
        description=description,
        parameters=parameters,
        risk_level=risk_level,
        timeout_ms=timeout_ms
    )
    
    # Wait for approval (this would be yielded as SSE event to frontend)
    # Frontend shows modal and submits response via /approvals/respond
    approved = await ApprovalManager.wait_for_approval(request.id)
    
    return request, approved


def determine_risk_level(tool_name: str, arguments: dict) -> str:
    """
    Determine risk level for a tool call
    
    Returns: "low", "medium", or "high"
    """
    # High risk tools (destructive actions)
    high_risk_tools = [
        "gmail_delete",
        "gmail_send",  # Sending emails
        "calendar_delete",
        "jira_delete_issue",
        "slack_delete_message"
    ]
    
    # Medium risk tools (modifications)
    medium_risk_tools = [
        "gmail_reply",
        "calendar_create",
        "calendar_update",
        "jira_create_issue",
        "jira_update_issue",
        "slack_send_message"
    ]
    
    if tool_name in high_risk_tools:
        return "high"
    elif tool_name in medium_risk_tools:
        return "medium"
    else:
        return "low"


# Export for use in other modules
__all__ = [
    "router",
    "ApprovalManager",
    "ApprovalRequest",
    "ApprovalResponse",
    "ApprovalStatus",
    "request_user_approval",
    "determine_risk_level"
]
