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


class FailedDocument(BaseModel):
    """Failed document information."""

    filename: str = Field(..., description="Filename that failed")
    error: str = Field(..., description="Error message")


class BatchIngestResponse(BaseModel):
    """Response for batch ingestion endpoint."""

    batch_id: str = Field(..., description="UUID of the batch", alias="batchId")
    total_documents: int = Field(..., description="Total number of documents in batch", alias="totalDocuments")
    status: str = Field(..., description="Batch status: 'in_progress'")
    message: str = Field(..., description="Status message")

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "batchId": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
                "totalDocuments": 50,
                "status": "in_progress",
                "message": "Batch ingestion started. Use batch_id to check status",
            }
        }


class BatchStatusResponse(BaseModel):
    """Response for batch status endpoint."""

    batch_id: str = Field(..., description="UUID of the batch", alias="batchId")
    total_documents: int = Field(..., description="Total number of documents", alias="totalDocuments")
    processed_count: int = Field(..., description="Number of successfully processed documents", alias="processedCount")
    failed_count: int = Field(..., description="Number of failed documents", alias="failedCount")
    status: str = Field(
        ..., description="Batch status: 'in_progress', 'completed', 'partial_failure'", alias="status"
    )
    failed_documents: List[FailedDocument] = Field(
        default_factory=list, description="List of failed documents", alias="failedDocuments"
    )
    completed_at: Optional[str] = Field(default=None, description="ISO 8601 completion time", alias="completedAt")
    processing_time_seconds: Optional[float] = Field(
        default=None, description="Total processing time in seconds", alias="processingTimeSeconds"
    )

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "batchId": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
                "totalDocuments": 50,
                "processedCount": 48,
                "failedCount": 2,
                "status": "completed",
                "failedDocuments": [
                    {"filename": "corrupted.pdf", "error": "Failed to parse PDF: File is corrupted"},
                    {
                        "filename": "invalid.txt",
                        "error": "Metadata validation failed: Missing required field 'author'",
                    },
                ],
                "completedAt": "2025-10-16T14:35:00Z",
                "processingTimeSeconds": 120.5,
            }
        }


class DocumentListItem(BaseModel):
    """Document list item for paginated responses."""

    document_id: str = Field(..., description="UUID of the document", alias="documentId")
    filename: str = Field(..., description="Original filename")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")
    ingestion_date: str = Field(..., description="ISO 8601 datetime of ingestion", alias="ingestionDate")
    status: str = Field(..., description="Document status: 'parsing', 'queued', 'indexed', 'failed'")
    size_bytes: int = Field(..., description="File size in bytes", alias="sizeBytes")

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "documentId": "550e8400-e29b-41d4-a716-446655440000",
                "filename": "technical-spec.pdf",
                "metadata": {
                    "author": "John Doe",
                    "department": "engineering",
                    "tags": ["technical", "api"],
                },
                "ingestionDate": "2025-10-16T14:30:00Z",
                "status": "indexed",
                "sizeBytes": 1048576,
            }
        }


class PaginationMetadata(BaseModel):
    """Pagination metadata for list responses."""

    total_count: int = Field(..., description="Total number of matching documents", alias="totalCount")
    limit: int = Field(..., description="Number of documents per page")
    offset: int = Field(..., description="Pagination offset")
    has_more: bool = Field(..., description="Whether more documents are available", alias="hasMore")

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "totalCount": 150,
                "limit": 50,
                "offset": 0,
                "hasMore": True,
            }
        }


class DocumentListResponse(BaseModel):
    """Response for document list endpoint."""

    documents: List[DocumentListItem] = Field(..., description="List of documents")
    pagination: PaginationMetadata = Field(..., description="Pagination metadata")

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "documents": [
                    {
                        "documentId": "550e8400-e29b-41d4-a716-446655440000",
                        "filename": "technical-spec.pdf",
                        "metadata": {
                            "author": "John Doe",
                            "department": "engineering",
                            "tags": ["technical", "api"],
                        },
                        "ingestionDate": "2025-10-16T14:30:00Z",
                        "status": "indexed",
                        "sizeBytes": 1048576,
                    }
                ],
                "pagination": {
                    "totalCount": 150,
                    "limit": 50,
                    "offset": 0,
                    "hasMore": True,
                },
            }
        }


class ParsedContentPreview(BaseModel):
    """Parsed content preview for document details."""

    format: Optional[str] = Field(None, description="File format (pdf, docx, etc.)")
    page_count: Optional[int] = Field(None, description="Number of pages", alias="pageCount")
    text_blocks: Optional[int] = Field(None, description="Number of text blocks", alias="textBlocks")
    images: Optional[int] = Field(None, description="Number of images")
    tables: Optional[int] = Field(None, description="Number of tables")
    preview: str = Field(..., description="First 500 characters of content")

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "format": "pdf",
                "pageCount": 25,
                "textBlocks": 120,
                "images": 5,
                "tables": 3,
                "preview": "This technical specification document describes the API architecture...",
            }
        }


