"""
Agent Tools API Endpoints
Manage tools available to AI agents
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from uuid import UUID

from app.db.session import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.tools import ToolRegistry

router = APIRouter()


@router.get("/tools", response_model=Dict[str, List[Dict[str, str]]])
async def get_available_tools(
    org_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all available tools for the current user based on connected integrations
    
    Returns:
        Dictionary mapping category to list of tool descriptions
    """
    try:
        tool_descriptions = await ToolRegistry.get_tool_descriptions(
            db,
            current_user.id,
            org_id
        )
        
        return tool_descriptions
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load tools: {str(e)}"
        )


@router.get("/tools/{category}", response_model=List[Dict[str, str]])
async def get_tools_by_category(
    category: str,
    org_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get tools for a specific category/integration
    
    Args:
        category: Tool category (gmail, calendar, slack, etc.)
        org_id: Organization ID
        
    Returns:
        List of tool descriptions for the category
    """
    try:
        tools = await ToolRegistry.get_tools_by_category(
            db,
            current_user.id,
            org_id,
            category
        )
        
        # Return tool descriptions
        descriptions = []
        for tool in tools:
            descriptions.append({
                "name": tool.name,
                "description": tool.description
            })
        
        return descriptions
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load tools for category {category}: {str(e)}"
        )
