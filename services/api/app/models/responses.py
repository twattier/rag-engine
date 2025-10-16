"""Response models for API endpoints."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DocumentIngestResponse(BaseModel):
    """Response for document ingestion endpoint."""

    document_id: str = Field(..., description="UUID of the ingested document", alias="documentId")
    filename: str = Field(..., description="Original filename")
    ingestion_status: str = Field(
        ...,
        description="Current ingestion status: 'parsing', 'queued', 'indexed', 'failed'",
        alias="ingestionStatus",
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")
    size_bytes: int = Field(..., description="File size in bytes", alias="sizeBytes")
    ingestion_date: str = Field(..., description="ISO 8601 datetime of ingestion", alias="ingestionDate")
    expected_entity_types: Optional[List[str]] = Field(
        default=None, description="Expected entity types for extraction", alias="expectedEntityTypes"
    )
    parsed_content_summary: Optional[Dict[str, int]] = Field(
        default=None, description="Summary of parsed content", alias="parsedContentSummary"
    )

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "documentId": "550e8400-e29b-41d4-a716-446655440000",
                "filename": "document.pdf",
                "ingestionStatus": "queued",
                "metadata": {"author": "John Doe", "department": "Engineering", "tags": ["technical", "api"]},
                "sizeBytes": 1048576,
                "ingestionDate": "2025-10-16T14:30:00Z",
                "expectedEntityTypes": ["person", "organization", "technology"],
                "parsedContentSummary": {"text_blocks": 25, "images": 3, "tables": 2},
            }
        }


class ApiError(BaseModel):
    """Standardized error response."""

    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Human-readable error message")
    fields: Optional[List[Dict[str, str]]] = Field(default=None, description="Field-specific validation errors")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "INVALID_METADATA",
                "message": "Metadata validation failed",
                "fields": [{"field": "date_created", "error": "Invalid date format. Expected ISO 8601 (YYYY-MM-DD)"}],
            }
        }


class ErrorResponse(BaseModel):
    """Wrapper for error responses."""

    error: ApiError = Field(..., description="Error details")

    class Config:
        json_schema_extra = {
            "example": {
                "error": {
                    "code": "FILE_TOO_LARGE",
                    "message": "File size exceeds maximum limit of 50MB. Uploaded file size: 75MB",
                }
            }
        }
