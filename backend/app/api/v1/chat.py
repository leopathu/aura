"""
Chat API Endpoints
Handles chat conversations and message streaming
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID
import json

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.agent import Agent
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ChatMessage,
    ConversationResponse,
    MessageResponse,
    ConversationWithMessages
)
from app.services import chat_service, agent_service, organization_service, llm_service
from app.services.agent_orchestration import run_agent_graph, format_thought_trace


router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def send_message(
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send a chat message to an agent
    
    Creates a new conversation if conversation_id is not provided
    """
    # Get agent and verify access
    agent = await agent_service.get_agent_by_id(db, chat_request.agent_id)
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
    
    # Get or create conversation
    if chat_request.conversation_id:
        conversation = await chat_service.get_conversation_by_id(db, chat_request.conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Verify conversation belongs to user
        if conversation.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this conversation"
            )
    else:
        # Create new conversation
        title = chat_service.generate_conversation_title(chat_request.message)
        conversation = await chat_service.create_conversation(
            db, agent.org_id, agent.id, current_user.id, title
        )
    
    # Save user message
    user_message = await chat_service.create_message(
        db, conversation.id, "user", chat_request.message
    )
    
    # Run agent orchestration with full state machine
    agent_state = await run_agent_graph(
        user_message=chat_request.message,
        agent=agent,
        db=db,
        user_id=current_user.id,
        org_id=agent.org_id
    )
    
    # Extract response
    response_text = agent_state.get("final_response", "I apologize, but I couldn't generate a response.")
    
    # Get thought trace for debugging/transparency
    thought_trace = format_thought_trace(agent_state.get("thought_trace", []))
    
    # Save assistant message with metadata
    assistant_message = await chat_service.create_message(
        db,
        conversation.id,
        "assistant",
        response_text,
        metadata={
            "thought_trace": agent_state.get("thought_trace", []),
            "tool_calls": agent_state.get("tool_calls", []),
            "iteration_count": agent_state.get("iteration_count", 0)
        }
    )
    
    return ChatResponse(
        conversation_id=conversation.id,
        message=ChatMessage(
            role=assistant_message.role,
            content=assistant_message.content,
            metadata=assistant_message.metadata
        ),
        created_at=assistant_message.created_at
    )


@router.post("/stream")
async def stream_message(
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Stream a chat message response using Server-Sent Events
    """
    # Get agent and verify access
    agent = await agent_service.get_agent_by_id(db, chat_request.agent_id)
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
    
    # Get or create conversation
    if chat_request.conversation_id:
        conversation = await chat_service.get_conversation_by_id(db, chat_request.conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Verify conversation belongs to user
        if conversation.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this conversation"
            )
    else:
        # Create new conversation
        title = chat_service.generate_conversation_title(chat_request.message)
        conversation = await chat_service.create_conversation(
            db, agent.org_id, agent.id, current_user.id, title
        )
    
    # Save user message
    await chat_service.create_message(
        db, conversation.id, "user", chat_request.message
    )
    
    # Get conversation history
    history = await chat_service.get_conversation_history(db, conversation.id)
    
    async def event_generator():
        """Generate SSE events"""
        # Send conversation_id first
        yield f"data: {json.dumps({'conversation_id': str(conversation.id)})}\n\n"
        
        # Stream the response
        full_response = ""
        async for chunk in llm_service.generate_chat_response_stream(
            messages=history,
            system_prompt=agent.system_prompt
        ):
            full_response += chunk
            yield f"data: {json.dumps({'chunk': chunk})}\n\n"
        
        # Save assistant message after streaming completes
        await chat_service.create_message(
            db, conversation.id, "assistant", full_response
        )
        
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream"
    )


@router.get("/history", response_model=List[ConversationResponse])
async def get_conversation_history(
    org_id: UUID,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's conversation history
    """
    # Check if user is a member
    is_member = await organization_service.is_org_member(db, current_user.id, org_id)
    if not is_member:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this organization"
        )
    
    conversations = await chat_service.get_user_conversations(db, current_user.id, org_id, limit)
    return conversations


@router.get("/{conversation_id}", response_model=ConversationWithMessages)
async def get_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get conversation with all messages
    """
    conversation = await chat_service.get_conversation_by_id(db, conversation_id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found"
        )
    
    # Verify conversation belongs to user
    if conversation.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this conversation"
        )
    
    # Get messages
    messages = await chat_service.get_conversation_messages(db, conversation_id)
    
    return ConversationWithMessages(
        **conversation.__dict__,
        messages=[MessageResponse(**msg.__dict__) for msg in messages]
    )
