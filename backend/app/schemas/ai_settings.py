"""Pydantic schemas for AI settings."""

from pydantic import BaseModel, ConfigDict, Field


class AISettingsUpdate(BaseModel):
    """Payload to create or update user AI settings."""

    # LLM
    llm_provider: str = Field(default="openai", pattern="^(openai|anthropic|google|ollama)$")
    llm_model: str = Field(default="gpt-4o", min_length=1, max_length=100)
    llm_api_key: str = Field(default="")
    llm_base_url: str = Field(default="http://localhost:11434")
    temperature: float = Field(default=0.2, ge=0.0, le=2.0)

    # Embedding
    embedding_provider: str = Field(
        default="openai", pattern="^(openai|google|ollama)$"
    )
    embedding_model: str = Field(
        default="text-embedding-3-small", min_length=1, max_length=100
    )
    embedding_api_key: str = Field(default="")
    embedding_base_url: str = Field(default="http://localhost:11434")

    # RAG pipeline
    chunk_size: int = Field(default=512, ge=64, le=4096)
    chunk_overlap: int = Field(default=64, ge=0, le=512)
    retrieval_top_k: int = Field(default=5, ge=1, le=20)


class AISettingsResponse(BaseModel):
    """AI settings as returned to the client. API keys are masked."""

    model_config = ConfigDict(from_attributes=True)

    llm_provider: str
    llm_model: str
    llm_api_key_set: bool  # never expose the raw key
    llm_base_url: str
    temperature: float

    embedding_provider: str
    embedding_model: str
    embedding_api_key_set: bool
    embedding_base_url: str

    chunk_size: int
    chunk_overlap: int
    retrieval_top_k: int
