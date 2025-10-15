"""
Unit tests for health check router.
"""

from __future__ import annotations

import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

from app.routers.health import health_check, HealthResponse, DependencyHealth, get_neo4j_client


def test_health_response_model_validation():
    """Test HealthResponse Pydantic model validation."""
    # Valid data with dependencies
    valid_data = {
        "status": "healthy",
        "service": "rag-engine-api",
        "version": "0.1.0",
        "dependencies": {
            "neo4j": DependencyHealth(status="healthy", response_time_ms=45.0)
        },
        "timestamp": datetime.now(timezone.utc),
    }
    response = HealthResponse(**valid_data)
    assert response.status == "healthy"
    assert "neo4j" in response.dependencies

    # Test that all fields are required
    with pytest.raises(Exception):  # Pydantic ValidationError
        HealthResponse(status="healthy")  # Missing required fields


def test_dependency_health_model():
    """Test DependencyHealth model."""
    # Healthy dependency
    healthy = DependencyHealth(status="healthy", response_time_ms=50.5)
    assert healthy.status == "healthy"
    assert healthy.response_time_ms == 50.5
    assert healthy.error is None

    # Unhealthy dependency
    unhealthy = DependencyHealth(status="unhealthy", error="Connection failed")
    assert unhealthy.status == "unhealthy"
    assert unhealthy.error == "Connection failed"
    assert unhealthy.response_time_ms is None


@pytest.mark.asyncio
@patch("app.routers.health.get_neo4j_client")
async def test_health_check_with_healthy_neo4j(mock_get_client):
    """Test health check returns healthy when Neo4j is reachable."""
    # Mock Neo4j client
    mock_client = Mock()
    mock_client.verify_connectivity.return_value = (True, 45.0, None)
    mock_get_client.return_value = mock_client

    response = await health_check()

    assert isinstance(response, HealthResponse)
    assert response.status == "healthy"
    assert response.service == "rag-engine-api"
    assert "neo4j" in response.dependencies
    assert response.dependencies["neo4j"].status == "healthy"
    assert response.dependencies["neo4j"].response_time_ms == 45.0
    assert response.dependencies["neo4j"].error is None


@pytest.mark.asyncio
@patch("app.routers.health.get_neo4j_client")
async def test_health_check_with_unhealthy_neo4j(mock_get_client):
    """Test health check returns unhealthy when Neo4j is unreachable."""
    # Mock Neo4j client returning failure
    mock_client = Mock()
    mock_client.verify_connectivity.return_value = (False, None, "ServiceUnavailable: Cannot connect")
    mock_get_client.return_value = mock_client

    response = await health_check()

    # Response should be JSONResponse with 503 status
    assert response.status_code == 503
    data = response.body.decode()
    assert "unhealthy" in data
    assert "neo4j" in data


@pytest.mark.asyncio
@patch("app.routers.health.get_neo4j_client")
async def test_health_check_with_neo4j_exception(mock_get_client):
    """Test health check handles Neo4j client exceptions."""
    # Mock Neo4j client raising exception
    mock_get_client.side_effect = Exception("Connection error")

    response = await health_check()

    # Response should be JSONResponse with 503 status
    assert response.status_code == 503
    data = response.body.decode()
    assert "unhealthy" in data


@patch("app.routers.health.parse_neo4j_auth")
@patch("app.routers.health.Neo4jClient")
def test_get_neo4j_client_singleton(mock_neo4j_client_class, mock_parse_auth):
    """Test that get_neo4j_client returns singleton instance."""
    # Reset the singleton
    import app.routers.health as health_module
    health_module._neo4j_client = None

    mock_parse_auth.return_value = ("neo4j", "password")
    mock_client_instance = Mock()
    mock_neo4j_client_class.return_value = mock_client_instance

    # First call
    client1 = get_neo4j_client()
    # Second call
    client2 = get_neo4j_client()

    # Should be the same instance
    assert client1 == client2
    # Neo4jClient should only be instantiated once
    assert mock_neo4j_client_class.call_count == 1

    # Clean up
    health_module._neo4j_client = None
