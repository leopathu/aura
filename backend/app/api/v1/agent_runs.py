from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models import AgentRun, AgentStep, ToolCall, ToolResult, User
from app.api.deps import get_current_user, get_current_organization_id

router = APIRouter(prefix="/agent-runs", tags=["Agent Runs & Execution Logging"])

@router.get("")
async def list_agent_runs(
    limit: int = 30,
    org_id: str = Depends(get_current_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(
        select(AgentRun)
        .where(AgentRun.organization_id == org_id)
        .order_by(AgentRun.created_at.desc())
        .limit(limit)
    )
    runs = res.scalars().all()
    return [
        {
            "id": r.id,
            "conversation_id": r.conversation_id,
            "user_id": r.user_id,
            "status": r.status,
            "intent": r.intent,
            "plan": r.plan_json or [],
            "created_at": r.created_at.isoformat(),
            "completed_at": r.completed_at.isoformat() if r.completed_at else None
        }
        for r in runs
    ]

@router.get("/{id}")
async def get_agent_run_trace(
    id: str,
    org_id: str = Depends(get_current_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(select(AgentRun).where(AgentRun.id == id, AgentRun.organization_id == org_id))
    run = res.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=404, detail="Agent run not found")

    steps_res = await db.execute(
        select(AgentStep).where(AgentStep.agent_run_id == run.id).order_by(AgentStep.step_index.asc())
    )
    steps = steps_res.scalars().all()

    tool_calls_res = await db.execute(
        select(ToolCall, ToolResult)
        .outerjoin(ToolResult, ToolResult.tool_call_id == ToolCall.id)
        .where(ToolCall.agent_run_id == run.id)
    )
    tool_calls = tool_calls_res.all()

    return {
        "id": run.id,
        "status": run.status,
        "intent": run.intent,
        "plan": run.plan_json or [],
        "created_at": run.created_at.isoformat(),
        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
        "steps": [
            {
                "index": s.step_index,
                "type": s.step_type,
                "title": s.title,
                "description": s.description,
                "status": s.status
            }
            for s in steps
        ],
        "tool_calls": [
            {
                "tool_name": tc.tool_name,
                "input": tc.tool_input,
                "status": tc.status,
                "output": tr.output_json if tr else None,
                "execution_time_ms": tr.execution_time_ms if tr else None,
                "error": tr.error if tr else None
            }
            for tc, tr in tool_calls
        ]
    }
