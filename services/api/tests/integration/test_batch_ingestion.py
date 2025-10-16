"""Integration tests for batch document ingestion."""
from __future__ import annotations

import asyncio
import io
from pathlib import Path

import pytest
from fastapi import status
from httpx import AsyncClient

# Test fixtures directory
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures"


@pytest.mark.asyncio
async def test_batch_ingestion_success(async_client: AsyncClient):
    """Test successful batch ingestion with 10 documents."""
    # Create 10 test documents
    files = []
    for i in range(10):
        content = f"This is test document {i}. It contains sample text for testing batch ingestion.".encode("utf-8")
        files.append(("files", (f"test_doc_{i}.txt", io.BytesIO(content), "text/plain")))

    # Start batch ingestion
    response = await async_client.post(
        "/api/v1/documents/ingest/batch",
        files=files,
    )

    assert response.status_code == status.HTTP_202_ACCEPTED
    result = response.json()
    assert "batchId" in result
    assert result["totalDocuments"] == 10
    assert result["status"] == "in_progress"

    # Poll status until complete
    batch_id = result["batchId"]
    max_retries = 60
    for _ in range(max_retries):
        status_response = await async_client.get(
            f"/api/v1/documents/ingest/batch/{batch_id}/status"
        )
        assert status_response.status_code == status.HTTP_200_OK
        status_data = status_response.json()

        if status_data["status"] in ["completed", "partial_failure"]:
            assert status_data["processedCount"] > 0
            assert status_data["totalDocuments"] == 10
            break

        await asyncio.sleep(2)
    else:
        pytest.fail("Batch processing timeout after 120 seconds")


@pytest.mark.asyncio
async def test_batch_ingestion_with_csv_metadata(async_client: AsyncClient):
    """Test batch ingestion with CSV metadata mapping."""
    # Create 5 test documents
    files = []
    for i in range(5):
        content = f"This is test document {i} with metadata.".encode("utf-8")
        files.append(("files", (f"test_doc_{i}.txt", io.BytesIO(content), "text/plain")))

    # Load CSV metadata mapping
    csv_path = FIXTURES_DIR / "metadata-mapping.csv"
    with open(csv_path, "rb") as f:
        csv_content = f.read()

    files.append(("metadata_mapping", ("metadata-mapping.csv", io.BytesIO(csv_content), "text/csv")))

    # Start batch ingestion
    response = await async_client.post(
        "/api/v1/documents/ingest/batch",
        files=files,
    )

    assert response.status_code == status.HTTP_202_ACCEPTED
    result = response.json()
    batch_id = result["batchId"]

    # Wait for completion
    max_retries = 60
    for _ in range(max_retries):
        status_response = await async_client.get(
            f"/api/v1/documents/ingest/batch/{batch_id}/status"
        )
        status_data = status_response.json()

        if status_data["status"] in ["completed", "partial_failure"]:
            assert status_data["processedCount"] > 0
            break

        await asyncio.sleep(2)
    else:
        pytest.fail("Batch processing timeout")


@pytest.mark.asyncio
async def test_batch_ingestion_with_json_metadata(async_client: AsyncClient):
    """Test batch ingestion with JSON metadata mapping."""
    # Create 3 test documents
    files = []
    for i in range(3):
        content = f"Test document {i} with JSON metadata.".encode("utf-8")
        files.append(("files", (f"test_doc_{i}.txt", io.BytesIO(content), "text/plain")))

    # Load JSON metadata mapping
    json_path = FIXTURES_DIR / "metadata-mapping.json"
    with open(json_path, "rb") as f:
        json_content = f.read()

    files.append(("metadata_mapping", ("metadata-mapping.json", io.BytesIO(json_content), "application/json")))

    # Start batch ingestion
    response = await async_client.post(
        "/api/v1/documents/ingest/batch",
        files=files,
    )

    assert response.status_code == status.HTTP_202_ACCEPTED
    result = response.json()
    batch_id = result["batchId"]

    # Wait for completion
    max_retries = 60
    for _ in range(max_retries):
        status_response = await async_client.get(
            f"/api/v1/documents/ingest/batch/{batch_id}/status"
        )
        status_data = status_response.json()

        if status_data["status"] in ["completed", "partial_failure"]:
            assert status_data["processedCount"] > 0
            break

        await asyncio.sleep(2)
    else:
        pytest.fail("Batch processing timeout")


