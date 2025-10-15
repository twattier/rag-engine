"""
Integration tests for health check endpoint with real Neo4j connection.
These tests require Neo4j to be running.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create test client for integration tests."""
    return TestClient(app)


@pytest.mark.integration
def test_health_endpoint_integration(client):
    """
    Integration test for health endpoint with real Neo4j.

    This test requires Neo4j to be running and accessible.
    If Neo4j is not available, the test will verify the unhealthy response.
    """
    response = client.get("/health")

    # Should return either 200 (healthy) or 503 (unhealthy)
    assert response.status_code in [200, 503]

    data = response.json()

    # Verify response structure
    assert "status" in data
    assert "service" in data
    assert "version" in data
    assert "dependencies" in data
    assert "timestamp" in data

    # Verify service metadata
    assert data["service"] == "rag-engine-api"
    assert data["version"] == "0.1.0"

    # Verify dependencies
    assert "neo4j" in data["dependencies"]
    neo4j_health = data["dependencies"]["neo4j"]

    assert "status" in neo4j_health
    assert neo4j_health["status"] in ["healthy", "unhealthy"]

    if data["status"] == "healthy":
        # If healthy, Neo4j should report response time
        assert neo4j_health["response_time_ms"] is not None
        assert neo4j_health["response_time_ms"] > 0
        assert neo4j_health.get("error") is None
    else:
        # If unhealthy, there should be an error message
        assert neo4j_health.get("error") is not None
        assert neo4j_health.get("response_time_ms") is None


@pytest.mark.integration
def test_health_endpoint_response_format(client):
    """Test that health endpoint returns valid JSON with correct schema."""
    response = client.get("/health")

    # Should be valid JSON
    data = response.json()

    # Verify all required fields are present
    required_fields = ["status", "service", "version", "dependencies", "timestamp"]
    for field in required_fields:
        assert field in data, f"Missing required field: {field}"

    # Verify timestamp format (ISO 8601)
    timestamp = data["timestamp"]
    assert "T" in timestamp
    # Should have timezone info
    assert timestamp.endswith("Z") or "+" in timestamp or timestamp.endswith(":00")


@pytest.mark.integration
def test_health_check_neo4j_retry_logic(client):
    """
    Test that health check properly uses retry logic.

    This test verifies the endpoint responds within reasonable time
    even if Neo4j is slow or temporarily unavailable.
    """
    import time

    start_time = time.time()
    response = client.get("/health")
    elapsed_time = time.time() - start_time

    # Health check should complete within 30 seconds even with retries
    # (3 retries with exponential backoff: 1s, 2s, 4s = 7s max + query time)
    assert elapsed_time < 30, f"Health check took too long: {elapsed_time}s"

    # Should still get a response
    assert response.status_code in [200, 503]


@pytest.mark.integration
@pytest.mark.skipif(
    True,
    reason="Manual test - requires Neo4j to be stopped and restarted"
)
def test_health_check_neo4j_failure_recovery(client):
    """
    Manual integration test for Neo4j failure and recovery.

    To run this test:
    1. Start services: docker-compose up -d
    2. Verify health is healthy
    3. Stop Neo4j: docker-compose stop neo4j
    4. Verify health returns 503
    5. Start Neo4j: docker-compose start neo4j
    6. Verify health returns 200
    """
    # Initial check - should be healthy
    response = client.get("/health")
    assert response.status_code == 200

    # Manual step: Stop Neo4j
    input("Stop Neo4j (docker-compose stop neo4j) and press Enter...")

    # Check should now be unhealthy
    response = client.get("/health")
    assert response.status_code == 503
    data = response.json()
    assert data["status"] == "unhealthy"
    assert data["dependencies"]["neo4j"]["status"] == "unhealthy"

    # Manual step: Start Neo4j
    input("Start Neo4j (docker-compose start neo4j) and press Enter...")

    # Wait a few seconds for Neo4j to initialize
    import time
    time.sleep(10)

    # Check should be healthy again
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["dependencies"]["neo4j"]["status"] == "healthy"
