"""Metadata schema definition and validation models.

This module provides Pydantic models for defining and validating custom metadata
fields for document organization and filtering.
"""

from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator, model_validator


class MetadataFieldType(str, Enum):
    """Supported metadata field types."""

    STRING = "string"
    INTEGER = "integer"
    DATE = "date"
    BOOLEAN = "boolean"
    TAGS = "tags"


class MetadataFieldDefinition(BaseModel):
    """Definition of a single metadata field.

    Attributes:
        field_name: Name of the metadata field
        type: Data type of the field (string, integer, date, boolean, tags)
        required: Whether the field is required
        default: Default value if field is not provided
        description: Human-readable description of the field
    """

    field_name: str = Field(..., description="Field name")
    type: MetadataFieldType = Field(..., description="Field data type")
    required: bool = Field(default=False, description="Whether field is required")
    default: Optional[Any] = Field(default=None, description="Default value")
    description: str = Field(..., description="Field description")

    @field_validator("default")
    @classmethod
    def validate_default_type(cls, v: Any, info) -> Any:
        """Ensure default value matches field type."""
        if v is None:
            return v

        field_type = info.data.get("type")
        if not field_type:
            return v

        # Validate default value type matches field type
        if field_type == MetadataFieldType.STRING:
            if not isinstance(v, str):
                raise ValueError(f"Default value must be string, got {type(v).__name__}")
        elif field_type == MetadataFieldType.INTEGER:
            if not isinstance(v, int):
                raise ValueError(f"Default value must be integer, got {type(v).__name__}")
        elif field_type == MetadataFieldType.DATE:
            if not isinstance(v, (str, date)):
                raise ValueError(
                    f"Default value must be string (ISO 8601) or date, got {type(v).__name__}"
                )
        elif field_type == MetadataFieldType.BOOLEAN:
            if not isinstance(v, bool):
                raise ValueError(f"Default value must be boolean, got {type(v).__name__}")
        elif field_type == MetadataFieldType.TAGS:
            if not isinstance(v, list):
                raise ValueError(f"Default value must be list, got {type(v).__name__}")
            if not all(isinstance(item, str) for item in v):
                raise ValueError("All items in tags default must be strings")

        return v


class MetadataSchema(BaseModel):
    """Complete metadata schema configuration.

    Attributes:
        metadata_fields: List of metadata field definitions
    """

    metadata_fields: List[MetadataFieldDefinition] = Field(
        ..., description="List of metadata field definitions"
    )

    def validate_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Validate metadata dictionary against schema.

        Args:
            metadata: Dictionary of metadata fields to validate

        Returns:
            Validated metadata dictionary with defaults applied

        Raises:
            ValueError: If validation fails (missing required fields or wrong types)
        """
        validated: Dict[str, Any] = {}
        errors: List[str] = []

        # Create a lookup dictionary for field definitions
        field_defs = {field.field_name: field for field in self.metadata_fields}

        # Check required fields and validate types
        for field_def in self.metadata_fields:
            field_name = field_def.field_name
            field_value = metadata.get(field_name)

            # Check if required field is missing
            if field_def.required and field_value is None:
                errors.append(f"Required field '{field_name}' is missing")
                continue

            # Apply default if field is missing
            if field_value is None:
                if field_def.default is not None:
                    validated[field_name] = field_def.default
                continue

            # Validate field type
            try:
                validated[field_name] = self._validate_field_value(
                    field_name, field_value, field_def.type
                )
            except ValueError as e:
                errors.append(str(e))

        # Allow extra fields not in schema (permissive validation)
        for field_name, field_value in metadata.items():
            if field_name not in field_defs:
                validated[field_name] = field_value

        if errors:
            raise ValueError("; ".join(errors))

        return validated

    def _validate_field_value(
        self, field_name: str, value: Any, field_type: MetadataFieldType
    ) -> Any:
        """Validate a single field value against its type.

        Args:
            field_name: Name of the field being validated
            value: Value to validate
            field_type: Expected type of the field

        Returns:
            Validated value (may be converted to correct type)

        Raises:
            ValueError: If validation fails
        """
        if field_type == MetadataFieldType.STRING:
            if not isinstance(value, str):
                raise ValueError(
                    f"Field '{field_name}' must be string, got {type(value).__name__}"
                )
            return value

        elif field_type == MetadataFieldType.INTEGER:
            # Note: bool is a subclass of int in Python (True == 1, False == 0)
            # We explicitly exclude booleans to ensure type safety
            if not isinstance(value, int) or isinstance(value, bool):
                raise ValueError(
                    f"Field '{field_name}' must be integer, got {type(value).__name__}"
                )
            return value

        elif field_type == MetadataFieldType.DATE:
            if isinstance(value, date):
                return value
            if isinstance(value, str):
                try:
                    # Validate ISO 8601 date format
                    return date.fromisoformat(value)
                except ValueError:
                    raise ValueError(
                        f"Field '{field_name}' must be valid ISO 8601 date string, got '{value}'"
                    )
            raise ValueError(
                f"Field '{field_name}' must be date or ISO 8601 string, got {type(value).__name__}"
            )

        elif field_type == MetadataFieldType.BOOLEAN:
            if not isinstance(value, bool):
                raise ValueError(
                    f"Field '{field_name}' must be boolean, got {type(value).__name__}"
                )
            return value

        elif field_type == MetadataFieldType.TAGS:
            if not isinstance(value, list):
                raise ValueError(
                    f"Field '{field_name}' must be list of strings, got {type(value).__name__}"
                )
            if not all(isinstance(item, str) for item in value):
                raise ValueError(f"Field '{field_name}' must contain only strings")
            return value

        else:
            raise ValueError(f"Unknown field type: {field_type}")
