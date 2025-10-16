"""
Shared dependencies for FastAPI routes.
Includes database connections, authentication, etc.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated, Any, Dict

from fastapi import Header, HTTPException, status

from app.config import settings
from app.middleware.rate_limiter import InMemoryRateLimiter
from app.services.document_service import DocumentService
from app.services.queue_service import LightRAGQueue
from shared.config.metadata_loader import load_metadata_schema
from shared.models.metadata import MetadataSchema
from shared.utils.neo4j_client import Neo4jClient, parse_neo4j_auth


async def verify_api_key(
    authorization: Annotated[str | None, Header()] = None
) -> str:
    """
    Verify API key from Authorization header.

    Args:
        authorization: Authorization header value (format: "Bearer <api_key>")

    Returns:
        API key if valid

    Raises:
        HTTPException: If API key is missing or invalid
    """
    if authorization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Parse "Bearer <token>" format
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Expected: 'Bearer <api_key>'",
            headers={"WWW-Authenticate": "Bearer"},
        )

    api_key = parts[1]

    # Validate API key
    if api_key != settings.API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return api_key


# Type alias for dependency injection
APIKeyDep = Annotated[str, Header(dependency=verify_api_key)]


@lru_cache()
def get_metadata_schema() -> MetadataSchema:
    """Load and cache metadata schema.

    Returns:
        Loaded MetadataSchema object

    Raises:
        HTTPException: If schema file cannot be loaded
    """
    try:
        return load_metadata_schema(settings.METADATA_SCHEMA_PATH)
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "SCHEMA_NOT_FOUND",
                    "message": str(e),
                }
            },
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "INVALID_SCHEMA",
                    "message": str(e),
                }
            },
        )


async def validate_document_metadata(
    metadata: Dict[str, Any],
    schema: MetadataSchema = None,
) -> Dict[str, Any]:
    """Validate document metadata against schema.

    Args:
        metadata: Dictionary of metadata fields to validate
        schema: MetadataSchema to validate against (injected by FastAPI)

    Returns:
        Validated metadata dictionary with defaults applied

    Raises:
        HTTPException: If validation fails (HTTP 422)
    """
    if schema is None:
        schema = get_metadata_schema()

    try:
        return schema.validate_metadata(metadata)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": {
                    "code": "INVALID_METADATA",
                    "message": "Metadata validation failed",
                    "validation_errors": str(e),
                }
            },
        )


# Singleton instances for services
_neo4j_client: Neo4jClient | None = None
_rate_limiter: InMemoryRateLimiter | None = None
_document_service: DocumentService | None = None
_lightrag_queue: LightRAGQueue | None = None


def get_neo4j_client() -> Neo4jClient:
    """Get Neo4j client singleton.

    Returns:
        Neo4jClient instance
    """
    global _neo4j_client
    if _neo4j_client is None:
        username, password = parse_neo4j_auth(settings.NEO4J_AUTH)
        _neo4j_client = Neo4jClient(
            uri=settings.NEO4J_URI,
            auth=(username, password),
            database=settings.NEO4J_DATABASE,
        )
    return _neo4j_client


def get_rate_limiter() -> InMemoryRateLimiter:
    """Get rate limiter singleton.

    Returns:
        InMemoryRateLimiter instance
    """
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = InMemoryRateLimiter(
            max_requests=settings.RATE_LIMIT_REQUESTS,
            window_seconds=settings.RATE_LIMIT_WINDOW_SECONDS,
        )
    return _rate_limiter


def get_document_service() -> DocumentService:
    """Get document service singleton.

    Returns:
        DocumentService instance
    """
    global _document_service
    if _document_service is None:
        _document_service = DocumentService(
            settings=settings,
            rag_anything_url=settings.RAG_ANYTHING_URL,
        )
    return _document_service


def get_lightrag_queue() -> LightRAGQueue:
    """Get LightRAG queue singleton.

    Returns:
        LightRAGQueue instance
    """
    global _lightrag_queue
    if _lightrag_queue is None:
        _lightrag_queue = LightRAGQueue()
    return _lightrag_queue
