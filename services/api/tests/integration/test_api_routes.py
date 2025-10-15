"""
Integration tests for FastAPI application routes.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


def test_root_endpoint_returns_200(sync_client: TestClient):
    """Test that root endpoint returns HTTP 200."""
    response = sync_client.get("/")

    assert response.status_code == 200


def test_root_endpoint_returns_api_info(sync_client: TestClient):
    """Test that root endpoint returns API information."""
    response = sync_client.get("/")

    data = response.json()
    assert data["message"] == "RAG Engine API"
    assert data["version"] == "0.1.0"
    assert data["docs_url"] == "/docs"
    assert data["health_url"] == "/health"


def test_health_endpoint_integration(sync_client: TestClient):
    """Integration test for health endpoint."""
    response = sync_client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_openapi_json_accessible(sync_client: TestClient):
    """Test that OpenAPI JSON schema is accessible."""
    response = sync_client.get("/openapi.json")

    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert data["info"]["title"] == "RAG Engine API"
    assert data["info"]["version"] == "0.1.0"


def test_openapi_json_includes_health_endpoint(sync_client: TestClient):
    """Test that OpenAPI schema includes health endpoint."""
    response = sync_client.get("/openapi.json")

    data = response.json()
    assert "/health" in data["paths"]
    assert "get" in data["paths"]["/health"]


def test_openapi_json_includes_root_endpoint(sync_client: TestClient):
    """Test that OpenAPI schema includes root endpoint."""
    response = sync_client.get("/openapi.json")

    data = response.json()
    assert "/" in data["paths"]
    assert "get" in data["paths"]["/"]


def test_swagger_ui_accessible(sync_client: TestClient):
    """Test that Swagger UI documentation is accessible."""
    response = sync_client.get("/docs")

    assert response.status_code == 200
    assert "swagger-ui" in response.text.lower()


def test_redoc_accessible(sync_client: TestClient):
    """Test that ReDoc documentation is accessible."""
    response = sync_client.get("/redoc")

    assert response.status_code == 200
    assert "redoc" in response.text.lower()


def test_cors_headers_present(sync_client: TestClient):
    """Test that CORS headers are configured (middleware is active)."""
    # Make an OPTIONS request (preflight)
    response = sync_client.options(
        "/health",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
        },
    )

    # CORS middleware should add headers
    assert "access-control-allow-origin" in response.headers


def test_health_endpoint_content_type(sync_client: TestClient):
    """Test that health endpoint returns JSON content type."""
    response = sync_client.get("/health")

    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]


def test_root_endpoint_content_type(sync_client: TestClient):
    """Test that root endpoint returns JSON content type."""
    response = sync_client.get("/")

    assert response.status_code == 200
    assert "application/json" in response.headers["content-type"]


@pytest.mark.asyncio
async def test_async_client_health_endpoint(async_client):
    """Test health endpoint with async client."""
    response = await async_client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_async_client_root_endpoint(async_client):
    """Test root endpoint with async client."""
    response = await async_client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "RAG Engine API"


def test_404_for_nonexistent_route(sync_client: TestClient):
    """Test that nonexistent routes return 404."""
    response = sync_client.get("/nonexistent-route")

    assert response.status_code == 404


def test_health_endpoint_multiple_requests(sync_client: TestClient):
    """Test that health endpoint handles multiple requests correctly."""
    # Make multiple requests
    for _ in range(5):
        response = sync_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
