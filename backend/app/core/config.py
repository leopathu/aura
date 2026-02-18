"""
Application Configuration
Manages all environment variables and settings
"""

from pydantic_settings import BaseSettings
from typing import List
import json
import os


class Settings(BaseSettings):
    """Application settings from environment variables"""
    
    # Project Info
    PROJECT_NAME: str = "Aura AI Assistant"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    PORT: int = 8001
    
    # Database
    POSTGRES_USER: str = "aura_user"
    POSTGRES_PASSWORD: str = "aura_password"
    POSTGRES_DB: str = "aura_db"
    POSTGRES_HOST: str = "postgres"
    POSTGRES_PORT: int = 5432
    
    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production-min-32-characters-long"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Encryption (for API keys and credentials)
    ENCRYPTION_KEY: str = "your-encryption-key-must-be-32-bytes-url-safe-base64"
    
    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3001", "http://127.0.0.1:3001"]
    
    @property
    def ALLOWED_ORIGINS_PARSED(self) -> List[str]:
        """Parse ALLOWED_ORIGINS if it's a JSON string"""
        if isinstance(self.ALLOWED_ORIGINS, str):
            try:
                return json.loads(self.ALLOWED_ORIGINS)
            except json.JSONDecodeError:
                return [self.ALLOWED_ORIGINS]
        return self.ALLOWED_ORIGINS
    
    # LLM API Keys (optional - users bring their own)
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    
    # OAuth Credentials (for app integrations)
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8001/api/v1/auth/callback/google"
    
    JIRA_CLIENT_ID: str = ""
    JIRA_CLIENT_SECRET: str = ""
    
    SLACK_CLIENT_ID: str = ""
    SLACK_CLIENT_SECRET: str = ""
    
    # Redis (for task queue)
    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    
    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
