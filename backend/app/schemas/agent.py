from pydantic import BaseModel, UUID4
from datetime import datetime
from typing import Optional, Dict, Any, List

class AgentBase(BaseModel):
    name: str
    description: Optional[str] = None
    system_prompt: Optional[str] = None

class AgentCreate(AgentBase):
    config: Optional[Dict[str, Any]] = {}

class AgentUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    system_prompt: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class AgentResponse(AgentBase):
    id: UUID4
    org_id: UUID4
    config: Dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ChatMessage(BaseModel):
    role: str  # user, assistant, system
    content: str

class ChatRequest(BaseModel):
    message: str
    agent_id: UUID4
    conversation_id: Optional[UUID4] = None

class ChatResponse(BaseModel):
    message: str
    thought_trace: List[str]
    sources: List[Dict[str, Any]]
    conversation_id: UUID4

class ActivityLogResponse(BaseModel):
    id: UUID4
    action_type: str
    tool_name: Optional[str]
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True
