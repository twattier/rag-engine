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


# ============ Metadata Testing Fixtures ============

import tempfile
from pathlib import Path
from typing import Generator

from shared.models.metadata import (
    MetadataFieldDefinition,
    MetadataFieldType,
    MetadataSchema,
)


@pytest.fixture
def temp_schema_file() -> Generator[Path, None, None]:
    """Create a temporary schema file for testing.

    Yields:
        Path to temporary YAML schema file
    """
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False
    ) as f:
        f.write("""
metadata_fields:
  - field_name: author
    type: string
    required: true
    description: "Author"
""")
        temp_path = Path(f.name)

    yield temp_path

    # Cleanup
    temp_path.unlink(missing_ok=True)


@pytest.fixture
def temp_invalid_yaml_file() -> Generator[Path, None, None]:
    """Create a temporary file with invalid YAML syntax.

    Yields:
        Path to temporary invalid YAML file
    """
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".yaml", delete=False
    ) as f:
        f.write("invalid: yaml: syntax:")
        temp_path = Path(f.name)

    yield temp_path

    # Cleanup
    temp_path.unlink(missing_ok=True)


@pytest.fixture
def test_metadata_schema() -> MetadataSchema:
    """Create a test metadata schema for API validation tests.

    Returns:
        MetadataSchema with common fields for testing
    """
    return MetadataSchema(
        metadata_fields=[
            MetadataFieldDefinition(
                field_name="author",
                type=MetadataFieldType.STRING,
                required=True,
                description="Author name",
            ),
            MetadataFieldDefinition(
                field_name="version",
                type=MetadataFieldType.INTEGER,
                required=False,
                default=1,
                description="Version number",
            ),
            MetadataFieldDefinition(
                field_name="tags",
                type=MetadataFieldType.TAGS,
                required=False,
                default=[],
                description="Document tags",
            ),
            MetadataFieldDefinition(
                field_name="date_created",
                type=MetadataFieldType.DATE,
                required=False,
                description="Creation date",
            ),
            MetadataFieldDefinition(
                field_name="is_public",
                type=MetadataFieldType.BOOLEAN,
                required=False,
                default=False,
                description="Public visibility",
            ),
        ]
    )


@pytest.fixture
def valid_api_metadata() -> dict:
    """Create valid metadata for API testing.

    Returns:
        Dictionary with valid metadata fields
    """
    return {
        "author": "Jane Smith",
        "version": 2,
        "tags": ["important", "reviewed"],
        "date_created": "2024-10-16",
        "is_public": True,
    }


@pytest.fixture
def invalid_api_metadata_missing_required() -> dict:
    """Create metadata missing required field for API testing.

    Returns:
        Dictionary missing the required 'author' field
    """
    return {
        "version": 1,
        "tags": [],
    }


@pytest.fixture
def invalid_api_metadata_wrong_type() -> dict:
    """Create metadata with wrong field types for API testing.

    Returns:
        Dictionary with incorrect field types
    """
    return {
        "author": "John Doe",
        "version": "not_an_integer",
        "tags": "should_be_list",
    }


@pytest.fixture
def minimal_valid_metadata() -> dict:
    """Create minimal valid metadata (only required fields).

    Returns:
        Dictionary with only the required 'author' field
    """
    return {
        "author": "Test Author",
    }
