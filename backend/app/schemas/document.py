"""Pydantic schemas for Document resources."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DocumentCreate(BaseModel):
    """Schema for creating a new document."""

    title: str = Field(..., min_length=1, max_length=500)
    source: str | None = Field(default=None, max_length=1000)
    content: str = Field(..., min_length=1)


class DocumentUpdate(BaseModel):
    """Schema for updating an existing document."""

    title: str | None = Field(default=None, min_length=1, max_length=500)
    source: str | None = Field(default=None, max_length=1000)


class DocumentResponse(BaseModel):
    """Schema for document responses."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    source: str | None
    embed_status: str
    embed_error: str | None
    created_at: datetime
    updated_at: datetime
