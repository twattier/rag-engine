"""Reindexing service for applying schema changes to existing documents.

This module provides background reindexing functionality to apply new metadata
schema defaults to existing documents.
"""

from __future__ import annotations

import asyncio
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

import structlog

from shared.database.document_repository import (
    list_documents,
    update_document_metadata,
)
from shared.models.metadata import MetadataSchema

logger = structlog.get_logger(__name__)


class FailedDocument(BaseModel):
    """Information about a document that failed to reindex.

    Attributes:
        document_id: Document UUID
        error: Error message
    """

    document_id: str
    error: str


class ReindexStatus(BaseModel):
    """Reindex job status tracking.

    Attributes:
        reindex_job_id: Unique job identifier
        total_documents: Total documents to reindex
        processed_count: Number of successfully processed documents
        failed_count: Number of failed documents
        status: Job status (in_progress, completed, failed)
        failed_documents: List of failed documents with errors
        processing_time_seconds: Time spent processing (seconds)
        estimated_completion_time: Estimated completion timestamp (ISO 8601)
        completed_at: Completion timestamp (ISO 8601)
    """

    reindex_job_id: UUID
    total_documents: int
    processed_count: int = 0
    failed_count: int = 0
    status: str = "in_progress"  # in_progress, completed, failed
    failed_documents: List[FailedDocument] = Field(default_factory=list)
    processing_time_seconds: float = 0.0
    estimated_completion_time: Optional[str] = None
    completed_at: Optional[str] = None


class ReindexService:
    """Service for reindexing documents with new metadata schema."""

    def __init__(self):
        """Initialize reindex service with in-memory job tracking."""
        self.jobs: Dict[UUID, ReindexStatus] = {}

    async def start_reindex(
        self,
        session: Any,
        filters: Dict[str, Any],
        new_schema: MetadataSchema,
    ) -> UUID:
        """Start reindexing job in background.

        Args:
            session: Neo4j session (passed to background task)
            filters: Filter criteria for documents to reindex
            new_schema: New metadata schema to apply

        Returns:
            Job ID for tracking progress
        """
        job_id = uuid4()

        # Query documents matching filters
        documents = await list_documents(session, filters, limit=10000, offset=0)
        total_docs = len(documents)

        # Initialize job status
        job_status = ReindexStatus(
            reindex_job_id=job_id,
            total_documents=total_docs,
        )
        self.jobs[job_id] = job_status

        logger.info(
            "reindex_job_started",
            job_id=str(job_id),
            total_documents=total_docs,
            filters=filters,
        )

        # Start background processing (don't await - let it run async)
        asyncio.create_task(
            self._process_reindex(session, job_id, documents, new_schema)
        )

        return job_id

    async def _process_reindex(
        self,
        session: Any,
        job_id: UUID,
        documents: List[Dict[str, Any]],
        new_schema: MetadataSchema,
    ) -> None:
        """Process reindexing in background.

        Args:
            session: Neo4j session
            job_id: Job identifier
            documents: List of documents to reindex
            new_schema: New metadata schema
        """
        job_status = self.jobs[job_id]
        start_time = time.time()

        for doc in documents:
            try:
                # Load current metadata
                metadata = doc.get("metadata", {})

                # Apply new schema defaults for missing fields
                for field_def in new_schema.metadata_fields:
                    if (
                        field_def.field_name not in metadata
                        and field_def.default is not None
                    ):
                        metadata[field_def.field_name] = field_def.default

                # Validate metadata against new schema
                validated_metadata = new_schema.validate_metadata(metadata)

                # Update document in Neo4j
                await update_document_metadata(
                    session=session,
                    document_id=doc["document_id"],
                    metadata=validated_metadata,
                )

                job_status.processed_count += 1

                # Update estimated completion time
                if job_status.processed_count > 0:
                    elapsed = time.time() - start_time
                    avg_time_per_doc = elapsed / job_status.processed_count
                    remaining_docs = job_status.total_documents - job_status.processed_count
                    remaining_seconds = avg_time_per_doc * remaining_docs

                    estimated_completion = datetime.now(timezone.utc).timestamp() + remaining_seconds
                    job_status.estimated_completion_time = datetime.fromtimestamp(
                        estimated_completion, tz=timezone.utc
                    ).isoformat()

            except Exception as e:
                logger.error(
                    "reindex_document_failed",
                    job_id=str(job_id),
                    document_id=doc.get("document_id", "unknown"),
                    error=str(e),
                )

                job_status.failed_count += 1
                job_status.failed_documents.append(
                    FailedDocument(
                        document_id=doc.get("document_id", "unknown"),
                        error=str(e),
                    )
                )

        # Update final status
        if job_status.failed_count == 0:
            job_status.status = "completed"
        elif job_status.processed_count > 0:
            job_status.status = "completed"  # Partial success
        else:
            job_status.status = "failed"

        job_status.processing_time_seconds = time.time() - start_time
        job_status.completed_at = datetime.now(timezone.utc).isoformat()
        job_status.estimated_completion_time = None

        logger.info(
            "reindex_job_completed",
            job_id=str(job_id),
            total=job_status.total_documents,
            processed=job_status.processed_count,
            failed=job_status.failed_count,
            duration_seconds=job_status.processing_time_seconds,
        )

    def get_reindex_status(self, job_id: UUID) -> Optional[ReindexStatus]:
        """Get reindex job status.

        Args:
            job_id: Job identifier

        Returns:
            Job status or None if not found
        """
        return self.jobs.get(job_id)
