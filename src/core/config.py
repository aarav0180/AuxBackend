"""
Application configuration using Pydantic Settings.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Application
    APP_NAME: str = "AUX"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # External API
    JIOSAAVN_API_BASE_URL: str = "https://jiosavan-api-with-playlist.vercel.app"
    EXTERNAL_API_TIMEOUT: float = 10.0
    
    # CORS
    CORS_ORIGINS: list[str] = ["*"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: list[str] = ["*"]
    CORS_ALLOW_HEADERS: list[str] = ["*"]
    
    # Room Settings
    ROOM_CODE_LENGTH: int = 6
    MAX_QUEUE_SIZE: int = 100
    DEFAULT_ROOM_CODE: str = "DEFAULT"
    DEFAULT_ROOM_HOST_ID: str = "system"
    DEFAULT_ROOM_HOST_NAME: str = "VibeSync Radio"
    
    # Security - Encryption (32 bytes for AES-256)
    ENCRYPTION_KEY: str = "VibeSync2025SecureKey1234567890X"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


settings = get_settings()
