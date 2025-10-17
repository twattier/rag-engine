"""
Pytest configuration and fixtures for API tests.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from neo4j import GraphDatabase, Session

from app.main import app
from app.config import Settings, get_settings


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
        RAG_ANYTHING_URL="http://localhost:8001",
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


# ============ Document Ingestion Testing Fixtures ============

import io


@pytest.fixture
def sample_txt_file() -> io.BytesIO:
    """Create a sample text file for testing.

    Returns:
        BytesIO object with text content
    """
    content = b"This is a sample text document for testing.\n\nMultiple paragraphs included.\n"
    return io.BytesIO(content)


@pytest.fixture
def sample_pdf_bytes() -> bytes:
    """Create sample PDF bytes for testing.

    Returns:
        Bytes representing a minimal PDF
    """
    # Minimal valid PDF content
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
/Resources <<
/Font <<
/F1 5 0 R
>>
>>
>>
endobj
4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
100 700 Td
(Test PDF) Tj
ET
endstream
endobj
5 0 obj
<<
/Type /Font
/Subtype /Type1
/BaseFont /Helvetica
>>
endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000262 00000 n
0000000356 00000 n
trailer
<<
/Size 6
/Root 1 0 R
>>
startxref
447
%%EOF
"""
    return pdf_content


@pytest.fixture
def large_file_bytes() -> bytes:
    """Create a large file (>50MB) for testing size limits.

    Returns:
        Bytes exceeding the MAX_FILE_SIZE limit
    """
    # Create 60MB file
    return b"X" * (60 * 1024 * 1024)


@pytest.fixture
def valid_metadata_json() -> str:
    """Create valid metadata as JSON string for API testing.

    Returns:
        JSON string with valid metadata
    """
    import json

    return json.dumps({"author": "Test Author", "version": 1, "tags": ["test", "api"]})


# ============ E2E Testing Fixtures ============


def pytest_addoption(parser):
    """Add custom pytest command-line options."""
    parser.addoption(
        "--clean",
        action="store_true",
        default=False,
        help="Clean up test data after execution (default: leave persistent)"
    )


@pytest.fixture
def clean_mode(request) -> bool:
    """
    Get clean mode flag from pytest command line.

    Returns:
        bool: True if --clean flag was passed, False otherwise
    """
    return request.config.getoption("--clean")


@pytest.fixture
def neo4j_session() -> Session:
    """
    Create a Neo4j session for integration tests.

    Yields:
        Session: Neo4j database session
    """
    settings = get_settings()
    driver = GraphDatabase.driver(
        settings.NEO4J_URI,
        auth=tuple(settings.NEO4J_AUTH.split("/"))
    )

    with driver.session(database=settings.NEO4J_DATABASE) as session:
        yield session

    driver.close()
