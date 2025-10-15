"""
Health check endpoints for monitoring and status verification.
"""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel
from datetime import datetime, timezone

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    service: str
    version: str
    timestamp: datetime


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.

    Returns basic service status. Story 1.4 will enhance this with
    dependency checks (Neo4j, LightRAG, etc.).

    Returns:
        HealthResponse: Service health status
    """
    return HealthResponse(
        status="healthy",
        service="rag-engine-api",
        version="0.1.0",
        timestamp=datetime.now(timezone.utc),
    )
