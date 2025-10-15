"""
Shared dependencies for FastAPI routes.
Includes database connections, authentication, etc.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Header, HTTPException, status

from app.config import settings


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
