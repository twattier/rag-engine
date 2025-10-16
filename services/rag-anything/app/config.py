"""Configuration for RAG-Anything service."""
from __future__ import annotations

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Service configuration settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Service settings
    SERVICE_NAME: str = "rag-anything"
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    LOG_LEVEL: str = "INFO"

    # File upload settings
    MAX_FILE_SIZE: int = 50 * 1024 * 1024  # 50MB
    UPLOAD_DIR: str = "/tmp/rag-anything-uploads"

    # Supported file formats
    SUPPORTED_FORMATS: list[str] = ["pdf", "txt", "md", "docx", "pptx", "csv"]


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
