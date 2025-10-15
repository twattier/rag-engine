"""
Configuration management for RAG Engine API.
Uses Pydantic Settings for type-safe environment variable loading.
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    APP_NAME: str = "RAG Engine API"
    VERSION: str = "0.1.0"

    # API Configuration
    API_PORT: int = 8000
    API_WORKERS: int = 1
    API_KEY: str = "change-me-in-production"
    RATE_LIMIT_PER_MINUTE: int = 100

    # Neo4j Configuration
    NEO4J_URI: str = "bolt://neo4j:7687"
    NEO4J_AUTH: str = "neo4j/password"
    NEO4J_DATABASE: str = "neo4j"

    # CORS Configuration (use string for env var compatibility)
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8080"

    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"

    # Request Configuration
    REQUEST_TIMEOUT: int = 120
    MAX_CONCURRENT_REQUESTS: int = 10

    def get_cors_origins_list(self) -> list[str]:
        """Get CORS origins as a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )


# Global settings instance
settings = Settings()
