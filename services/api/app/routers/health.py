"""
Health check endpoints for monitoring and status verification.
"""

from __future__ import annotations

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from datetime import datetime, timezone
from typing import Optional

from app.config import settings
from shared.utils.neo4j_client import Neo4jClient, parse_neo4j_auth
from shared.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


class DependencyHealth(BaseModel):
    """Health status of a dependency."""
    status: str
    response_time_ms: Optional[float] = None
    error: Optional[str] = None


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    service: str
    version: str
    dependencies: dict[str, DependencyHealth]
    timestamp: datetime


# Initialize Neo4j client (singleton)
_neo4j_client: Optional[Neo4jClient] = None


def get_neo4j_client() -> Neo4jClient:
    """Get or create Neo4j client instance."""
    global _neo4j_client
    if _neo4j_client is None:
        username, password = parse_neo4j_auth(settings.NEO4J_AUTH)
        _neo4j_client = Neo4jClient(
            uri=settings.NEO4J_URI,
            auth=(username, password),
            database=settings.NEO4J_DATABASE,
        )
    return _neo4j_client


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint with dependency verification.

    Checks:
    - Neo4j database connectivity and response time

    Returns HTTP 200 if all dependencies are healthy.
    Returns HTTP 503 if any critical dependency is unhealthy.

    Returns:
        HealthResponse: Service health status with dependency checks
    """
    dependencies = {}
    overall_status = "healthy"

    # Check Neo4j connectivity
    try:
        neo4j_client = get_neo4j_client()
        success, response_time_ms, error_msg = neo4j_client.verify_connectivity(retries=3)

        if success:
            dependencies["neo4j"] = DependencyHealth(
                status="healthy",
                response_time_ms=response_time_ms,
            )
        else:
            dependencies["neo4j"] = DependencyHealth(
                status="unhealthy",
                error=error_msg,
            )
            overall_status = "unhealthy"
            logger.error(
                "health_check_neo4j_unhealthy",
                error=error_msg,
            )

    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        dependencies["neo4j"] = DependencyHealth(
            status="unhealthy",
            error=error_msg,
        )
        overall_status = "unhealthy"
        logger.error(
            "health_check_neo4j_exception",
            error=error_msg,
            exc_info=True,
        )

    # Create response
    response_data = HealthResponse(
        status=overall_status,
        service="rag-engine-api",
        version=settings.VERSION,
        dependencies=dependencies,
        timestamp=datetime.now(timezone.utc),
    )

    # Return 503 if unhealthy, 200 if healthy
    if overall_status == "unhealthy":
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=response_data.model_dump(mode="json"),
        )

    return response_data
