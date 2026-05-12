"""Pydantic schemas for Conversation and ChatMessage resources."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ChatMessageResponse(BaseModel):
    """Schema for a single chat message."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    role: str
    content: str
    sources_json: str | None
    created_at: datetime


class ConversationSummary(BaseModel):
    """Lightweight conversation for sidebar listing (no messages)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    brain_id: uuid.UUID | None
    agent_id: uuid.UUID | None
    title: str
    created_at: datetime
    updated_at: datetime


class ConversationDetail(BaseModel):
    """Full conversation with all messages."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    brain_id: uuid.UUID | None
    agent_id: uuid.UUID | None
    title: str
    messages: list[ChatMessageResponse]
    created_at: datetime
    updated_at: datetime


class ConversationCreate(BaseModel):
    """Schema for creating a new Brain conversation."""

    brain_id: uuid.UUID
    title: str = "New Chat"


class AgentConversationCreate(BaseModel):
    """Schema for creating a new Agent conversation."""

    title: str = Field(default="New Chat", max_length=255)


class ChatRequest(BaseModel):
    """Schema for sending a message in a Brain conversation."""

    conversation_id: uuid.UUID | None = None
    brain_id: uuid.UUID
    message: str
    top_k: int = 5


class AgentChatRequest(BaseModel):
    """Schema for sending a message to an Agent via SSE streaming."""

    conversation_id: uuid.UUID | None = None
    message: str = Field(..., min_length=1, max_length=4000)


class AgentSourceChunk(BaseModel):
    """A retrieved chunk returned alongside an agent answer as a source citation."""

    document_title: str
    source_url: str | None
    app_type: str
    chunk_index: int
    content: str
    similarity: float
