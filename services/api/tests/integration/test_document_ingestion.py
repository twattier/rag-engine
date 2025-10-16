"""Integration tests for document ingestion API."""
from __future__ import annotations

import io
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status
from httpx import AsyncClient


@pytest.mark.asyncio
@patch("app.routers.documents.DocumentService")
@patch("app.routers.documents.Neo4jClient")
@patch("app.routers.documents.LightRAGQueue")
async def test_ingest_document_success(
    mock_queue_class,
    mock_neo4j_class,
    mock_doc_service_class,
    async_client: AsyncClient,
    sample_txt_file: io.BytesIO,
    valid_metadata_json: str,
):
    """Test successful document ingestion with metadata."""
    # Setup mocks
    mock_doc_service = AsyncMock()
    mock_doc_service.ingest_document = AsyncMock(
        return_value={
            "document_id": "test-uuid-123",
            "filename": "test.txt",
            "ingestion_status": "parsing",
            "metadata": {},
            "size_bytes": 100,
            "ingestion_date": "2025-10-16T14:30:00Z",
            "parsed_content": {
                "content_list": [
                    {"type": "text", "text": "Test content"},
                    {"type": "image", "image_ref": "img1"},
                ],
                "metadata": {"pages": 1},
            },
            "format": "txt",
        }
    )
    mock_doc_service.calculate_parsed_content_summary = MagicMock(return_value={"text_blocks": 1, "images": 1, "tables": 0, "equations": 0})
    mock_doc_service_class.return_value = mock_doc_service

    mock_neo4j = MagicMock()
    mock_neo4j.session = MagicMock()
    mock_neo4j_class.return_value = mock_neo4j

    mock_queue = AsyncMock()
    mock_queue.enqueue = AsyncMock()
    mock_queue_class.return_value = mock_queue

    # Make request
    files = {"file": ("test.txt", sample_txt_file, "text/plain")}
    data = {"metadata": valid_metadata_json, "expected_entity_types": json.dumps(["person", "organization"])}
    headers = {"X-API-Key": "test-key-12345"}

    response = await async_client.post("/api/v1/documents/ingest", files=files, data=data, headers=headers)

    # Assertions
    assert response.status_code == status.HTTP_202_ACCEPTED
    result = response.json()
    assert "documentId" in result
    assert result["filename"] == "test.txt"
    assert result["ingestionStatus"] == "queued"
    assert "metadata" in result
    assert "sizeBytes" in result
    assert "ingestionDate" in result


@pytest.mark.asyncio
async def test_ingest_file_too_large(
    async_client: AsyncClient,
    large_file_bytes: bytes,
):
    """Test file size limit enforcement (413 response)."""
    files = {"file": ("large.txt", io.BytesIO(large_file_bytes), "text/plain")}
    headers = {"X-API-Key": "test-key-12345"}

    response = await async_client.post("/api/v1/documents/ingest", files=files, headers=headers)

    assert response.status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE
    error = response.json()
    assert "error" in error
    assert error["error"]["code"] == "FILE_TOO_LARGE"
    assert "50MB" in error["error"]["message"]


@pytest.mark.asyncio
async def test_ingest_unsupported_format(
    async_client: AsyncClient,
    sample_txt_file: io.BytesIO,
):
    """Test unsupported file format (400 response)."""
    files = {"file": ("test.exe", sample_txt_file, "application/x-msdownload")}
    headers = {"X-API-Key": "test-key-12345"}

    response = await async_client.post("/api/v1/documents/ingest", files=files, headers=headers)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    error = response.json()
    assert "error" in error
    assert error["error"]["code"] == "UNSUPPORTED_FORMAT"
    assert "exe" in error["error"]["message"]


@pytest.mark.asyncio
@patch("app.routers.documents.validate_document_metadata")
async def test_ingest_invalid_metadata(
    mock_validate,
    async_client: AsyncClient,
    sample_txt_file: io.BytesIO,
):
    """Test invalid metadata (422 response)."""
    # Setup mock to raise validation error
    from fastapi import HTTPException

    mock_validate.side_effect = HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail={
            "error": {
                "code": "INVALID_METADATA",
                "message": "Metadata validation failed",
                "validation_errors": "Missing required field: author",
            }
        },
    )

    files = {"file": ("test.txt", sample_txt_file, "text/plain")}
    data = {"metadata": json.dumps({"version": "invalid"})}
    headers = {"X-API-Key": "test-key-12345"}

    response = await async_client.post("/api/v1/documents/ingest", files=files, data=data, headers=headers)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    error = response.json()
    assert "error" in error
    assert error["error"]["code"] == "INVALID_METADATA"


