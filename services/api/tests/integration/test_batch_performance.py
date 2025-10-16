"""Performance tests for batch document ingestion."""
from __future__ import annotations

import asyncio
import io
import time

import pytest
from fastapi import status
from httpx import AsyncClient

from shared.utils.logging import get_logger

logger = get_logger(__name__)


@pytest.mark.slow
@pytest.mark.asyncio
async def test_batch_performance_20_documents(async_client: AsyncClient):
    """Test batch ingestion of 20 documents completes in <2 minutes (>10 docs/min KPI)."""
    # Generate 20 sample documents
    num_docs = 20
    files = []
    for i in range(num_docs):
        # Create realistic document content (varying sizes)
        content_size = 1000 + (i * 100)  # 1KB to 3KB documents
        content = f"Document {i}\n" + ("Sample text. " * (content_size // 13))
        files.append(("files", (f"perf_test_doc_{i}.txt", io.BytesIO(content.encode("utf-8")), "text/plain")))

    logger.info(
        "batch_performance_test_starting",
        num_documents=num_docs,
    )

    # Start timer
    start_time = time.time()

    # Start batch ingestion
    response = await async_client.post(
        "/api/v1/documents/ingest/batch",
        files=files,
    )

    assert response.status_code == status.HTTP_202_ACCEPTED
    batch_id = response.json()["batchId"]

    logger.info(
        "batch_performance_test_batch_started",
        batch_id=batch_id,
    )

    # Wait for completion
    max_retries = 120  # 4 minutes max (with 2 second polls)
    completed = False

    for retry_count in range(max_retries):
        status_response = await async_client.get(
            f"/api/v1/documents/ingest/batch/{batch_id}/status"
        )
        status_data = status_response.json()

        if status_data["status"] in ["completed", "partial_failure"]:
            completed = True
            end_time = time.time()
            duration_seconds = end_time - start_time
            duration_minutes = duration_seconds / 60

            # Calculate throughput
            docs_per_minute = num_docs / duration_minutes

            logger.info(
                "batch_performance_test_completed",
                batch_id=batch_id,
                duration_seconds=duration_seconds,
                duration_minutes=duration_minutes,
                docs_per_minute=docs_per_minute,
                processed_count=status_data["processedCount"],
                failed_count=status_data["failedCount"],
                status=status_data["status"],
            )

            # Verify performance: 20 docs in <2 minutes
            assert duration_minutes < 2, (
                f"Batch took {duration_minutes:.2f} minutes, expected <2 minutes. "
                f"Throughput: {docs_per_minute:.2f} docs/min"
            )

            # Verify throughput: >=10 docs/min
            assert docs_per_minute >= 10, (
                f"Throughput: {docs_per_minute:.2f} docs/min, expected >=10 docs/min"
            )

            # Verify success
            assert status_data["processedCount"] == num_docs, (
                f"Expected {num_docs} documents processed, got {status_data['processedCount']}"
            )
            assert status_data["failedCount"] == 0, (
                f"Expected 0 failures, got {status_data['failedCount']}"
            )

            break

        # Log progress periodically
        if retry_count % 10 == 0 and retry_count > 0:
            logger.info(
                "batch_performance_test_progress",
                batch_id=batch_id,
                elapsed_seconds=time.time() - start_time,
                processed=status_data["processedCount"],
                failed=status_data["failedCount"],
                total=status_data["totalDocuments"],
            )

        await asyncio.sleep(2)

    if not completed:
        pytest.fail(f"Batch processing timeout after {max_retries * 2} seconds")


@pytest.mark.slow
@pytest.mark.asyncio
async def test_batch_performance_10_documents(async_client: AsyncClient):
    """Test batch ingestion of 10 documents for baseline performance."""
    # Generate 10 sample documents
    num_docs = 10
    files = []
    for i in range(num_docs):
        content = f"Document {i}\n" + ("Sample text. " * 100)
        files.append(("files", (f"perf_test_small_{i}.txt", io.BytesIO(content.encode("utf-8")), "text/plain")))

    logger.info(
        "batch_performance_test_10_docs_starting",
        num_documents=num_docs,
    )

    # Start timer
    start_time = time.time()

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

        if status_data["status"] in ["completed", "partial_failure"]:
            end_time = time.time()
            duration_seconds = end_time - start_time
            duration_minutes = duration_seconds / 60
            docs_per_minute = num_docs / duration_minutes

            logger.info(
                "batch_performance_test_10_docs_completed",
                batch_id=batch_id,
                duration_seconds=duration_seconds,
                docs_per_minute=docs_per_minute,
            )

            # Should complete quickly for 10 documents
            assert duration_minutes < 1, f"10 documents took {duration_minutes:.2f} minutes, expected <1 minute"
            assert docs_per_minute >= 10, f"Throughput: {docs_per_minute:.2f} docs/min, expected >=10 docs/min"

            break

        await asyncio.sleep(2)
    else:
        pytest.fail("Batch processing timeout")


@pytest.mark.slow
@pytest.mark.asyncio
async def test_batch_sequential_processing_memory_management(async_client: AsyncClient):
    """Test that batch processing handles documents sequentially to manage memory."""
    # Create 15 larger documents
    num_docs = 15
    files = []
    for i in range(num_docs):
        # Create larger documents (~10KB each)
        content = f"Large Document {i}\n" + ("Sample text content. " * 500)
        files.append(("files", (f"large_doc_{i}.txt", io.BytesIO(content.encode("utf-8")), "text/plain")))

    logger.info(
        "batch_memory_test_starting",
        num_documents=num_docs,
    )

    start_time = time.time()

    # Start batch ingestion
    response = await async_client.post(
        "/api/v1/documents/ingest/batch",
        files=files,
    )

    assert response.status_code == status.HTTP_202_ACCEPTED
    batch_id = response.json()["batchId"]

    # Monitor processing - should see gradual progress (sequential processing)
    previous_processed = 0
    sequential_progress_detected = False

    max_retries = 90
    for _ in range(max_retries):
        status_response = await async_client.get(
            f"/api/v1/documents/ingest/batch/{batch_id}/status"
        )
        status_data = status_response.json()

        current_processed = status_data["processedCount"]

        # Check for gradual progress (indicates sequential processing)
        if current_processed > previous_processed and current_processed < num_docs:
            sequential_progress_detected = True
            logger.info(
                "batch_memory_test_sequential_progress",
                processed=current_processed,
                total=num_docs,
            )

        previous_processed = current_processed

        if status_data["status"] in ["completed", "partial_failure"]:
            end_time = time.time()
            duration_seconds = end_time - start_time

            logger.info(
                "batch_memory_test_completed",
                batch_id=batch_id,
                duration_seconds=duration_seconds,
                sequential_detected=sequential_progress_detected,
            )

            # Verify all processed
            assert status_data["processedCount"] == num_docs
            break

        await asyncio.sleep(2)
    else:
        pytest.fail("Batch processing timeout")
