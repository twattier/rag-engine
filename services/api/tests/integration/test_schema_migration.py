"""Integration tests for schema migration and reindexing.

Tests backward compatibility validation, schema updates, and document reindexing.
"""

from __future__ import annotations

import asyncio
import pytest
from httpx import AsyncClient
from fastapi import status


@pytest.mark.asyncio
async def test_schema_update_backward_compatible(async_client: AsyncClient):
    """Test schema update with backward compatible changes."""
    # Compatible schema: adds optional field with default
    new_schema = {
        "metadata_fields": [
            {
                "field_name": "author",
                "type": "string",
                "required": False,
                "default": "Unknown",
                "description": "Document author",
            },
            {
                "field_name": "priority",  # New field
                "type": "integer",
                "required": False,
                "default": 3,
                "description": "Document priority (1-5)",
            },
        ]
    }

    response = await async_client.put(
        "/api/v1/config/metadata-schema",
        json=new_schema,
        headers={"Authorization": "Bearer test-api-key"},
    )

    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    assert result["changesDetected"] is True
    assert result["reindexRequired"] is True
    assert "priority" in result["addedFields"]


@pytest.mark.asyncio
async def test_schema_update_breaking_change_rejected(async_client: AsyncClient):
    """Test schema update rejection for breaking changes."""
    # Breaking schema: removes required field
    breaking_schema = {
        "metadata_fields": [
            # Missing 'author' field which is required in base schema
            {
                "field_name": "priority",
                "type": "integer",
                "required": False,
                "default": 3,
                "description": "Priority",
            },
        ]
    }

    response = await async_client.put(
        "/api/v1/config/metadata-schema",
        json=breaking_schema,
        headers={"Authorization": "Bearer test-api-key"},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    error = response.json()
    assert error["error"]["code"] == "SCHEMA_INCOMPATIBLE"
    assert "incompatibilities" in error["error"]
    assert len(error["error"]["incompatibilities"]) > 0


@pytest.mark.asyncio
async def test_schema_update_type_change_rejected(async_client: AsyncClient):
    """Test rejection of field type changes."""
    # Breaking schema: changes field type
    type_change_schema = {
        "metadata_fields": [
            {
                "field_name": "author",
                "type": "integer",  # Changed from string
                "required": False,
                "default": 0,
                "description": "Author",
            },
        ]
    }

    response = await async_client.put(
        "/api/v1/config/metadata-schema",
        json=type_change_schema,
        headers={"Authorization": "Bearer test-api-key"},
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    error = response.json()
    assert error["error"]["code"] == "SCHEMA_INCOMPATIBLE"
    # Check that incompatibility mentions type change
    incomp = error["error"]["incompatibilities"][0]
    assert "type" in incomp["issue"].lower()


@pytest.mark.asyncio
async def test_reindex_trigger_and_status(async_client: AsyncClient):
    """Test triggering reindex and checking status."""
    # Trigger reindex with no filters (all documents)
    reindex_request = {"filters": None}

    response = await async_client.post(
        "/api/v1/documents/reindex",
        json=reindex_request,
        headers={"Authorization": "Bearer test-api-key"},
    )

    assert response.status_code == status.HTTP_202_ACCEPTED
    result = response.json()
    assert "reindexJobId" in result
    assert result["status"] == "in_progress"
    job_id = result["reindexJobId"]

    # Check status immediately
    status_response = await async_client.get(
        f"/api/v1/documents/reindex/{job_id}/status"
    )

    assert status_response.status_code == status.HTTP_200_OK
    status_data = status_response.json()
    assert status_data["reindexJobId"] == job_id
    assert status_data["status"] in ["in_progress", "completed"]
    assert "totalDocuments" in status_data
    assert "processedCount" in status_data


@pytest.mark.asyncio
async def test_reindex_with_filters(async_client: AsyncClient):
    """Test reindexing with document filters."""
    # Reindex only indexed documents
    reindex_request = {
        "filters": {
            "status": "indexed",
            "ingestion_date_from": "2025-10-01",
            "ingestion_date_to": "2025-10-17",
        }
    }

    response = await async_client.post(
        "/api/v1/documents/reindex",
        json=reindex_request,
        headers={"Authorization": "Bearer test-api-key"},
    )

    assert response.status_code == status.HTTP_202_ACCEPTED
    result = response.json()
    assert "reindexJobId" in result


@pytest.mark.asyncio
async def test_reindex_status_not_found(async_client: AsyncClient):
    """Test 404 for non-existent reindex job."""
    fake_job_id = "550e8400-e29b-41d4-a716-446655440000"

    response = await async_client.get(
        f"/api/v1/documents/reindex/{fake_job_id}/status"
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    error = response.json()
    assert error["error"]["code"] == "JOB_NOT_FOUND"


@pytest.mark.asyncio
async def test_reindex_idempotency(async_client: AsyncClient):
    """Test that running reindex multiple times is safe (idempotent)."""
    # Trigger reindex twice
    reindex_request = {"filters": {"status": "indexed"}}

    # First reindex
    response1 = await async_client.post(
        "/api/v1/documents/reindex",
        json=reindex_request,
        headers={"Authorization": "Bearer test-api-key"},
    )
    assert response1.status_code == status.HTTP_202_ACCEPTED
    job_id1 = response1.json()["reindexJobId"]

    # Wait for first to complete
    for _ in range(10):
        status_resp = await async_client.get(
            f"/api/v1/documents/reindex/{job_id1}/status"
        )
        if status_resp.json()["status"] == "completed":
            break
        await asyncio.sleep(0.5)

    # Second reindex (should create new job, same result)
    response2 = await async_client.post(
        "/api/v1/documents/reindex",
        json=reindex_request,
        headers={"Authorization": "Bearer test-api-key"},
    )
    assert response2.status_code == status.HTTP_202_ACCEPTED
    job_id2 = response2.json()["reindexJobId"]

    # Different job IDs but both should succeed
    assert job_id1 != job_id2


@pytest.mark.asyncio
async def test_schema_update_no_changes(async_client: AsyncClient):
    """Test schema update with no actual changes."""
    # Get current schema first
    get_response = await async_client.get("/api/v1/config/metadata-schema")
    current_schema = get_response.json()

    # Submit same schema
    response = await async_client.put(
        "/api/v1/config/metadata-schema",
        json=current_schema,
        headers={"Authorization": "Bearer test-api-key"},
    )

    assert response.status_code == status.HTTP_200_OK
    result = response.json()
    assert result["changesDetected"] is False
    assert result["reindexRequired"] is False
    assert result["reindexStatus"] == "not_required"


@pytest.mark.asyncio
async def test_schema_update_unauthorized(async_client: AsyncClient):
    """Test schema update requires API key."""
    new_schema = {
        "metadata_fields": [
            {
                "field_name": "test",
                "type": "string",
                "required": False,
                "default": "test",
                "description": "Test field",
            },
        ]
    }

    response = await async_client.put(
        "/api/v1/config/metadata-schema",
        json=new_schema,
        # No Authorization header
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
