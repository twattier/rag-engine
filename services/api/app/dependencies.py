"""
Shared dependencies for FastAPI routes.
Includes database connections, authentication, etc.
"""

from __future__ import annotations

from functools import lru_cache
from typing import Annotated, Any, Dict

from fastapi import Header, HTTPException, status

from app.config import settings
from shared.config.metadata_loader import load_metadata_schema
from shared.models.metadata import MetadataSchema


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
