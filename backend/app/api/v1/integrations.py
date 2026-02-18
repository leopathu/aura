"""
Integrations API Endpoints
Handles integration-specific operations
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.services.slack_service import get_slack_workspace_info


router = APIRouter(prefix="/integrations", tags=["integrations"])


# ===== SLACK ENDPOINTS =====

@router.get("/slack/workspace")
async def get_slack_workspace(
    org_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get Slack workspace information for connected workspace
    """
    try:
        workspace_info = await get_slack_workspace_info(
            db,
            current_user.id,
            org_id
        )
        
        if not workspace_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No Slack connection found or failed to fetch workspace info"
            )
        
        return workspace_info
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get workspace info: {str(e)}"
        )
