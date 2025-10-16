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
