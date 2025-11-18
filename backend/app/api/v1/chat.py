from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List
from app.db.session import get_db
from app.models.models import ChatSession, ChatMessage, Brain, User
from app.schemas.schemas import (
    ChatRequest, ChatResponse, ChatMessageResponse,
    ChatSessionResponse, SearchRequest, SearchResponse, SearchResult
)
from app.api.deps import get_current_user
from app.api.v1.brains import check_brain_access
from app.services.llm_service import llm_service
from app.services.embeddings import embedding_service
from app.services.vector_store import vector_store

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(
    chat_data: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Chat with a brain."""
    # Check brain access
    result = await db.execute(select(Brain).where(Brain.id == chat_data.brain_id))
    brain = result.scalar_one_or_none()
    
    if not brain:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brain not found"
        )
    
    if not await check_brain_access(brain, current_user, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Get or create chat session
    if chat_data.session_id:
        result = await db.execute(
            select(ChatSession)
            .options(selectinload(ChatSession.messages))
            .where(
                ChatSession.id == chat_data.session_id,
                ChatSession.user_id == current_user.id,
                ChatSession.brain_id == chat_data.brain_id
            )
        )
        session = result.scalar_one_or_none()
        
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat session not found"
            )
    else:
        # Create new session
        session = ChatSession(
            user_id=current_user.id,
            brain_id=chat_data.brain_id
        )
        db.add(session)
        await db.flush()
    
    # Save user message
    user_message = ChatMessage(
        session_id=session.id,
        role="user",
        content=chat_data.message
    )
    db.add(user_message)
    await db.commit()
    
    # Get chat history
    chat_history = [
        {"role": msg.role, "content": msg.content}
        for msg in session.messages[-10:]  # Last 10 messages
    ]
    
    # Generate response using RAG
    response_data = await llm_service.generate_response(
        query=chat_data.message,
        brain_id=chat_data.brain_id,
        chat_history=chat_history
    )
    
    # Save assistant message
    assistant_message = ChatMessage(
        session_id=session.id,
        role="assistant",
        content=response_data["answer"],
        sources=response_data["sources"]
    )
    db.add(assistant_message)
    
    # Generate title for new session
    if not session.title:
        title = await llm_service.generate_chat_title(chat_data.message)
        session.title = title
    
    await db.commit()
    await db.refresh(assistant_message)
    
    # Get source documents
    from app.models.models import Document
    doc_ids = [s["document_id"] for s in response_data["sources"]]
    documents = []
    if doc_ids:
        result = await db.execute(
            select(Document).where(Document.id.in_(doc_ids))
        )
        documents = result.scalars().all()
    
    return {
        "session_id": session.id,
        "message": assistant_message,
        "sources": documents
    }


@router.get("/sessions", response_model=List[ChatSessionResponse])
async def list_sessions(
    brain_id: int = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List chat sessions for current user."""
    query = select(ChatSession).where(ChatSession.user_id == current_user.id)
    
    if brain_id:
        query = query.where(ChatSession.brain_id == brain_id)
    
    query = query.order_by(ChatSession.updated_at.desc())
    
    result = await db.execute(query)
    sessions = result.scalars().all()
    
    return sessions


@router.get("/sessions/{session_id}", response_model=ChatSessionResponse)
async def get_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get chat session with messages."""
    result = await db.execute(
        select(ChatSession)
        .options(selectinload(ChatSession.messages))
        .where(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    return session


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete chat session."""
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    await db.delete(session)
    await db.commit()
    
    return None


@router.post("/search", response_model=SearchResponse)
async def search(
    search_data: SearchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Search for documents in a brain."""
    # Check brain access
    result = await db.execute(select(Brain).where(Brain.id == search_data.brain_id))
    brain = result.scalar_one_or_none()
    
    if not brain:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Brain not found"
        )
    
    if not await check_brain_access(brain, current_user, db):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Create embedding for search query
    query_embedding = await embedding_service.create_embedding(search_data.query)
    
    # Search in vector store
    search_results = vector_store.search(
        query_vector=query_embedding,
        brain_id=search_data.brain_id,
        limit=search_data.limit,
        score_threshold=0.5
    )
    
    # Get document info
    from app.models.models import Document
    results = []
    
    for result_item in search_results:
        payload = result_item["payload"]
        doc_id = payload["document_id"]
        
        result = await db.execute(select(Document).where(Document.id == doc_id))
        document = result.scalar_one_or_none()
        
        if document:
            results.append({
                "document": document,
                "score": result_item["score"],
                "content": payload["content"],
                "page": payload.get("page")
            })
    
    return {
        "results": results,
        "query": search_data.query
    }
