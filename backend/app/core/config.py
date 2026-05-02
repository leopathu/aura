"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central settings for the Aura backend."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@db:5432/aura"

    # OpenAI
    openai_api_key: str = ""
    embedding_model: str = "text-embedding-3-small"
    llm_model: str = "gpt-4o"
    vector_dimensions: int = 1536

    # RAG pipeline
    chunk_size: int = 512
    chunk_overlap: int = 64
    retrieval_top_k: int = 5

    # Auth / JWT
    secret_key: str = "change-me-in-production-use-a-long-random-string"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24  # 24 hours

    # API
    allowed_origins: list[str] = ["http://localhost:3000", "http://localhost:3001"]
    api_prefix: str = "/api/v1"

    # App
    debug: bool = False
    project_name: str = "Aura RAG"


settings = Settings()
