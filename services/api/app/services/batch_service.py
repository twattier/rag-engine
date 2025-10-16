"""Batch document ingestion service."""
from __future__ import annotations

import asyncio
import time
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from uuid import UUID, uuid4

from fastapi import UploadFile
from pydantic import BaseModel, Field

from shared.models.metadata import MetadataSchema
from shared.utils.logging import get_logger

if TYPE_CHECKING:
    from app.services.document_service import DocumentService
    from app.services.queue_service import LightRAGQueue
    from shared.utils.neo4j_client import Neo4jClient

logger = get_logger(__name__)


class BatchStatus(BaseModel):
    """Batch processing status."""

    batch_id: UUID = Field(..., description="Batch UUID")
    total_documents: int = Field(..., description="Total number of documents")
    processed_count: int = Field(default=0, description="Number of successfully processed documents")
    failed_count: int = Field(default=0, description="Number of failed documents")
    status: str = Field(..., description="Batch status: 'in_progress', 'completed', 'partial_failure', 'failed'")
    failed_documents: List[Dict[str, str]] = Field(default_factory=list, description="List of failed documents")
    completed_at: Optional[str] = Field(default=None, description="ISO 8601 completion time")
    processing_time_seconds: float = Field(default=0.0, description="Total processing time")


class BatchService:
    """Batch document ingestion service."""

    def __init__(
        self,
        document_service: "DocumentService",
        lightrag_queue: "LightRAGQueue",
        neo4j_client: "Neo4jClient",
        metadata_schema: MetadataSchema,
    ):
        """Initialize batch service.

        Args:
            document_service: Document service instance
            lightrag_queue: LightRAG queue instance
            neo4j_client: Neo4j client instance
            metadata_schema: Metadata schema for validation
        """
        self.document_service = document_service
        self.lightrag_queue = lightrag_queue
        self.neo4j_client = neo4j_client
        self.metadata_schema = metadata_schema
        self.batches: Dict[UUID, BatchStatus] = {}

    async def start_batch(
        self,
        files: List[UploadFile],
        metadata_mapping: Dict[str, Dict[str, Any]],
    ) -> UUID:
        """Start batch ingestion and return batch_id.

        Args:
            files: List of uploaded files
            metadata_mapping: Dict mapping filename to metadata

        Returns:
            Batch UUID
        """
        batch_id = uuid4()

        # Initialize batch status
        batch_status = BatchStatus(
            batch_id=batch_id,
            total_documents=len(files),
            processed_count=0,
            failed_count=0,
            status="in_progress",
            failed_documents=[],
        )
        self.batches[batch_id] = batch_status

        logger.info(
            "batch_ingestion_started",
            batch_id=str(batch_id),
            total_documents=len(files),
        )

        # Start background processing
        asyncio.create_task(
            self._process_batch(batch_id, files, metadata_mapping)
        )

        return batch_id

    async def _process_batch(
        self,
        batch_id: UUID,
        files: List[UploadFile],
        metadata_mapping: Dict[str, Dict[str, Any]],
    ):
        """Process batch documents sequentially.

        Args:
            batch_id: Batch UUID
            files: List of uploaded files
            metadata_mapping: Dict mapping filename to metadata
        """
        batch_status = self.batches[batch_id]
        start_time = time.time()

        # Process files sequentially to limit memory usage
        for file in files:
            try:
                # Get metadata for this file
                metadata = metadata_mapping.get(file.filename, {})

                # Validate metadata against schema
                validated_metadata = self.metadata_schema.validate(metadata)

                # Ingest document (parse with RAG-Anything)
                ingestion_result = await self.document_service.ingest_document(
                    file=file,
                    metadata=validated_metadata,
                    expected_entity_types=None,  # Not supported in batch mode for MVP
                )

                # Note: Neo4j storage and LightRAG queueing are handled within
                # document_service.ingest_document() for now (Story 2.3 implementation)
                # This keeps the integration consistent with single document ingestion

                # Increment processed count
                batch_status.processed_count += 1

                logger.info(
                    "batch_document_processed",
                    batch_id=str(batch_id),
                    filename=file.filename,
                    document_id=ingestion_result["document_id"],
                    progress=f"{batch_status.processed_count + batch_status.failed_count}/{batch_status.total_documents}",
                )

            except Exception as e:
                # Log error and continue processing
                logger.error(
                    "batch_document_processing_failed",
                    batch_id=str(batch_id),
                    filename=file.filename,
                    error=str(e),
                    error_type=type(e).__name__,
                )

                batch_status.failed_count += 1
                batch_status.failed_documents.append({
                    "filename": file.filename,
                    "error": str(e),
                })

        # Update final status
        if batch_status.failed_count == 0:
            batch_status.status = "completed"
        elif batch_status.processed_count > 0:
            batch_status.status = "partial_failure"
        else:
            batch_status.status = "failed"

        batch_status.processing_time_seconds = time.time() - start_time
        batch_status.completed_at = datetime.utcnow().isoformat() + "Z"

        logger.info(
            "batch_processing_completed",
            batch_id=str(batch_id),
            total=batch_status.total_documents,
            processed=batch_status.processed_count,
            failed=batch_status.failed_count,
            status=batch_status.status,
            duration_seconds=batch_status.processing_time_seconds,
        )

    def get_batch_status(self, batch_id: UUID) -> BatchStatus:
        """Get current batch status.

        Args:
            batch_id: Batch UUID

        Returns:
            Batch status

        Raises:
            ValueError: If batch not found
        """
        if batch_id not in self.batches:
            raise ValueError(f"Batch {batch_id} not found")

        return self.batches[batch_id]
