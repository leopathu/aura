"""Agent chat routes with streaming SSE — RAG over synced agent data."""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncGenerator

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.repositories.ai_settings_repository import AISettingsRepository
from app.repositories.conversation_repository import ConversationRepository
from app.schemas.conversation import (
    AgentChatRequest,
    AgentConversationCreate,
    ConversationDetail,
    ConversationSummary,
)
from app.services.rag_service import RAGService

router = APIRouter(prefix="/agents/{agent_id}/chat", tags=["Agent Chat"])


async def _get_agent_or_404(agent_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession) -> None:
    """Verify the agent exists and belongs to the current user.

    Raises:
        HTTPException: 404 if agent not found or not owned by the user.
    """
    from sqlalchemy import select  # noqa: PLC0415
    from app.models.agent import Agent  # noqa: PLC0415

    result = await db.execute(
        select(Agent).where(Agent.id == agent_id, Agent.user_id == user_id)
    )
    if result.scalar_one_or_none() is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent not found")


@router.get("/conversations", response_model=list[ConversationSummary])
async def list_agent_conversations(
    agent_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ConversationSummary]:
    """List all conversations for the current user in a specific agent."""
    await _get_agent_or_404(agent_id, current_user.id, db)
    repo = ConversationRepository(db)
    convs = await repo.list_by_agent(current_user.id, agent_id)
    return [ConversationSummary.model_validate(c) for c in convs]


@router.post(
    "/conversations",
    response_model=ConversationSummary,
    status_code=status.HTTP_201_CREATED,
)
async def create_agent_conversation(
    agent_id: uuid.UUID,
    payload: AgentConversationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ConversationSummary:
    """Create a new agent-scoped conversation."""
    await _get_agent_or_404(agent_id, current_user.id, db)
    repo = ConversationRepository(db)
    conv = await repo.create_for_agent(current_user.id, agent_id, payload.title)
    await db.commit()
    return ConversationSummary.model_validate(conv)


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
async def get_agent_conversation(
    agent_id: uuid.UUID,
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ConversationDetail:
    """Fetch a full agent conversation with all messages."""
    await _get_agent_or_404(agent_id, current_user.id, db)
    repo = ConversationRepository(db)
    conv = await repo.get_by_id(conversation_id, current_user.id)
    if not conv or conv.agent_id != agent_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return ConversationDetail.model_validate(conv)


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_agent_conversation(
    agent_id: uuid.UUID,
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete an agent conversation."""
    await _get_agent_or_404(agent_id, current_user.id, db)
    repo = ConversationRepository(db)
    conv = await repo.get_by_id(conversation_id, current_user.id)
    if not conv or conv.agent_id != agent_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    deleted = await repo.delete(conversation_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    await db.commit()


@router.post("/stream")
async def stream_agent_chat(
    agent_id: uuid.UUID,
    request: AgentChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    """Stream a RAG response over agent-synced data using Server-Sent Events.

    Creates a new conversation if conversation_id is None.
    Saves the user message and full assistant response to the DB after streaming.

    SSE event types:
    - ``meta``: First event — carries ``conversation_id`` and ``sources`` list.
    - ``token``: Subsequent events — carries individual LLM tokens.
    - ``done``: Final event — signals end of stream.
    - ``error``: Sent on failure.
    """
    await _get_agent_or_404(agent_id, current_user.id, db)
    conv_repo = ConversationRepository(db)

    # Resolve or create conversation
    if request.conversation_id:
        conv = await conv_repo.get_by_id(request.conversation_id, current_user.id)
        if not conv or conv.agent_id != agent_id:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        title = request.message[:60] + ("…" if len(request.message) > 60 else "")
        conv = await conv_repo.create_for_agent(current_user.id, agent_id, title)

    # Save user message
    await conv_repo.add_message(conv.id, "user", request.message)

    # Build multi-turn history (last 10 turns, excluding the message just added)
    existing = await conv_repo.get_by_id(conv.id, current_user.id)
    history = [
        {"role": m.role, "content": m.content}
        for m in (existing.messages if existing else [])
        if m.role in ("user", "assistant")
    ][:-1]

    await db.commit()

    ai = await AISettingsRepository(db).get_by_user(current_user.id)
    svc = RAGService(db, ai=ai)

    async def event_stream() -> AsyncGenerator[str, None]:
        """Async generator yielding SSE-formatted events."""
        from app.db.session import AsyncSessionLocal  # noqa: PLC0415

        full_answer = ""
        sources_sent = False

        try:
            async for token, sources in svc.stream_agent_answer(
                query=request.message,
                agent_id=str(agent_id),
                history=history,
            ):
                if not sources_sent:
                    sources_sent = True
                    meta = {
                        "type": "meta",
                        "conversation_id": str(conv.id),
                        "sources": [s.model_dump() for s in sources],
                    }
                    yield f"data: {json.dumps(meta)}\n\n"
                    continue

                full_answer += token
                yield f"data: {json.dumps({'type': 'token', 'token': token})}\n\n"

            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as exc:
            yield f"data: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"
            return

        finally:
            if full_answer:
                async with AsyncSessionLocal() as save_db:
                    try:
                        save_repo = ConversationRepository(save_db)
                        saved_conv = await save_repo.get_by_id(conv.id, current_user.id)
                        if saved_conv:
                            await save_repo.add_message(
                                conv.id, "assistant", full_answer, sources_json=None
                            )
                            await save_repo.touch(saved_conv)
                        await save_db.commit()
                    except Exception:
                        await save_db.rollback()

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
