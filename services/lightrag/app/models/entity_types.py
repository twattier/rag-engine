"""Pydantic models for entity types and extracted entities."""

from __future__ import annotations

from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class EntityType(BaseModel):
    """Entity type configuration from entity-types.yaml."""

    type_name: str = Field(..., description="Lowercase entity type identifier")
    description: str = Field(..., description="Human-readable description of entity type")
    examples: List[str] = Field(..., description="Example entities of this type")

    model_config = ConfigDict(frozen=True)  # Immutable after creation

    @field_validator("type_name")
    @classmethod
    def validate_type_name(cls, v: str) -> str:
        """Ensure type_name is lowercase and has no spaces."""
        if not v.islower():
            raise ValueError("type_name must be lowercase")
        if " " in v:
            raise ValueError("type_name cannot contain spaces")
        return v


class ExtractedEntity(BaseModel):
    """Entity extracted from a document by LLM."""

    entity_name: str = Field(..., description="Name of the extracted entity")
    entity_type: str = Field(..., description="Type of entity (person, company, skill, etc.)")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Extraction confidence (0.0-1.0)")
    source_document_id: UUID = Field(..., description="Document ID where entity was found")
    text_span: Optional[str] = Field(
        None, description="Location in document (e.g., 'char 245-260' or 'page 2, para 3')"
    )

    @field_validator("confidence_score")
    @classmethod
    def validate_confidence(cls, v: float) -> float:
        """Ensure confidence score is between 0.0 and 1.0."""
        if not 0.0 <= v <= 1.0:
            raise ValueError("confidence_score must be between 0.0 and 1.0")
        return v
