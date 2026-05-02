"""Pydantic schemas for Brain resources."""

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BrainCreate(BaseModel):
    """Schema for creating a new brain."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)


class BrainUpdate(BaseModel):
    """Schema for updating an existing brain."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=2000)


class BrainDocumentResponse(BaseModel):
    """A document associated with a brain."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    source: str | None
    created_at: datetime
    embed_status: str
    embed_error: str | None


class BrainResponse(BaseModel):
    """Schema for brain responses."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    description: str | None
    user_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
