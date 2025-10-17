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

    # Metadata Configuration
    METADATA_SCHEMA_PATH: str = "/app/config/metadata-schema.yaml"

    # Entity Types Configuration
    ENTITY_TYPES_CONFIG_PATH: str = "/app/config/entity-types.yaml"

    # Document Ingestion Configuration
    MAX_FILE_SIZE_MB: int = 50
    RATE_LIMIT_REQUESTS: int = 10
    RATE_LIMIT_WINDOW_SECONDS: int = 60

    # Service URLs
    RAG_ANYTHING_URL: str = "http://rag-anything:8001"

    # LLM Provider Configuration
    LLM_PROVIDER: str = "ollama"  # openai, ollama, azure
    LLM_ENDPOINT: str = ""  # OpenAI-compatible endpoint URL

    # Provider-specific LLM settings
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    ANTHROPIC_API_KEY: str = ""
    AZURE_API_KEY: str = ""
    AZURE_API_BASE: str = ""
    AZURE_API_VERSION: str = "2024-02-15-preview"
    AZURE_DEPLOYMENT_NAME: str = ""
    OLLAMA_BASE_URL: str = "http://host.docker.internal:11434"
    OLLAMA_MODEL: str = "qwen2.5:7b-instruct-q4_K_M"

    # Embedding Provider Configuration
    EMBEDDING_PROVIDER: str = "local"  # local, openai, azure
    LOCAL_EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    EMBEDDING_DIM: int = 384
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    OPENAI_EMBEDDING_DIM: int = 1536

    # LightRAG Configuration (Epic 3.1)
    LIGHTRAG_WORKING_DIR: str = "/app/lightrag_cache"
    LIGHTRAG_MAX_TOKENS: int = 32768
    LIGHTRAG_MAX_EMBED_TOKENS: int = 8192

    def get_cors_origins_list(self) -> list[str]:
        """Get CORS origins as a list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    def get_max_file_size_bytes(self) -> int:
        """Get maximum file size in bytes."""
        return self.MAX_FILE_SIZE_MB * 1024 * 1024

    def get_llm_endpoint(self) -> str:
        """Get LLM endpoint URL based on provider configuration.

        Returns:
            OpenAI-compatible endpoint URL
        """
        # If LLM_ENDPOINT is explicitly set, use it
        if self.LLM_ENDPOINT:
            return self.LLM_ENDPOINT

        # Otherwise derive from provider
        if self.LLM_PROVIDER == "ollama":
            # Ensure /v1 suffix for OpenAI compatibility
            base = self.OLLAMA_BASE_URL.rstrip('/')
            return f"{base}/v1" if not base.endswith('/v1') else base
        elif self.LLM_PROVIDER == "openai":
            return "https://api.openai.com/v1"
        elif self.LLM_PROVIDER == "azure":
            return self.AZURE_API_BASE
        else:
            raise ValueError(f"Unknown LLM provider: {self.LLM_PROVIDER}")

    def get_embedding_model(self) -> str:
        """Get embedding model name based on provider configuration.

        Returns:
            Embedding model identifier
        """
        if self.EMBEDDING_PROVIDER == "local":
            return f"sentence-transformers/{self.LOCAL_EMBEDDING_MODEL}"
        elif self.EMBEDDING_PROVIDER == "openai":
            return self.OPENAI_EMBEDDING_MODEL
        elif self.EMBEDDING_PROVIDER == "azure":
            return self.OPENAI_EMBEDDING_MODEL  # Azure uses same model names
        else:
            raise ValueError(f"Unknown embedding provider: {self.EMBEDDING_PROVIDER}")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # Allow extra env vars in .env file not defined in Settings
    )


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings
