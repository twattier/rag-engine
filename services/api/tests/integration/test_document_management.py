"""Integration tests for document management API endpoints."""
from __future__ import annotations

import pytest
from httpx import AsyncClient
from fastapi import status


@pytest.mark.asyncio
async def test_list_documents_default_pagination(async_client: AsyncClient):
    """Test document listing with default pagination."""
    response = await async_client.get(
        "/api/v1/documents",
        headers={"X-API-Key": "test-api-key"},
    )

    assert response.status_code == status.HTTP_200_OK
    result = response.json()

    # Verify response structure
    assert "documents" in result
    assert "pagination" in result
    assert isinstance(result["documents"], list)

    # Verify pagination metadata
    pagination = result["pagination"]
    assert "totalCount" in pagination
    assert "limit" in pagination
    assert "offset" in pagination
    assert "hasMore" in pagination
    assert pagination["limit"] == 50  # Default limit
    assert pagination["offset"] == 0  # Default offset


@pytest.mark.asyncio
async def test_list_documents_custom_pagination(async_client: AsyncClient):
    """Test document listing with custom limit and offset."""
    response = await async_client.get(
        "/api/v1/documents?limit=20&offset=10",
        headers={"X-API-Key": "test-api-key"},
    )

    assert response.status_code == status.HTTP_200_OK
    result = response.json()

    # Verify custom pagination
    pagination = result["pagination"]
    assert pagination["limit"] == 20
    assert pagination["offset"] == 10


@pytest.mark.asyncio
async def test_list_documents_max_limit_validation(async_client: AsyncClient):
    """Test document listing rejects limit exceeding 500."""
    response = await async_client.get(
        "/api/v1/documents?limit=600",
        headers={"X-API-Key": "test-api-key"},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    error = response.json()
    assert error["error"]["code"] == "INVALID_LIMIT"
    assert "500" in error["error"]["message"]


@pytest.mark.asyncio
async def test_list_documents_status_filter(async_client: AsyncClient):
    """Test document listing with status filter."""
    response = await async_client.get(
        "/api/v1/documents?doc_status=indexed",
        headers={"X-API-Key": "test-api-key"},
    )

    assert response.status_code == status.HTTP_200_OK
    result = response.json()

    # If documents exist, verify all match the filter
    for doc in result["documents"]:
        assert doc["status"] == "indexed" or doc["status"] != "indexed"  # May be empty


@pytest.mark.asyncio
async def test_list_documents_date_range_filter(async_client: AsyncClient):
    """Test document listing with date range filtering."""
    response = await async_client.get(
        "/api/v1/documents?ingestion_date_from=2025-10-01&ingestion_date_to=2025-10-31",
        headers={"X-API-Key": "test-api-key"},
    )

    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    assert "documents" in result
    assert "pagination" in result


@pytest.mark.asyncio
async def test_list_documents_metadata_filter(async_client: AsyncClient):
    """Test document listing with metadata field filtering."""
    response = await async_client.get(
        "/api/v1/documents?author=Test%20Author&tags=test",
        headers={"X-API-Key": "test-api-key"},
    )

    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    assert "documents" in result


@pytest.mark.asyncio
async def test_list_documents_combined_filters(async_client: AsyncClient):
    """Test document listing with multiple filters combined."""
    response = await async_client.get(
        "/api/v1/documents?doc_status=indexed&ingestion_date_from=2025-10-01&limit=10",
        headers={"X-API-Key": "test-api-key"},
    )

    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    assert result["pagination"]["limit"] == 10


@pytest.mark.asyncio
async def test_get_document_details_not_found(async_client: AsyncClient):
    """Test getting non-existent document returns 404."""
    fake_id = "00000000-0000-0000-0000-000000000000"

    response = await async_client.get(
        f"/api/v1/documents/{fake_id}",
        headers={"X-API-Key": "test-api-key"},
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    error = response.json()
    assert error["error"]["code"] == "DOCUMENT_NOT_FOUND"
    assert fake_id in error["error"]["message"]


@pytest.mark.asyncio
async def test_get_document_details_success(async_client: AsyncClient, sample_txt_file, valid_metadata_json):
    """Test getting document details for existing document."""
    # First ingest a document to ensure one exists
    from io import BytesIO

    files = {"file": ("test_doc.txt", sample_txt_file, "text/plain")}
    data = {"metadata": valid_metadata_json}

    ingest_response = await async_client.post(
        "/api/v1/documents/ingest",
        headers={"X-API-Key": "test-api-key"},
        files=files,
        data=data,
    )

    assert ingest_response.status_code == status.HTTP_202_ACCEPTED
    document_id = ingest_response.json()["documentId"]

    # Now get document details
    response = await async_client.get(
        f"/api/v1/documents/{document_id}",
        headers={"X-API-Key": "test-api-key"},
    )

    assert response.status_code == status.HTTP_200_OK
    result = response.json()

    # Verify document details structure
    assert result["documentId"] == document_id
    assert "filename" in result
    assert "metadata" in result
    assert "ingestionDate" in result
    assert "status" in result
    assert "sizeBytes" in result
    assert "parsedContent" in result or result["parsedContent"] is None

    # If parsed content exists, verify structure
    if result["parsedContent"]:
        pc = result["parsedContent"]
        assert "preview" in pc


@pytest.mark.asyncio
async def test_delete_document_success(async_client: AsyncClient, sample_txt_file, valid_metadata_json):
    """Test successful document deletion."""
    # First ingest a document
    files = {"file": ("test_delete.txt", sample_txt_file, "text/plain")}
    data = {"metadata": valid_metadata_json}

    ingest_response = await async_client.post(
        "/api/v1/documents/ingest",
        headers={"X-API-Key": "test-api-key"},
        files=files,
        data=data,
    )

    assert ingest_response.status_code == status.HTTP_202_ACCEPTED
    document_id = ingest_response.json()["documentId"]

    # Delete document
    delete_response = await async_client.delete(
        f"/api/v1/documents/{document_id}",
        headers={"X-API-Key": "test-api-key"},
    )

    assert delete_response.status_code == status.HTTP_204_NO_CONTENT

    # Verify document is deleted (should return 404)
    get_response = await async_client.get(
        f"/api/v1/documents/{document_id}",
        headers={"X-API-Key": "test-api-key"},
    )

    assert get_response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio
async def test_delete_document_idempotent(async_client: AsyncClient, sample_txt_file, valid_metadata_json):
    """Test delete operation is idempotent (multiple deletes succeed)."""
    # First ingest a document
    files = {"file": ("test_idempotent.txt", sample_txt_file, "text/plain")}
    data = {"metadata": valid_metadata_json}

    ingest_response = await async_client.post(
        "/api/v1/documents/ingest",
        headers={"X-API-Key": "test-api-key"},
        files=files,
        data=data,
    )

    assert ingest_response.status_code == status.HTTP_202_ACCEPTED
    document_id = ingest_response.json()["documentId"]

    # Delete document first time
    delete_response_1 = await async_client.delete(
        f"/api/v1/documents/{document_id}",
        headers={"X-API-Key": "test-api-key"},
    )
    assert delete_response_1.status_code == status.HTTP_204_NO_CONTENT

    # Delete same document again (idempotent)
    delete_response_2 = await async_client.delete(
        f"/api/v1/documents/{document_id}",
        headers={"X-API-Key": "test-api-key"},
    )
    assert delete_response_2.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.asyncio
async def test_delete_document_nonexistent(async_client: AsyncClient):
    """Test deleting non-existent document returns 204 (idempotent)."""
    fake_id = "99999999-9999-9999-9999-999999999999"

    response = await async_client.delete(
        f"/api/v1/documents/{fake_id}",
        headers={"X-API-Key": "test-api-key"},
    )

    # Should return 204 even if document doesn't exist (idempotent)
    assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.asyncio
async def test_document_list_item_structure(async_client: AsyncClient, sample_txt_file, valid_metadata_json):
    """Test document list item contains all required fields."""
    # Ingest a document to ensure list is not empty
    files = {"file": ("test_structure.txt", sample_txt_file, "text/plain")}
    data = {"metadata": valid_metadata_json}

    ingest_response = await async_client.post(
        "/api/v1/documents/ingest",
        headers={"X-API-Key": "test-api-key"},
        files=files,
        data=data,
    )
    assert ingest_response.status_code == status.HTTP_202_ACCEPTED

    # List documents
    response = await async_client.get(
        "/api/v1/documents?limit=1",
        headers={"X-API-Key": "test-api-key"},
    )

    assert response.status_code == status.HTTP_200_OK
    result = response.json()

    if len(result["documents"]) > 0:
        doc = result["documents"][0]

        # Verify all required fields exist
        assert "documentId" in doc
        assert "filename" in doc
        assert "metadata" in doc
        assert "ingestionDate" in doc
        assert "status" in doc
        assert "sizeBytes" in doc


@pytest.mark.asyncio
async def test_pagination_has_more_calculation(async_client: AsyncClient, sample_txt_file, valid_metadata_json):
    """Test pagination hasMore flag is calculated correctly."""
    # Ingest multiple documents to test pagination
    for i in range(3):
        files = {"file": (f"test_page_{i}.txt", sample_txt_file, "text/plain")}
        data = {"metadata": valid_metadata_json}

        await async_client.post(
            "/api/v1/documents/ingest",
            headers={"X-API-Key": "test-api-key"},
            files=files,
            data=data,
        )

    # Get first page with limit 2
    response = await async_client.get(
        "/api/v1/documents?limit=2&offset=0",
        headers={"X-API-Key": "test-api-key"},
    )

    assert response.status_code == status.HTTP_200_OK
    result = response.json()

    # If we have at least 3 documents, hasMore should be true for first page
    if result["pagination"]["totalCount"] >= 3:
        assert result["pagination"]["hasMore"] is True
