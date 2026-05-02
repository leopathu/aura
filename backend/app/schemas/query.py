"""Pydantic schemas for RAG query and response."""

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Schema for a RAG query request."""

    query: str = Field(..., min_length=1, max_length=2000, description="The user's question")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of chunks to retrieve")


class SourceChunk(BaseModel):
    """A retrieved source chunk included in the RAG response."""

    document_title: str
    chunk_index: int
    content: str
    similarity: float


class QueryResponse(BaseModel):
    """Schema for a RAG query response."""

    answer: str
    sources: list[SourceChunk]
