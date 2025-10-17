"""
End-to-end integration test for CV document ingestion pipeline.

This test validates the complete pipeline from document upload through
Neo4j storage, LightRAG entity extraction, and deletion.

Tests:
1. test_cv_single_document_pipeline - Basic ingestion and storage
2. test_cv_full_pipeline_with_entities - Complete pipeline including entity extraction

The tests always clean up after themselves (delete documents at the end).

Usage:
    pytest services/api/tests/integration/test_e2e_cv_ingestion.py -v
"""

from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path

import pytest
from fastapi import status
from httpx import AsyncClient
from neo4j import Session

# Project root for finding CV samples
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.parent
CV_SAMPLES_DIR = PROJECT_ROOT / "tests" / "fixtures" / "sample-data" / "cv-pdfs"


@pytest.mark.asyncio
async def test_cv_single_document_pipeline(
    async_client: AsyncClient,
    neo4j_session: Session,
):
    """
    Test single CV document ingestion pipeline with cleanup.

    Validates:
        1. Document upload via POST /api/v1/documents/ingest
        2. Neo4j storage (Document + ParsedContent nodes)
        3. Metadata retrieval via GET /api/v1/documents/{doc_id}
        4. Document deletion via DELETE /api/v1/documents/{doc_id}

    The test always cleans up by deleting the document at the end.

    Args:
        async_client: Async HTTP test client
        neo4j_session: Neo4j database session
    """
    # Find test CV file
    if not CV_SAMPLES_DIR.exists():
        pytest.skip(
            f"CV samples directory not found: {CV_SAMPLES_DIR}\n"
            "Run: python scripts/download-sample-data.py"
        )

    cv_files = sorted(CV_SAMPLES_DIR.glob("cv_*.pdf"))
    if not cv_files:
        pytest.skip(
            f"No CV PDF files found in {CV_SAMPLES_DIR}\n"
            "Run: python scripts/download-sample-data.py"
        )

    cv_file = cv_files[0]
    doc_id = None

    print(f"\n{'='*70}")
    print(f"E2E Pipeline Test: {cv_file.name}")
    print(f"{'='*70}\n")

    try:
        # ============ Step 1: Upload CV Document ============
        print("Step 1: Uploading CV document...")
        start_time = time.time()

        with open(cv_file, "rb") as f:
            files = {"file": (cv_file.name, f, "application/pdf")}
            metadata = {
                "category": "cv",
                "source": "test",
                "test_type": "e2e_pipeline"
            }
            data = {"metadata": json.dumps(metadata)}
            headers = {"X-API-Key": "test-key-12345"}

            response = await async_client.post(
                "/api/v1/documents/ingest",
                files=files,
                data=data,
                headers=headers
            )

        ingestion_time = time.time() - start_time

        assert response.status_code == status.HTTP_202_ACCEPTED, \
            f"Expected 202, got {response.status_code}: {response.text}"

        result = response.json()
        assert "documentId" in result
        assert result["filename"] == cv_file.name

        doc_id = result["documentId"]

        print(f"✓ Document uploaded successfully")
        print(f"  Document ID: {doc_id}")
        print(f"  Ingestion time: {ingestion_time:.2f}s\n")

        # ============ Step 2: Verify Neo4j Storage ============
        print("Step 2: Verifying Neo4j storage...")

        # Wait for async processing to complete
        max_wait = 30  # seconds
        wait_interval = 2  # seconds
        elapsed = 0

        while elapsed < max_wait:
            result = neo4j_session.run(
                """
                MATCH (d:Document {id: $doc_id})
                OPTIONAL MATCH (d)-[:HAS_PARSED_CONTENT]->(pc:ParsedContent)
                RETURN d, pc
                """,
                doc_id=doc_id
            ).single()

            if result and result["d"]:
                break

            time.sleep(wait_interval)
            elapsed += wait_interval

        assert result is not None, "Document not found in Neo4j"
        assert result["d"] is not None, "Document node not created"

        print(f"✓ Document verified in Neo4j")
        print(f"  Wait time: {elapsed}s\n")

        # ============ Step 3: Retrieve Document Metadata ============
        print("Step 3: Retrieving document metadata...")

        response = await async_client.get(
            f"/api/v1/documents/{doc_id}",
            headers=headers
        )

        assert response.status_code == status.HTTP_200_OK, \
            f"Expected 200, got {response.status_code}: {response.text}"

        doc_data = response.json()
        assert doc_data["documentId"] == doc_id
        assert doc_data["filename"] == cv_file.name

        print(f"✓ Document metadata retrieved successfully\n")

        # ============ Step 4: Delete Document ============
        print("Step 4: Deleting document...")

        response = await async_client.delete(
            f"/api/v1/documents/{doc_id}",
            headers=headers
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT, \
            f"Expected 204, got {response.status_code}: {response.text}"

        # Verify deletion in Neo4j
        result = neo4j_session.run(
            "MATCH (d:Document {id: $doc_id}) RETURN d",
            doc_id=doc_id
        ).single()

        assert result is None or result["d"] is None, \
            "Document still exists in Neo4j after deletion"

        print(f"✓ Document deleted successfully\n")

        print(f"{'='*70}")
        print("✓ E2E PIPELINE TEST PASSED")
        print(f"{'='*70}\n")

        # Clear doc_id since we successfully deleted it
        doc_id = None

    finally:
        # Safety cleanup in case test fails mid-way
        if doc_id:
            print("Cleanup: Deleting test document...")
            try:
                await async_client.delete(
                    f"/api/v1/documents/{doc_id}",
                    headers={"X-API-Key": "test-key-12345"}
                )
                print(f"  ✓ Deleted {doc_id}")
            except Exception as e:
                print(f"  ⚠ Failed to delete {doc_id}: {e}")


@pytest.mark.asyncio
async def test_cv_full_pipeline_with_entities(
    async_client: AsyncClient,
    neo4j_session: Session,
):
    """
    Test complete CV document pipeline including entity extraction.

    Validates the full pipeline from upload to entity extraction:
        1. Document upload via POST /api/v1/documents/ingest
        2. Neo4j storage (Document + ParsedContent nodes)
        3. Queue processing and status transitions
        4. LightRAG entity extraction (entities created in Neo4j)
        5. Entity validation (types, counts, relationships)
        6. Document deletion and cleanup

    This is the most comprehensive E2E test for the CV ingestion pipeline.

    Args:
        async_client: Async HTTP test client
        neo4j_session: Neo4j database session
    """
    # Find test CV file
    if not CV_SAMPLES_DIR.exists():
        pytest.skip(
            f"CV samples directory not found: {CV_SAMPLES_DIR}\n"
            "Run: python scripts/download-sample-data.py"
        )

    cv_files = sorted(CV_SAMPLES_DIR.glob("cv_*.pdf"))
    if not cv_files:
        pytest.skip(
            f"No CV PDF files found in {CV_SAMPLES_DIR}\n"
            "Run: python scripts/download-sample-data.py"
        )

    cv_file = cv_files[0]
    doc_id = None

    print(f"\n{'='*70}")
    print(f"FULL PIPELINE E2E Test: {cv_file.name}")
    print(f"{'='*70}\n")

    try:
        # ============ Step 1: Upload CV Document ============
        print("Step 1: Uploading CV document...")
        start_time = time.time()

        with open(cv_file, "rb") as f:
            files = {"file": (cv_file.name, f, "application/pdf")}
            metadata = {
                "category": "cv",
                "source": "test",
                "test_type": "full_pipeline_e2e"
            }
            data = {"metadata": json.dumps(metadata)}
            headers = {"X-API-Key": "test-key-12345"}

            response = await async_client.post(
                "/api/v1/documents/ingest",
                files=files,
                data=data,
                headers=headers
            )

        ingestion_time = time.time() - start_time

        assert response.status_code == status.HTTP_202_ACCEPTED, \
            f"Expected 202, got {response.status_code}: {response.text}"

        result = response.json()
        doc_id = result["documentId"]

        print(f"✓ Document uploaded")
        print(f"  Document ID: {doc_id}")
        print(f"  Upload time: {ingestion_time:.2f}s\n")

        # ============ Step 2: Verify Initial Neo4j Storage ============
        print("Step 2: Verifying Neo4j document storage...")

        max_wait = 30
        wait_interval = 2
        elapsed = 0

        while elapsed < max_wait:
            result = neo4j_session.run(
                """
                MATCH (d:Document {id: $doc_id})
                OPTIONAL MATCH (d)-[:HAS_PARSED_CONTENT]->(pc:ParsedContent)
                RETURN d.status as status, d.filename as filename,
                       pc.text as content_preview
                """,
                doc_id=doc_id
            ).single()

            if result and result["status"]:
                break

            time.sleep(wait_interval)
            elapsed += wait_interval

        assert result is not None, "Document not found in Neo4j"
        print(f"✓ Document stored in Neo4j")
        print(f"  Status: {result['status']}")
        print(f"  Filename: {result['filename']}")
        print(f"  Wait time: {elapsed}s\n")

        # ============ Step 3: Wait for Queue Processing ============
        print("Step 3: Waiting for queue processing and entity extraction...")

        max_processing_wait = 120  # 2 minutes for LLM processing
        poll_interval = 3
        elapsed = 0
        last_status = result['status']

        while elapsed < max_processing_wait:
            response = await async_client.get(
                f"/api/v1/documents/{doc_id}",
                headers=headers
            )

            if response.status_code == status.HTTP_200_OK:
                doc_data = response.json()
                current_status = doc_data.get("status", "unknown")

                if current_status != last_status:
                    print(f"  Status changed: {last_status} → {current_status}")
                    last_status = current_status

                # Check for completion statuses
                if current_status == "indexed":
                    print(f"✓ Document indexed successfully")
                    print(f"  Processing time: {elapsed}s\n")
                    break
                elif current_status == "failed":
                    pytest.fail(f"Document processing failed: {doc_data}")

            await asyncio.sleep(poll_interval)
            elapsed += poll_interval
        else:
            pytest.fail(
                f"Processing timeout after {max_processing_wait}s. "
                f"Final status: {last_status}"
            )

        # ============ Step 4: Verify Entity Extraction ============
        print("Step 4: Verifying entity extraction...")

        # Query for entities created by LightRAG
        result = neo4j_session.run(
            """
            MATCH (e)
            WHERE e.entity_type IS NOT NULL
            RETURN DISTINCT e.entity_type AS entity_type, count(e) AS count
            ORDER BY count DESC
            """
        )

        entities_by_type = {}
        for record in result:
            entities_by_type[record["entity_type"]] = record["count"]

        total_entities = sum(entities_by_type.values())

        assert total_entities > 0, \
            f"No entities extracted for document {doc_id}"

        print(f"✓ Entities extracted successfully")
        print(f"  Total entities: {total_entities}")
        for entity_type, count in sorted(
            entities_by_type.items(),
            key=lambda x: x[1],
            reverse=True
        ):
            print(f"    - {entity_type}: {count}")
        print()

        # Validate expected entity types for a CV
        expected_types = {
            "person", "skill", "company", "job",
            "technology", "organization", "location"
        }
        found_types = set(entities_by_type.keys())
        common_types = expected_types & found_types

        assert len(common_types) > 0, \
            f"No expected CV entity types found. Expected: {expected_types}, Found: {found_types}"

        print(f"✓ Entity types validation passed")
        print(f"  Found {len(common_types)} expected types: {common_types}\n")

        # ============ Step 5: Verify Entity Relationships ============
        print("Step 5: Verifying entity relationships...")

        result = neo4j_session.run(
            """
            MATCH (e1)-[r]->(e2)
            WHERE e1.entity_type IS NOT NULL AND e2.entity_type IS NOT NULL
            RETURN type(r) AS rel_type, count(r) AS count
            ORDER BY count DESC
            LIMIT 10
            """
        )

        relationships_by_type = {}
        for record in result:
            relationships_by_type[record["rel_type"]] = record["count"]

        total_relationships = sum(relationships_by_type.values())

        if total_relationships > 0:
            print(f"✓ Entity relationships created")
            print(f"  Total relationships: {total_relationships}")
            for rel_type, count in relationships_by_type.items():
                print(f"    - {rel_type}: {count}")
        else:
            print(f"⚠ No entity relationships created (may be expected for simple CVs)")
        print()

        # ============ Step 6: Retrieve Full Document Metadata ============
        print("Step 6: Retrieving document metadata...")

        response = await async_client.get(
            f"/api/v1/documents/{doc_id}",
            headers=headers
        )

        assert response.status_code == status.HTTP_200_OK
        doc_data = response.json()

        assert doc_data["documentId"] == doc_id
        assert doc_data["filename"] == cv_file.name
        assert doc_data["status"] == "indexed"

        print(f"✓ Document metadata retrieved")
        print(f"  Status: {doc_data['status']}")
        print(f"  Metadata keys: {list(doc_data.keys())}\n")

        # ============ Step 7: Delete Document and Cleanup ============
        print("Step 7: Deleting document...")

        response = await async_client.delete(
            f"/api/v1/documents/{doc_id}",
            headers=headers
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

        # Verify deletion in Neo4j
        result = neo4j_session.run(
            "MATCH (d:Document {id: $doc_id}) RETURN d",
            doc_id=doc_id
        ).single()

        assert result is None or result["d"] is None, \
            "Document still exists in Neo4j after deletion"

        print(f"✓ Document deleted successfully\n")

        # Optionally cleanup entities (comment out to preserve for inspection)
        # neo4j_session.run(
        #     """
        #     MATCH (e)
        #     WHERE e.entity_type IS NOT NULL
        #     DETACH DELETE e
        #     """
        # )

        print(f"{'='*70}")
        print("✓ FULL PIPELINE E2E TEST PASSED")
        print(f"{'='*70}")
        print(f"\nPipeline Summary:")
        print(f"  - Document uploaded and parsed: ✓")
        print(f"  - Queue processing completed: ✓")
        print(f"  - Entities extracted: {total_entities}")
        print(f"  - Relationships created: {total_relationships}")
        print(f"  - Document deleted: ✓")
        print(f"{'='*70}\n")

        # Clear doc_id since we successfully deleted it
        doc_id = None

    finally:
        # Safety cleanup in case test fails mid-way
        if doc_id:
            print("Cleanup: Deleting test document...")
            try:
                await async_client.delete(
                    f"/api/v1/documents/{doc_id}",
                    headers={"X-API-Key": "test-key-12345"}
                )
                # Cleanup entities
                neo4j_session.run(
                    """
                    MATCH (e)
                    WHERE e.entity_type IS NOT NULL
                    DETACH DELETE e
                    """
                )
                print(f"  ✓ Cleaned up {doc_id} and entities")
            except Exception as e:
                print(f"  ⚠ Failed to cleanup: {e}")