@pytest.mark.asyncio
async def test_ingest_missing_api_key(
    async_client: AsyncClient,
    sample_txt_file: io.BytesIO,
):
    """Test missing API key (401 response)."""
    files = {"file": ("test.txt", sample_txt_file, "text/plain")}

    response = await async_client.post("/api/v1/documents/ingest", files=files)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    error = response.json()
    assert "error" in error


@pytest.mark.asyncio
async def test_ingest_invalid_api_key(
    async_client: AsyncClient,
    sample_txt_file: io.BytesIO,
):
    """Test invalid API key (401 response)."""
    files = {"file": ("test.txt", sample_txt_file, "text/plain")}
    headers = {"X-API-Key": "bad"}  # Too short (< 5 chars)

    response = await async_client.post("/api/v1/documents/ingest", files=files, headers=headers)

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    error = response.json()
    assert "error" in error


@pytest.mark.asyncio
@patch("app.routers.documents.DocumentService")
async def test_rate_limit_exceeded(
    mock_doc_service_class,
    async_client: AsyncClient,
    sample_txt_file: io.BytesIO,
):
    """Test rate limiting after 10 requests (429 response)."""
    # Setup mock to prevent actual document processing
    mock_doc_service = AsyncMock()
    mock_doc_service_class.return_value = mock_doc_service

    api_key = "test-key-12345"
    headers = {"X-API-Key": api_key}

    # Make 10 requests quickly (should succeed)
    for i in range(10):
        files = {"file": (f"test{i}.txt", io.BytesIO(b"test"), "text/plain")}
        response = await async_client.post("/api/v1/documents/ingest", files=files, headers=headers)

        # First request might fail on other validations, but should not be rate limited
        if response.status_code != status.HTTP_429_TOO_MANY_REQUESTS:
            assert response.status_code in [status.HTTP_202_ACCEPTED, status.HTTP_400_BAD_REQUEST, status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_500_INTERNAL_SERVER_ERROR]

    # 11th request should be rate limited
    files = {"file": ("test11.txt", io.BytesIO(b"test"), "text/plain")}
    response = await async_client.post("/api/v1/documents/ingest", files=files, headers=headers)

    assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    error = response.json()
    assert "error" in error
    assert error["error"]["code"] == "RATE_LIMIT_EXCEEDED"

    # Check rate limit headers
    assert "X-RateLimit-Limit" in response.headers
    assert "X-RateLimit-Remaining" in response.headers
    assert response.headers["X-RateLimit-Remaining"] == "0"


@pytest.mark.asyncio
async def test_ingest_invalid_metadata_json(
    async_client: AsyncClient,
    sample_txt_file: io.BytesIO,
):
    """Test invalid JSON in metadata field (422 response)."""
    files = {"file": ("test.txt", sample_txt_file, "text/plain")}
    data = {"metadata": "not-valid-json{"}
    headers = {"X-API-Key": "test-key-12345"}

    response = await async_client.post("/api/v1/documents/ingest", files=files, data=data, headers=headers)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    error = response.json()
    assert "error" in error
    assert error["error"]["code"] == "INVALID_JSON"


@pytest.mark.asyncio
async def test_ingest_invalid_entity_types_json(
    async_client: AsyncClient,
    sample_txt_file: io.BytesIO,
):
    """Test invalid JSON in expected_entity_types field (422 response)."""
    files = {"file": ("test.txt", sample_txt_file, "text/plain")}
    data = {"expected_entity_types": "not-a-json-array"}
    headers = {"X-API-Key": "test-key-12345"}

    response = await async_client.post("/api/v1/documents/ingest", files=files, data=data, headers=headers)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    error = response.json()
    assert "error" in error
    assert error["error"]["code"] == "INVALID_JSON"