class DocumentDetail(BaseModel):
    """Detailed document response."""

    document_id: str = Field(..., description="UUID of the document", alias="documentId")
    filename: str = Field(..., description="Original filename")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Document metadata")
    ingestion_date: str = Field(..., description="ISO 8601 datetime of ingestion", alias="ingestionDate")
    status: str = Field(..., description="Document status: 'parsing', 'queued', 'indexed', 'failed'")
    size_bytes: int = Field(..., description="File size in bytes", alias="sizeBytes")
    parsed_content: Optional[ParsedContentPreview] = Field(
        None, description="Parsed content preview", alias="parsedContent"
    )

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "documentId": "550e8400-e29b-41d4-a716-446655440000",
                "filename": "technical-spec.pdf",
                "metadata": {
                    "author": "John Doe",
                    "department": "engineering",
                    "tags": ["technical", "api"],
                    "date_created": "2025-10-15",
                },
                "ingestionDate": "2025-10-16T14:30:00Z",
                "status": "indexed",
                "sizeBytes": 1048576,
                "parsedContent": {
                    "format": "pdf",
                    "pageCount": 25,
                    "textBlocks": 120,
                    "images": 5,
                    "tables": 3,
                    "preview": "This technical specification document describes the API architecture...",
                },
            }
        }


class SchemaUpdateResponse(BaseModel):
    """Response for metadata schema update endpoint."""

    message: str = Field(..., description="Status message")
    schema_version: str = Field(..., description="Schema version identifier", alias="schemaVersion")
    changes_detected: bool = Field(..., description="Whether changes were detected", alias="changesDetected")
    reindex_required: bool = Field(..., description="Whether reindexing is required", alias="reindexRequired")
    reindex_status: str = Field(..., description="Reindex status (pending, not_required)", alias="reindexStatus")
    added_fields: List[str] = Field(default_factory=list, description="List of added fields", alias="addedFields")
    removed_fields: List[str] = Field(default_factory=list, description="List of removed fields", alias="removedFields")
    modified_fields: List[str] = Field(
        default_factory=list, description="List of modified fields", alias="modifiedFields"
    )

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "message": "Metadata schema updated successfully",
                "schemaVersion": "2.0",
                "changesDetected": True,
                "reindexRequired": True,
                "reindexStatus": "pending",
                "addedFields": ["priority"],
                "removedFields": [],
                "modifiedFields": [],
            }
        }


class SchemaIncompatibility(BaseModel):
    """Schema incompatibility details."""

    field: str = Field(..., description="Field name with incompatibility")
    issue: str = Field(..., description="Description of the incompatibility")


class SchemaIncompatibilityError(BaseModel):
    """Error response for incompatible schema changes."""

    code: str = Field(default="SCHEMA_INCOMPATIBLE", description="Error code")
    message: str = Field(..., description="Error message")
    incompatibilities: List[SchemaIncompatibility] = Field(..., description="List of incompatibilities")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "SCHEMA_INCOMPATIBLE",
                "message": "Schema update rejected: Breaking changes detected",
                "incompatibilities": [
                    {"field": "author", "issue": "Cannot change required field to optional"},
                    {"field": "date_created", "issue": "Cannot change field type from 'date' to 'string'"},
                    {"field": "department", "issue": "Cannot remove required field"},
                ],
            }
        }


class ReindexFailedDocument(BaseModel):
    """Failed document info for reindexing."""

    document_id: str = Field(..., description="Document UUID", alias="documentId")
    error: str = Field(..., description="Error message")

    class Config:
        populate_by_name = True


class ReindexResponse(BaseModel):
    """Response for reindex trigger endpoint."""

    reindex_job_id: str = Field(..., description="UUID of reindex job", alias="reindexJobId")
    total_documents: int = Field(..., description="Total documents to reindex", alias="totalDocuments")
    status: str = Field(..., description="Job status (in_progress)")
    message: str = Field(..., description="Status message")

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "reindexJobId": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
                "totalDocuments": 150,
                "status": "in_progress",
                "message": "Reindexing started. Use reindex_job_id to check status",
            }
        }


class ReindexStatusResponse(BaseModel):
    """Response for reindex status endpoint."""

    reindex_job_id: str = Field(..., description="UUID of reindex job", alias="reindexJobId")
    total_documents: int = Field(..., description="Total documents", alias="totalDocuments")
    processed_count: int = Field(..., description="Number processed", alias="processedCount")
    failed_count: int = Field(..., description="Number failed", alias="failedCount")
    status: str = Field(..., description="Job status (in_progress, completed, failed)")
    estimated_completion_time: Optional[str] = Field(
        default=None, description="Estimated completion time (ISO 8601)", alias="estimatedCompletionTime"
    )
    completed_at: Optional[str] = Field(default=None, description="Completion time (ISO 8601)", alias="completedAt")
    processing_time_seconds: Optional[float] = Field(
        default=None, description="Processing time in seconds", alias="processingTimeSeconds"
    )
    failed_documents: List[ReindexFailedDocument] = Field(
        default_factory=list, description="Failed documents", alias="failedDocuments"
    )

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "reindexJobId": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
                "totalDocuments": 150,
                "processedCount": 75,
                "failedCount": 2,
                "status": "in_progress",
                "estimatedCompletionTime": "2025-10-16T14:45:00Z",
                "failedDocuments": [
                    {
                        "documentId": "660f9511-f3ac-52e5-b827-557766551111",
                        "error": "Failed to apply new metadata field: Invalid default value",
                    }
                ],
            }
        }
