from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models import Conversation, ConversationMessage, User
from app.schemas.domain import ConversationCreate, ConversationResponse, MessageCreate, MessageResponse
from app.api.deps import get_current_user, get_current_organization_id, require_permission
from app.agent.runtime import AgentRuntime

router = APIRouter(prefix="/chat", tags=["Chat & Agent Conversations"])

@router.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations(
    org_id: str = Depends(get_current_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(
        select(Conversation)
        .where(Conversation.organization_id == org_id, Conversation.user_id == current_user.id)
        .order_by(Conversation.updated_at.desc())
    )
    return res.scalars().all()

@router.post("/conversations", response_model=ConversationResponse)
async def create_conversation(
    payload: ConversationCreate,
    org_id: str = Depends(get_current_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    conv = Conversation(
        organization_id=org_id,
        user_id=current_user.id,
        title=payload.title or "New Conversation"
    )
    db.add(conv)
    await db.commit()
    await db.refresh(conv)
    return conv

@router.get("/conversations/{id}")
async def get_conversation(
    id: str,
    org_id: str = Depends(get_current_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(
        select(Conversation).where(
            Conversation.id == id,
            Conversation.organization_id == org_id,
            Conversation.user_id == current_user.id
        )
    )
    conv = res.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    m_res = await db.execute(
        select(ConversationMessage)
        .where(ConversationMessage.conversation_id == conv.id)
        .order_by(ConversationMessage.created_at.asc())
    )
    messages = m_res.scalars().all()

    return {
        "id": conv.id,
        "title": conv.title,
        "created_at": conv.created_at.isoformat(),
        "messages": [
            {
                "id": m.id,
                "sender": m.sender,
                "content": m.content,
                "reasoning_summary": m.reasoning_summary,
                "tool_calls": m.tool_calls_json or [],
                "citations": m.citations_json or [],
                "created_at": m.created_at.isoformat()
            }
            for m in messages
        ]
    }

@router.delete("/conversations/{id}")
async def delete_conversation(
    id: str,
    org_id: str = Depends(get_current_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(
        select(Conversation).where(
            Conversation.id == id,
            Conversation.organization_id == org_id,
            Conversation.user_id == current_user.id
        )
    )
    conv = res.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    await db.delete(conv)
    await db.commit()
    return {"status": "success", "message": "Conversation deleted"}

@router.post("/conversations/{id}/messages", dependencies=[Depends(require_permission("agent.execute"))])
async def send_message_stream(
    id: str,
    payload: MessageCreate,
    org_id: str = Depends(get_current_organization_id),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    res = await db.execute(
        select(Conversation).where(
            Conversation.id == id,
            Conversation.organization_id == org_id,
            Conversation.user_id == current_user.id
        )
    )
    conv = res.scalar_one_or_none()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Update conversation title if first message
    if conv.title == "New Conversation":
        snippet = payload.content[:40].strip()
        conv.title = snippet if snippet else "Conversation"

    # Save user message
    user_msg = ConversationMessage(
        conversation_id=conv.id,
        sender="USER",
        content=payload.content
    )
    db.add(user_msg)
    await db.commit()

    agent_runtime = AgentRuntime(db)

    return StreamingResponse(
        agent_runtime.execute_stream(
            conversation_id=conv.id,
            user_id=current_user.id,
            organization_id=org_id,
            user_request=payload.content
        ),
        media_type="text/event-stream"
    )
