"""Shared pytest fixtures for metadata tests.

This module provides reusable fixtures for testing metadata validation functionality.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from shared.models.metadata import (
    MetadataFieldDefinition,
    MetadataFieldType,
    MetadataSchema,
)


@pytest.fixture
def sample_string_field() -> MetadataFieldDefinition:
    """Create a sample string field definition."""
    return MetadataFieldDefinition(
        field_name="author",
        type=MetadataFieldType.STRING,
        required=True,
        description="Document author name",
    )


@pytest.fixture
def sample_integer_field() -> MetadataFieldDefinition:
    """Create a sample integer field definition."""
    return MetadataFieldDefinition(
        field_name="version",
        type=MetadataFieldType.INTEGER,
        required=False,
        default=1,
        description="Document version number",
    )


@pytest.fixture
def sample_date_field() -> MetadataFieldDefinition:
    """Create a sample date field definition."""
    return MetadataFieldDefinition(
        field_name="date_created",
        type=MetadataFieldType.DATE,
        required=False,
        description="Document creation date",
    )


@pytest.fixture
def sample_boolean_field() -> MetadataFieldDefinition:
    """Create a sample boolean field definition."""
    return MetadataFieldDefinition(
        field_name="is_public",
        type=MetadataFieldType.BOOLEAN,
        required=False,
        default=False,
        description="Whether document is publicly accessible",
    )


@pytest.fixture
def sample_tags_field() -> MetadataFieldDefinition:
    """Create a sample tags field definition."""
    return MetadataFieldDefinition(
        field_name="tags",
        type=MetadataFieldType.TAGS,
        required=False,
        default=[],
        description="Document tags",
    )


@pytest.fixture
def simple_schema(sample_string_field: MetadataFieldDefinition) -> MetadataSchema:
    """Create a simple schema with one required string field."""
    return MetadataSchema(metadata_fields=[sample_string_field])


@pytest.fixture
def comprehensive_schema(
    sample_string_field: MetadataFieldDefinition,
    sample_integer_field: MetadataFieldDefinition,
    sample_date_field: MetadataFieldDefinition,
    sample_boolean_field: MetadataFieldDefinition,
    sample_tags_field: MetadataFieldDefinition,
) -> MetadataSchema:
    """Create a comprehensive schema with all field types."""
    return MetadataSchema(
        metadata_fields=[
            sample_string_field,
            sample_integer_field,
            sample_date_field,
            sample_boolean_field,
            sample_tags_field,
        ]
    )


@pytest.fixture
def valid_metadata_dict() -> dict:
    """Create a valid metadata dictionary for testing."""
    return {
        "author": "Jane Smith",
        "version": 2,
        "date_created": "2024-10-16",
        "is_public": True,
        "tags": ["important", "reviewed"],
    }


@pytest.fixture
def invalid_metadata_missing_required() -> dict:
    """Create metadata dictionary missing required field."""
    return {
        "version": 1,
        "tags": [],
    }


@pytest.fixture
def invalid_metadata_wrong_types() -> dict:
    """Create metadata dictionary with wrong field types."""
    return {
        "author": "John Doe",
        "version": "1.0",  # Should be integer
        "is_public": "true",  # Should be boolean
        "tags": "tag1,tag2",  # Should be list
    }


@pytest.fixture
def fixtures_dir() -> Path:
    """Get the path to the fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def valid_schema_path(fixtures_dir: Path) -> Path:
    """Get the path to the valid schema fixture."""
    return fixtures_dir / "valid-schema.yaml"


@pytest.fixture
def invalid_schema_path(fixtures_dir: Path) -> Path:
    """Get the path to the invalid schema fixture."""
    return fixtures_dir / "invalid-schema.yaml"


@pytest.fixture
def sample_date_object() -> date:
    """Create a sample date object for testing."""
    return date(2024, 10, 16)


@pytest.fixture
def sample_iso_date_string() -> str:
    """Create a sample ISO 8601 date string for testing."""
    return "2024-10-16"


@pytest.fixture
def invalid_date_string() -> str:
    """Create an invalid date string for testing."""
    return "10/16/2024"  # US format, not ISO 8601
