"""
Agent Service
Business logic for agent management
"""

from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.models.agent import Agent
from app.schemas.agent import AgentCreate, AgentUpdate


async def create_agent(db: Session, agent_data: AgentCreate, org_id: UUID) -> Agent:
    """
    Create a new agent
    
    Args:
        db: Database session
        agent_data: Agent creation data
        org_id: Organization ID
        
    Returns:
        Created agent
    """
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


async def get_agent_by_id(db: Session, agent_id: UUID) -> Optional[Agent]:
    """
    Get agent by ID
    
    Args:
        db: Database session
        agent_id: Agent ID
        
    Returns:
        Agent or None
    """
    return db.query(Agent).filter(Agent.id == agent_id).first()


async def get_organization_agents(db: Session, org_id: UUID, include_inactive: bool = False) -> List[Agent]:
    """
    Get all agents for an organization
    
    Args:
        db: Database session
        org_id: Organization ID
        include_inactive: Whether to include inactive agents
        
    Returns:
        List of agents
    """
    query = db.query(Agent).filter(Agent.org_id == org_id)
    
    if not include_inactive:
        query = query.filter(Agent.is_active == True)
    
    return query.order_by(Agent.created_at.desc()).all()


async def update_agent(db: Session, agent_id: UUID, agent_data: AgentUpdate) -> Optional[Agent]:
    """
    Update agent
    
    Args:
        db: Database session
        agent_id: Agent ID
        agent_data: Update data
        
    Returns:
        Updated agent or None
    """
    agent = await get_agent_by_id(db, agent_id)
    if not agent:
        return None
    
    update_dict = agent_data.dict(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(agent, key, value)
    
    db.commit()
    db.refresh(agent)
    return agent


async def delete_agent(db: Session, agent_id: UUID) -> bool:
    """
    Delete agent
    
    Args:
        db: Database session
        agent_id: Agent ID
        
    Returns:
        True if deleted, False if not found
    """
    agent = await get_agent_by_id(db, agent_id)
    if not agent:
        return False
    
    db.delete(agent)
    db.commit()
    return True
