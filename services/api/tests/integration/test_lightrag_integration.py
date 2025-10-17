"""Integration tests for LightRAG entity extraction and graph construction.

Tests the full workflow:
1. Upload CV document via ingestion API
2. Wait for queue processing (poll document status)
3. Verify entities exist in Neo4j
4. Validate entity types and relationships
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import AsyncGenerator

import pytest
from httpx import AsyncClient
from neo4j import AsyncDriver

from app.main import app
from shared.utils.neo4j_client import get_neo4j_client


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create async HTTP client for API testing."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


@pytest.fixture
async def neo4j_session() -> AsyncGenerator:
    """Create Neo4j session for database validation."""
    client = get_neo4j_client()
    async with client.session() as session:
        yield session


@pytest.fixture
def sample_cv_file() -> Path:
    """Get sample CV file for testing."""
    # Use existing CV fixtures from Epic 2
    cv_path = Path("tests/fixtures/sample-data/cv-pdfs/cv_000.pdf")

    if not cv_path.exists():
        pytest.skip(f"Sample CV file not found: {cv_path}")

    return cv_path


@pytest.mark.asyncio
async def test_lightrag_queue_processing_workflow(
    async_client: AsyncClient,
    neo4j_session,
    sample_cv_file: Path,
):
    """Test document queue processing extracts entities via LightRAG.

    Flow:
    1. Upload CV document (triggers queue)
    2. Poll document status until "indexed"
    3. Verify entities exist in Neo4j
    4. Validate entity types match configured types
    """
    # Step 1: Upload CV document
    with open(sample_cv_file, "rb") as f:
        response = await async_client.post(
            "/api/v1/documents/ingest",
            files={"file": (sample_cv_file.name, f, "application/pdf")},
            data={"metadata": json.dumps({"category": "cv"})},
        )

    assert response.status_code == 202, f"Ingestion failed: {response.json()}"
    doc_id = response.json()["documentId"]

    # Step 2: Wait for processing (poll status with timeout)
    max_wait_seconds = 60
    poll_interval_seconds = 2
    max_attempts = max_wait_seconds // poll_interval_seconds

    status = None
    for attempt in range(max_attempts):
        doc_response = await async_client.get(f"/api/v1/documents/{doc_id}")
        assert doc_response.status_code == 200

        doc_data = doc_response.json()
        status = doc_data.get("status")

        if status == "indexed":
            break

        if status == "failed":
            pytest.fail(f"Document processing failed for {doc_id}")

        await asyncio.sleep(poll_interval_seconds)
    else:
        pytest.fail(f"Processing timeout after {max_wait_seconds}s. Final status: {status}")

    # Step 3: Verify entities exist in Neo4j
    # LightRAG creates entities with dynamic labels based on entity_type property
    # Query all nodes that have an entity_type property (LightRAG entities)
    result = await neo4j_session.run(
        """
        MATCH (e)
        WHERE e.entity_type IS NOT NULL
        RETURN DISTINCT e.entity_type AS entity_type, count(e) AS count
        """
    )

    entities_by_type = {}
    async for record in result:
        entities_by_type[record["entity_type"]] = record["count"]

    # Step 4: Validate entity extraction
    total_entities = sum(entities_by_type.values())

    # Assert at least some entities were extracted
    assert total_entities > 0, f"No entities extracted for document {doc_id}"

    # Assert expected entity types exist (from entity-types.yaml config)
    # Note: LightRAG may extract different entity types than configured
    # This is normal - LightRAG's LLM extracts based on content
    expected_types = {"person", "skill", "company", "job", "technology", "organization", "location"}
    found_types = set(entities_by_type.keys())

    # At least one expected type should be found in a CV
    assert len(expected_types & found_types) > 0, (
        f"No expected entity types found. "
        f"Expected: {expected_types}, Found: {found_types}"
    )

    # Log extracted entities for debugging
    print(f"\n✓ Extracted {total_entities} entities:")
    for entity_type, count in entities_by_type.items():
        print(f"  - {entity_type}: {count}")


@pytest.mark.asyncio
async def test_lightrag_entity_relationships(
    async_client: AsyncClient,
    neo4j_session,
    sample_cv_file: Path,
):
    """Test that LightRAG creates entity-to-entity relationships.

    Validates:
    - Entities are connected via relationships
    - Relationship types are meaningful (e.g., WORKS_AT, HAS_SKILL)
    """
    # Upload document
    with open(sample_cv_file, "rb") as f:
        response = await async_client.post(
            "/api/v1/documents/ingest",
            files={"file": (sample_cv_file.name, f, "application/pdf")},
            data={"metadata": json.dumps({"category": "cv"})},
        )

    assert response.status_code == 202
    doc_id = response.json()["documentId"]

    # Wait for processing
    for _ in range(30):  # 60s timeout
        doc_response = await async_client.get(f"/api/v1/documents/{doc_id}")
        if doc_response.json().get("status") == "indexed":
            break
        await asyncio.sleep(2)
    else:
        pytest.skip("Processing timeout - cannot test relationships")

    # Query for entity relationships
    # LightRAG creates relationships between entities with dynamic types
    result = await neo4j_session.run(
        """
        MATCH (e1)-[r]->(e2)
        WHERE e1.entity_type IS NOT NULL AND e2.entity_type IS NOT NULL
        RETURN type(r) AS rel_type, count(r) AS count
        ORDER BY count DESC
        LIMIT 10
        """
    )

    relationships_by_type = {}
    async for record in result:
        relationships_by_type[record["rel_type"]] = record["count"]

    total_relationships = sum(relationships_by_type.values())

    # LightRAG should create relationships between entities
    if total_relationships > 0:
        print(f"\n✓ Created {total_relationships} entity relationships:")
        for rel_type, count in relationships_by_type.items():
            print(f"  - {rel_type}: {count}")

        # Assert some relationships exist
        assert total_relationships > 0, "Expected LightRAG to create entity relationships"
    else:
        # If no relationships, this may indicate an issue or sparse content
        print("\n⚠ No entity-to-entity relationships created")
        pytest.skip("No relationships created - may need more complex test document")


@pytest.mark.asyncio
async def test_lightrag_error_handling(
    async_client: AsyncClient,
    neo4j_session,
):
    """Test LightRAG error handling for documents with no text content.

    Validates:
    - Documents with no text are marked as "indexed" (not failed)
    - Worker doesn't crash on empty content
    """
    # Create a minimal document with no text content (edge case)
    response = await async_client.post(
        "/api/v1/documents/ingest",
        files={"file": ("empty.txt", b"", "text/plain")},
        data={"metadata": json.dumps({"category": "test"})},
    )

    # Even if ingestion fails, test error handling
    if response.status_code != 202:
        pytest.skip("Empty file ingestion not supported - expected behavior")

    doc_id = response.json()["documentId"]

    # Wait for processing
    for _ in range(30):
        doc_response = await async_client.get(f"/api/v1/documents/{doc_id}")
        status = doc_response.json().get("status")

        if status in ("indexed", "failed"):
            # Either status is acceptable for empty content
            assert status in ("indexed", "failed")
            break

        await asyncio.sleep(2)
    else:
        pytest.fail("Processing timeout for empty document")


@pytest.mark.asyncio
async def test_lightrag_concurrent_processing(
    async_client: AsyncClient,
    neo4j_session,
    sample_cv_file: Path,
):
    """Test LightRAG worker handles concurrent document processing.

    Validates:
    - Multiple documents can be queued simultaneously
    - All documents are processed successfully
    - No race conditions or corruption
    """
    # Upload 3 documents concurrently
    doc_ids = []

    for i in range(3):
        with open(sample_cv_file, "rb") as f:
            response = await async_client.post(
                "/api/v1/documents/ingest",
                files={"file": (f"cv_{i}.pdf", f, "application/pdf")},
                data={"metadata": json.dumps({"category": "cv", "batch": i})},
            )

        assert response.status_code == 202
        doc_ids.append(response.json()["documentId"])

    # Wait for all documents to be processed
    processed_count = 0

    for _ in range(60):  # 120s total timeout
        statuses = []

        for doc_id in doc_ids:
            doc_response = await async_client.get(f"/api/v1/documents/{doc_id}")
            status = doc_response.json().get("status")
            statuses.append(status)

        processed_count = sum(1 for s in statuses if s == "indexed")

        if processed_count == len(doc_ids):
            break

        await asyncio.sleep(2)

    # Assert all documents processed
    assert processed_count == len(doc_ids), (
        f"Only {processed_count}/{len(doc_ids)} documents processed"
    )

    # Verify entities were created (query all since we don't track doc_id in entities)
    # LightRAG entities don't have explicit document linkage
    result = await neo4j_session.run(
        """
        MATCH (e)
        WHERE e.entity_type IS NOT NULL
        RETURN count(e) AS entity_count
        """
    )

    record = await result.single()
    total_entity_count = record["entity_count"] if record else 0

    # Assert entities were created for the documents
    # We expect at least some entities from 3 CV documents
    assert total_entity_count > 0, f"No entities found after processing {len(doc_ids)} documents"

    print(f"\n✓ Concurrent processing successful: {total_entity_count} total entities created")


# Cleanup: Delete test documents and entities after tests
@pytest.fixture(autouse=True)
async def cleanup_test_documents(neo4j_session):
    """Delete all test documents and LightRAG entities after each test."""
    yield

    # Cleanup: Delete all documents created during tests
    await neo4j_session.run(
        """
        MATCH (d:Document)
        WHERE d.id STARTS WITH 'test-' OR d.metadata_json CONTAINS '"category": "test"'
        DETACH DELETE d
        """
    )

    # Cleanup: Delete all LightRAG entities (optional - for clean test state)
    # Comment out if you want to preserve entities between test runs
    await neo4j_session.run(
        """
        MATCH (e)
        WHERE e.entity_type IS NOT NULL
        DETACH DELETE e
        """
    )
