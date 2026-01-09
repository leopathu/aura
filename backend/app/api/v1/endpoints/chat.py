from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models.user import User
from app.db.models.agent import Agent, ActivityLog
from app.db.models.credential import Credential
from app.schemas.agent import ChatRequest
from app.api.dependencies import get_current_user, get_current_org
from app.services.mcp_client import mcp_registry
from app.services.agent_orchestrator import AgentOrchestrator
from app.services.llm_service import LLMService
from uuid import UUID, uuid4
import json

router = APIRouter()

@router.post("/organizations/{org_id}/agents/{agent_id}/chat")
async def chat_with_agent(
    org_id: UUID,
    agent_id: UUID,
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Stream chat with an agent."""
    # Verify org access
    await get_current_org(org_id, current_user, db)
    
    # Get agent
    agent = db.query(Agent).filter(
        Agent.id == agent_id,
        Agent.org_id == org_id
    ).first()
    
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    
    # Get active credential for this org
    credential = db.query(Credential).filter(
        Credential.org_id == org_id,
        Credential.is_active == True
    ).first()
    
    if not credential:
        raise HTTPException(
            status_code=400,
            detail="No active LLM credentials found. Please add your API key."
        )
    
    # Create LLM service
    llm_service = LLMService.create_from_credential(
        credential.encrypted_api_key,
        credential.credential_type.value
    )
    
    # Create orchestrator
    orchestrator = AgentOrchestrator(
        agent_config=agent.config,
        llm_client=llm_service,
        mcp_registry=mcp_registry
    )
    
    # Log activity
    conversation_id = chat_request.conversation_id or uuid4()
    activity_log = ActivityLog(
        agent_id=agent_id,
        org_id=org_id,
        user_id=current_user.id,
        action_type="chat",
        input_data={"message": chat_request.message},
        status="in_progress"
    )
    db.add(activity_log)
    db.commit()
    
    async def event_stream():
        """Stream server-sent events."""
        try:
            async for event in orchestrator.run(chat_request.message, conversation_id):
                # Format as SSE
                yield f"data: {json.dumps(event)}\n\n"
            
            # Update activity log
            activity_log.status = "success"
            db.commit()
            
        except Exception as e:
            error_event = {
                "type": "error",
                "content": str(e)
            }
            yield f"data: {json.dumps(error_event)}\n\n"
            
            # Update activity log
            activity_log.status = "failed"
            activity_log.error_message = str(e)
            db.commit()
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
