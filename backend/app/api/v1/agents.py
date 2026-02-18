"""
Agent API Endpoints
Handles agent CRUD operations
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.agent import AgentCreate, AgentUpdate, AgentResponse
from app.services import agent_service, organization_service


router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("", response_model=List[AgentResponse])
async def list_agents(
    org_id: UUID,
    include_inactive: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all agents for an organization
    
    User must be a member of the organization
    """
    # Check if user is a member
    is_member = await organization_service.is_org_member(db, current_user.id, org_id)
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this organization"
        )
    
    agents = await agent_service.get_organization_agents(db, org_id, include_inactive)
    return agents


@router.post("", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    org_id: UUID,
    agent_data: AgentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new agent
    
    Only admins and owners can create agents
    """
    # Check if user is admin/owner
    is_admin = await organization_service.is_org_admin(db, current_user.id, org_id)
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and owners can create agents"
        )
    
    agent = await agent_service.create_agent(db, agent_data, org_id)
    return agent


@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    agent_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get agent details
    
    User must be a member of the agent's organization
    """
    agent = await agent_service.get_agent_by_id(db, agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    # Check if user is a member
    is_member = await organization_service.is_org_member(db, current_user.id, agent.org_id)
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this organization"
        )
    
    return agent


@router.patch("/{agent_id}", response_model=AgentResponse)
async def update_agent(
    agent_id: UUID,
    agent_data: AgentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update agent
    
    Only admins and owners can update agents
    """
    agent = await agent_service.get_agent_by_id(db, agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    # Check if user is admin/owner
    is_admin = await organization_service.is_org_admin(db, current_user.id, agent.org_id)
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and owners can update agents"
        )
    
    updated_agent = await agent_service.update_agent(db, agent_id, agent_data)
    return updated_agent


@router.delete("/{agent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent(
    agent_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete agent
    
    Only admins and owners can delete agents
    """
    agent = await agent_service.get_agent_by_id(db, agent_id)
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    # Check if user is admin/owner
    is_admin = await organization_service.is_org_admin(db, current_user.id, agent.org_id)
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins and owners can delete agents"
        )
    
    await agent_service.delete_agent(db, agent_id)
    return None
