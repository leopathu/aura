"""
Agent Debug API Endpoints
Endpoints for inspecting agent execution details
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Dict, Any

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.agent import Agent
from app.services.agent_orchestration import run_agent_graph, format_thought_trace
from pydantic import BaseModel


router = APIRouter(prefix="/agent-debug", tags=["agent-debug"])


class AgentTestRequest(BaseModel):
    """Request for testing agent orchestration"""
    agent_id: UUID
    message: str


class AgentTestResponse(BaseModel):
    """Response with full agent execution details"""
    final_response: str
    thought_trace: list
    tool_calls: list
    iteration_count: int
    formatted_trace: str
    execution_time_ms: int


@router.post("/test", response_model=AgentTestResponse)
async def test_agent_orchestration(
    test_request: AgentTestRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Test agent orchestration and inspect full execution details
    
    This endpoint is useful for debugging and understanding how the agent
    processes requests through the state machine.
    """
    from datetime import datetime
    
    start_time = datetime.utcnow()
    
    # Get agent
    agent = db.query(Agent).filter(
        Agent.id == test_request.agent_id,
        Agent.is_active == True
    ).first()
    
    if not agent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Agent not found"
        )
    
    # Verify access (user must be in agent's organization)
    from app.services import organization_service
    is_member = await organization_service.is_org_member(
        db,
        current_user.id,
        agent.org_id
    )
    
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this agent"
        )
    
    # Run agent orchestration
    agent_state = await run_agent_graph(
        user_message=test_request.message,
        agent=agent,
        db=db,
        user_id=current_user.id,
        org_id=agent.org_id
    )
    
    execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
    
    # Format response
    return AgentTestResponse(
        final_response=agent_state.get("final_response", "No response generated"),
        thought_trace=agent_state.get("thought_trace", []),
        tool_calls=agent_state.get("tool_calls", []),
        iteration_count=agent_state.get("iteration_count", 0),
        formatted_trace=format_thought_trace(agent_state.get("thought_trace", [])),
        execution_time_ms=execution_time
    )


@router.get("/trace-format-example")
async def get_trace_format_example():
    """
    Get an example of the thought trace format
    
    Useful for understanding the structure of agent execution traces
    """
    example_trace = [
        {
            "timestamp": "2026-02-18T10:30:00.000Z",
            "step": "analyze_request",
            "node": "analyze",
            "content": "Analyzing user request to understand intent...",
            "status": "in_progress",
            "metadata": {}
        },
        {
            "timestamp": "2026-02-18T10:30:02.000Z",
            "step": "analyze_request",
            "node": "analyze",
            "content": "Request analysis: User wants to send an email",
            "status": "completed",
            "metadata": {"user_message": "Send an email to john@example.com"}
        },
        {
            "timestamp": "2026-02-18T10:30:03.000Z",
            "step": "create_plan",
            "node": "plan",
            "content": "Creating execution plan...",
            "status": "in_progress",
            "metadata": {}
        },
        {
            "timestamp": "2026-02-18T10:30:05.000Z",
            "step": "create_plan",
            "node": "plan",
            "content": "Plan: 1. Use send_email tool\n2. Verify sending status",
            "status": "completed",
            "metadata": {"plan_steps": ["Use send_email tool", "Verify status"]}
        },
        {
            "timestamp": "2026-02-18T10:30:06.000Z",
            "step": "execute_tools",
            "node": "execute",
            "content": "Executing tools according to plan...",
            "status": "in_progress",
            "metadata": {}
        },
        {
            "timestamp": "2026-02-18T10:30:10.000Z",
            "step": "execute_tool_send_email",
            "node": "execute",
            "content": "✅ send_email completed: Email sent successfully",
            "status": "completed",
            "metadata": {"tool": "send_email", "duration_ms": 3500}
        },
        {
            "timestamp": "2026-02-18T10:30:11.000Z",
            "step": "synthesize_response",
            "node": "synthesize",
            "content": "Synthesizing final response...",
            "status": "in_progress",
            "metadata": {}
        },
        {
            "timestamp": "2026-02-18T10:30:13.000Z",
            "step": "synthesize_response",
            "node": "synthesize",
            "content": "Final response generated: I've sent the email to john@example.com...",
            "status": "completed",
            "metadata": {}
        }
    ]
    
    formatted = format_thought_trace(example_trace)
    
    return {
        "raw_trace": example_trace,
        "formatted_trace": formatted,
        "explanation": {
            "timestamp": "ISO 8601 timestamp of when step occurred",
            "step": "Unique identifier for this step",
            "node": "Graph node that executed this step",
            "content": "Human-readable description of what happened",
            "status": "One of: in_progress, completed, failed",
            "metadata": "Additional structured data about the step"
        }
    }
