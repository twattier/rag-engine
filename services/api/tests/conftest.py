"""
Pytest configuration and fixtures for API tests.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.config import Settings


@pytest.fixture
def test_settings() -> Settings:
    """
    Provide test settings with safe defaults.

    Returns:
        Settings: Test configuration instance
    """
    return Settings(
        APP_NAME="RAG Engine API Test",
        VERSION="0.1.0",
        API_PORT=8000,
        API_KEY="test-api-key",
        NEO4J_URI="bolt://localhost:7687",
        NEO4J_AUTH="neo4j/test",
        NEO4J_DATABASE="neo4j",
        CORS_ORIGINS="http://localhost:3000,http://localhost:8080",
        LOG_LEVEL="DEBUG",
        LOG_FORMAT="json",
    )


@pytest.fixture
def sync_client() -> TestClient:
    """
    Synchronous test client for FastAPI app.

    Returns:
        TestClient: Synchronous test client
    """
    return TestClient(app)


@pytest.fixture
async def async_client() -> AsyncClient:
    """
    Asynchronous test client for FastAPI app.

    Yields:
        AsyncClient: Async HTTP client for testing
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
