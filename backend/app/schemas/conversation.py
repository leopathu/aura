"""Pydantic schemas for Conversation and ChatMessage resources."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


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
    brain_id: uuid.UUID
    title: str
    created_at: datetime
    updated_at: datetime


class ConversationDetail(BaseModel):
    """Full conversation with all messages."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    brain_id: uuid.UUID
    title: str
    messages: list[ChatMessageResponse]
    created_at: datetime
    updated_at: datetime


class ConversationCreate(BaseModel):
    """Schema for creating a new conversation."""

    brain_id: uuid.UUID
    title: str = "New Chat"


class ChatRequest(BaseModel):
    """Schema for sending a message in a conversation."""

    conversation_id: uuid.UUID | None = None
    brain_id: uuid.UUID
    message: str
    top_k: int = 5