@pytest.mark.asyncio
async def test_batch_ingestion_partial_failure(async_client: AsyncClient, mock_rag_anything_server):
    """Test batch ingestion handles partial failures gracefully."""
    # Create mix of valid and potentially problematic files
    files = [
        ("files", ("valid_doc.txt", io.BytesIO(b"Valid document content"), "text/plain")),
        ("files", ("empty_doc.txt", io.BytesIO(b""), "text/plain")),  # Empty file might fail
        ("files", ("another_valid.txt", io.BytesIO(b"Another valid document"), "text/plain")),
    ]

    # Start batch ingestion
    response = await async_client.post(
        "/api/v1/documents/ingest/batch",
        files=files,
    )

    assert response.status_code == status.HTTP_202_ACCEPTED
    batch_id = response.json()["batchId"]

    # Wait for completion
    max_retries = 60
    for _ in range(max_retries):
        status_response = await async_client.get(
            f"/api/v1/documents/ingest/batch/{batch_id}/status"
        )
        status_data = status_response.json()

        if status_data["status"] in ["completed", "partial_failure", "failed"]:
            # Should have at least processed some documents
            assert (status_data["processedCount"] + status_data["failedCount"]) == 3
            break

        await asyncio.sleep(2)
    else:
        pytest.fail("Batch processing timeout")


@pytest.mark.asyncio
async def test_batch_status_tracking(async_client: AsyncClient):
    """Test batch status tracking through lifecycle."""
    # Create small batch
    files = [
        ("files", ("doc1.txt", io.BytesIO(b"Document 1"), "text/plain")),
        ("files", ("doc2.txt", io.BytesIO(b"Document 2"), "text/plain")),
    ]

    # Start batch
    response = await async_client.post(
        "/api/v1/documents/ingest/batch",
        files=files,
    )

    assert response.status_code == status.HTTP_202_ACCEPTED
    batch_id = response.json()["batchId"]

    # Check initial status
    status_response = await async_client.get(
        f"/api/v1/documents/ingest/batch/{batch_id}/status"
    )
    assert status_response.status_code == status.HTTP_200_OK
    status_data = status_response.json()

    assert status_data["batchId"] == batch_id
    assert status_data["totalDocuments"] == 2
    assert status_data["status"] in ["in_progress", "completed"]

    # Wait for completion
    max_retries = 60
    for _ in range(max_retries):
        status_response = await async_client.get(
            f"/api/v1/documents/ingest/batch/{batch_id}/status"
        )
        status_data = status_response.json()

        if status_data["status"] in ["completed", "partial_failure"]:
            assert "completedAt" in status_data
            assert "processingTimeSeconds" in status_data
            assert status_data["processingTimeSeconds"] > 0
            break

        await asyncio.sleep(2)
    else:
        pytest.fail("Batch processing timeout")


@pytest.mark.asyncio
async def test_batch_limit_exceeded(async_client: AsyncClient):
    """Test batch ingestion rejects >100 files."""
    # Create 101 files
    files = []
    for i in range(101):
        content = f"Test document {i}".encode("utf-8")
        files.append(("files", (f"test_doc_{i}.txt", io.BytesIO(content), "text/plain")))

    # Should reject
    response = await async_client.post(
        "/api/v1/documents/ingest/batch",
        files=files,
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    error = response.json()
    assert error["error"]["code"] == "BATCH_TOO_LARGE"


@pytest.mark.asyncio
async def test_batch_status_not_found(async_client: AsyncClient):
    """Test batch status endpoint returns 404 for unknown batch."""
    # Query non-existent batch
    response = await async_client.get(
        "/api/v1/documents/ingest/batch/00000000-0000-0000-0000-000000000000/status"
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    error = response.json()
    assert error["error"]["code"] == "BATCH_NOT_FOUND"


@pytest.mark.asyncio
async def test_batch_mixed_file_formats(async_client: AsyncClient):
    """Test batch ingestion with mixed file formats."""
    files = [
        ("files", ("document.txt", io.BytesIO(b"Plain text document"), "text/plain")),
        ("files", ("document.md", io.BytesIO(b"# Markdown Document"), "text/markdown")),
        ("files", ("data.csv", io.BytesIO(b"col1,col2\nval1,val2"), "text/csv")),
    ]

    response = await async_client.post(
        "/api/v1/documents/ingest/batch",
        files=files,
    )

    assert response.status_code == status.HTTP_202_ACCEPTED
    batch_id = response.json()["batchId"]

    # Wait for completion
    max_retries = 60
    for _ in range(max_retries):
        status_response = await async_client.get(
            f"/api/v1/documents/ingest/batch/{batch_id}/status"
        )
        status_data = status_response.json()

        if status_data["status"] in ["completed", "partial_failure"]:
            assert status_data["processedCount"] > 0
            break

        await asyncio.sleep(2)
    else:
        pytest.fail("Batch processing timeout")


@pytest.mark.asyncio
async def test_invalid_metadata_mapping_format(async_client: AsyncClient):
    """Test batch ingestion rejects invalid metadata mapping."""
    files = [
        ("files", ("doc.txt", io.BytesIO(b"Test document"), "text/plain")),
        ("metadata_mapping", ("invalid.xml", io.BytesIO(b"<xml>invalid</xml>"), "application/xml")),
    ]

    response = await async_client.post(
        "/api/v1/documents/ingest/batch",
        files=files,
    )

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    error = response.json()
    assert error["error"]["code"] == "INVALID_METADATA_MAPPING"
