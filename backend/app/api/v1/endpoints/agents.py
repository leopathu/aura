from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models.user import User
from app.db.models.agent import Agent, ActivityLog
from app.schemas.agent import (
    AgentCreate, AgentResponse, AgentUpdate,
    ChatRequest, ActivityLogResponse
)
from app.api.dependencies import get_current_user, get_current_org
from typing import List
from uuid import UUID

router = APIRouter()

@router.post("/", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    org_id: UUID,
    agent_data: AgentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new agent."""
    # Verify org access
    await get_current_org(org_id, current_user, db)
    
    agent = Agent(
        org_id=org_id,
        name=agent_data.name,
        description=agent_data.description,
        system_prompt=agent_data.system_prompt,
        config=agent_data.config
    )
    
    db.add(agent)
    db.commit()
    db.refresh(agent)
    
    return agent

@router.get("/", response_model=List[AgentResponse])
async def list_agents(
    org_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all agents in an organization."""
    # Verify org access
    await get_current_org(org_id, current_user, db)
    
    agents = db.query(Agent).filter(
        Agent.org_id == org_id,
        Agent.is_active == True
    ).all()
    
    return agents

@router.get("/{agent_id}", response_model=AgentResponse)
async def get_agent(
    org_id: UUID,
    agent_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get agent details."""
    # Verify org access
    await get_current_org(org_id, current_user, db)
    
    agent = db.query(Agent).filter(
        Agent.id == agent_id,
        Agent.org_id == org_id
    ).first()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    return agent

@router.get("/{agent_id}/logs", response_model=List[ActivityLogResponse])
async def get_agent_logs(
    org_id: UUID,
    agent_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = 50
):
    """Get activity logs for an agent."""
    # Verify org access
    await get_current_org(org_id, current_user, db)
    
    logs = db.query(ActivityLog).filter(
        ActivityLog.agent_id == agent_id,
        ActivityLog.org_id == org_id
    ).order_by(ActivityLog.created_at.desc()).limit(limit).all()
    
    return logs
