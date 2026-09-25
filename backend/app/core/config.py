import os
import secrets
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Aura - Agentic Data & Knowledge Platform"
    API_V1_STR: str = "/api/v1"
    
    # Environment
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "aura-development-secret-key-change-in-production-min-32-chars")
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "b'G4_yZ0RkL1f_hXq3c8s-Uq7m8Lz4pQ1X3y2a5W9rT7A='")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    ALGORITHM: str = "HS256"
    
    # Database
    # Default to sqlite for quick standalone start, or postgresql+asyncpg for production
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite+aiosqlite:///./aura.db"
    )
    
    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Storage
    STORAGE_DIR: str = os.getenv("STORAGE_DIR", "./storage")
    UPLOAD_MAX_SIZE_MB: int = 50
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000", "*"]
    
    # Query Safety Limits
    SQL_MAX_ROWS: int = 10000
    SQL_DEFAULT_LIMIT: int = 1000
    SQL_QUERY_TIMEOUT_SECONDS: int = 30
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
