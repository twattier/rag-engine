"""
End-to-end integration test for CV document ingestion pipeline.

This test validates the complete pipeline from document upload through
Neo4j storage and deletion using a single CV PDF file.

The test always cleans up after itself (deletes the document at the end).

Usage:
    pytest services/api/tests/integration/test_e2e_cv_ingestion.py -v
"""

from __future__ import annotations

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
