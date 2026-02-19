"""
Chat Service
Business logic for chat conversations and message handling
"""

from sqlalchemy.orm import Session
from typing import List, Optional, AsyncGenerator
from uuid import UUID
from datetime import datetime

from app.models.conversation import Conversation, Message
from app.models.agent import Agent


async def create_conversation(
    db: Session,
    org_id: UUID,
    agent_id: UUID,
    user_id: UUID,
    title: Optional[str] = None
) -> Conversation:
    """
    Create a new conversation
    
    Args:
        db: Database session
        org_id: Organization ID
        agent_id: Agent ID
        user_id: User ID
        title: Optional conversation title
        
    Returns:
        Created conversation
    """
    conversation = Conversation(
        org_id=org_id,
        agent_id=agent_id,
        user_id=user_id,
        title=title
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


async def get_conversation_by_id(db: Session, conversation_id: UUID) -> Optional[Conversation]:
    """
    Get conversation by ID
    
    Args:
        db: Database session
        conversation_id: Conversation ID
        
    Returns:
        Conversation or None
    """
    return db.query(Conversation).filter(Conversation.id == conversation_id).first()


async def get_user_conversations(
    db: Session,
    user_id: UUID,
    org_id: UUID,
    limit: int = 50
) -> List[Conversation]:
    """
    Get conversations for a user in an organization
    
    Args:
        db: Database session
        user_id: User ID
        org_id: Organization ID
        limit: Maximum number of conversations
        
    Returns:
        List of conversations
    """
    return (
        db.query(Conversation)
        .filter(
            Conversation.user_id == user_id,
            Conversation.org_id == org_id
        )
        .order_by(Conversation.updated_at.desc())
        .limit(limit)
        .all()
    )


async def create_message(
    db: Session,
    conversation_id: UUID,
    role: str,
    content: str,
    metadata: dict = None
) -> Message:
    """
    Create a new message
    
    Args:
        db: Database session
        conversation_id: Conversation ID
        role: Message role (user/assistant/system)
        content: Message content
        metadata: Optional metadata
        
    Returns:
        Created message
    """
    message = Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
        message_metadata=metadata or {}
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


async def get_conversation_messages(
    db: Session,
    conversation_id: UUID,
    limit: int = 100
) -> List[Message]:
    """
    Get messages for a conversation
    
    Args:
        db: Database session
        conversation_id: Conversation ID
        limit: Maximum number of messages
        
    Returns:
        List of messages
    """
    return (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .limit(limit)
        .all()
    )


async def get_conversation_history(
    db: Session,
    conversation_id: UUID,
    max_messages: int = 10
) -> List[dict]:
    """
    Get conversation history formatted for LLM
    
    Args:
        db: Database session
        conversation_id: Conversation ID
        max_messages: Maximum number of messages to retrieve
        
    Returns:
        List of message dictionaries
    """
    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(max_messages)
        .all()
    )
    
    # Reverse to get chronological order
    messages.reverse()
    
    return [
        {"role": msg.role, "content": msg.content}
        for msg in messages
    ]


def generate_conversation_title(first_message: str, max_length: int = 50) -> str:
    """
    Generate a conversation title from the first message
    
    Args:
        first_message: First user message
        max_length: Maximum title length
        
    Returns:
        Generated title
    """
    # Take first line or sentence
    title = first_message.split('\n')[0].strip()
    
    # Truncate if too long
    if len(title) > max_length:
        title = title[:max_length - 3] + '...'
    
    return title or "New Conversation"
