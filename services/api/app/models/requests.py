"""Request models for API endpoints."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class IngestDocumentRequest(BaseModel):
    """Request model for document ingestion (for documentation purposes)."""

    # Note: This is primarily for OpenAPI documentation
    # Actual multipart/form-data handling is done in the router
    metadata: Optional[Dict[str, Any]] = Field(default=None, description="Custom metadata fields (JSON string)")
    expected_entity_types: Optional[List[str]] = Field(
        default=None, description="Expected entity types for extraction (JSON array)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "metadata": {"author": "John Doe", "department": "Engineering", "tags": ["technical", "api"]},
                "expected_entity_types": ["person", "organization", "technology"],
            }
        }


class ReindexFilters(BaseModel):
    """Filters for reindexing documents.

    Attributes:
        document_ids: List of specific document IDs to reindex
        ingestion_date_from: Start date for ingestion date filter (ISO 8601)
        ingestion_date_to: End date for ingestion date filter (ISO 8601)
        status: Document status filter
        metadata: Metadata field filters
    """

    document_ids: Optional[List[str]] = Field(
        default=None,
        description="List of document IDs to reindex",
    )
    ingestion_date_from: Optional[str] = Field(
        default=None,
        description="Filter documents from this ingestion date (ISO 8601)",
    )
    ingestion_date_to: Optional[str] = Field(
        default=None,
        description="Filter documents to this ingestion date (ISO 8601)",
    )
    status: Optional[str] = Field(
        default=None,
        description="Filter by document status",
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Filter by metadata fields",
    )


class ReindexRequest(BaseModel):
    """Request model for triggering document reindexing.

    Attributes:
        filters: Optional filters to select specific documents
    """

    filters: Optional[ReindexFilters] = Field(
        default=None,
        description="Filters to select documents for reindexing",
    )

    class Config:
        json_schema_extra = {
            "example": {
                "filters": {
                    "ingestion_date_from": "2025-10-01",
                    "ingestion_date_to": "2025-10-16",
                    "status": "indexed",
                    "metadata": {"department": "engineering"},
                }
            }
        }
