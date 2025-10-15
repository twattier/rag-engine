"""
Unit tests for health check router.
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient

from app.routers.health import health_check, HealthResponse


@pytest.mark.asyncio
async def test_health_check_returns_correct_model():
    """Test that health_check returns HealthResponse model."""
    response = await health_check()

    assert isinstance(response, HealthResponse)
    assert response.status == "healthy"
    assert response.service == "rag-engine-api"
    assert response.version == "0.1.0"
    assert isinstance(response.timestamp, datetime)


@pytest.mark.asyncio
async def test_health_check_timestamp_is_utc():
    """Test that health check timestamp is timezone-aware UTC."""
    response = await health_check()

    assert response.timestamp.tzinfo is not None
    assert response.timestamp.tzinfo == timezone.utc


def test_health_endpoint_returns_200(sync_client: TestClient):
    """Test that /health endpoint returns HTTP 200."""
    response = sync_client.get("/health")

    assert response.status_code == 200


def test_health_endpoint_returns_correct_structure(sync_client: TestClient):
    """Test that /health endpoint returns correct JSON structure."""
    response = sync_client.get("/health")

    data = response.json()
    assert "status" in data
    assert "service" in data
    assert "version" in data
    assert "timestamp" in data


def test_health_endpoint_returns_correct_values(sync_client: TestClient):
    """Test that /health endpoint returns correct field values."""
    response = sync_client.get("/health")

    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "rag-engine-api"
    assert data["version"] == "0.1.0"
    # Timestamp should be ISO-8601 format
    assert "T" in data["timestamp"]
    assert "Z" in data["timestamp"]


def test_health_response_model_validation():
    """Test HealthResponse Pydantic model validation."""
    # Valid data
    valid_data = {
        "status": "healthy",
        "service": "rag-engine-api",
        "version": "0.1.0",
        "timestamp": datetime.now(timezone.utc),
    }
    response = HealthResponse(**valid_data)
    assert response.status == "healthy"

    # Test that all fields are required
    with pytest.raises(Exception):  # Pydantic ValidationError
        HealthResponse(status="healthy")  # Missing required fields
