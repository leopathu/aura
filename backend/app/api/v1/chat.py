"""Chat conversation routes with streaming SSE."""

from __future__ import annotations

import json
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.repositories.ai_settings_repository import AISettingsRepository
from app.repositories.conversation_repository import ConversationRepository
from app.schemas.conversation import (
    ChatRequest,
    ConversationCreate,
    ConversationDetail,
    ConversationSummary,
)
from app.services.rag_service import RAGService

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.get("/conversations", response_model=list[ConversationSummary])
async def list_conversations(
    brain_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ConversationSummary]:
    """List all conversations for the current user in a brain."""
    repo = ConversationRepository(db)
    convs = await repo.list_by_brain(current_user.id, brain_id)
    return [ConversationSummary.model_validate(c) for c in convs]


@router.post("/conversations", response_model=ConversationSummary, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    payload: ConversationCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ConversationSummary:
    """Create a new conversation."""
    repo = ConversationRepository(db)
    conv = await repo.create(current_user.id, payload)
    return ConversationSummary.model_validate(conv)


@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ConversationDetail:
    """Fetch a full conversation with all messages."""
    repo = ConversationRepository(db)
    conv = await repo.get_by_id(conversation_id, current_user.id)
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
    return ConversationDetail.model_validate(conv)


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    """Delete a conversation."""
    repo = ConversationRepository(db)
    deleted = await repo.delete(conversation_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")


@router.post("/stream")
async def stream_chat(
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> StreamingResponse:
    """Stream a RAG response using Server-Sent Events.

    Creates a new conversation if conversation_id is None.
    Saves user message + full assistant response to DB after streaming.
    """
    conv_repo = ConversationRepository(db)

    # Resolve or create conversation
    if request.conversation_id:
        conv = await conv_repo.get_by_id(request.conversation_id, current_user.id)
        if not conv:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        # Create new conversation titled from first message (truncated)
        title = request.message[:60] + ("…" if len(request.message) > 60 else "")
        conv = await conv_repo.create(
            current_user.id,
            ConversationCreate(brain_id=request.brain_id, title=title),
        )

    # Save user message
    await conv_repo.add_message(conv.id, "user", request.message)

    # Build history for multi-turn context (last 10 messages)
    existing = await conv_repo.get_by_id(conv.id, current_user.id)
    history = [
        {"role": m.role, "content": m.content}
        for m in (existing.messages if existing else [])
        if m.role in ("user", "assistant")
    ][:-1]  # exclude the message we just added

    await db.commit()

    # Build RAG service
    ai = await AISettingsRepository(db).get_by_user(current_user.id)
    svc = RAGService(db, ai=ai)

    async def event_stream() -> AsyncGenerator[str, None]:
        """Async generator yielding SSE-formatted events."""
        from app.db.session import AsyncSessionLocal  # noqa: PLC0415

        full_answer = ""
        sources_sent = False

        try:
            async for token, sources in svc.stream_answer(
                query=request.message,
                brain_id=str(request.brain_id),
                history=history,
            ):
                if not sources_sent:
                    # First event: send conversation_id + sources metadata
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

            # Final event: done
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as exc:
            yield f"data: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"
            return

        finally:
            # Persist assistant message in a fresh session (stream already in progress)
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

    from collections.abc import AsyncGenerator  # noqa: PLC0415

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
