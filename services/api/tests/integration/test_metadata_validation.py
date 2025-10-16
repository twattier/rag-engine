"""Integration tests for metadata validation in API endpoints."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from fastapi import HTTPException

from app.dependencies import get_metadata_schema, validate_document_metadata
from shared.models.metadata import MetadataFieldDefinition, MetadataFieldType, MetadataSchema


class TestGetMetadataSchema:
    """Tests for get_metadata_schema dependency."""

    def test_get_metadata_schema_loads_successfully(self, monkeypatch):
        """Test that metadata schema is loaded successfully."""
        # Create temporary schema file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("""
metadata_fields:
  - field_name: author
    type: string
    required: true
    description: "Author"
""")
            temp_path = f.name

        try:
            # Mock settings to use temp file
            from app import config
            monkeypatch.setattr(config.settings, "METADATA_SCHEMA_PATH", temp_path)

            # Clear cache to force reload
            get_metadata_schema.cache_clear()

            schema = get_metadata_schema()
            assert isinstance(schema, MetadataSchema)
            assert len(schema.metadata_fields) == 1
            assert schema.metadata_fields[0].field_name == "author"
        finally:
            Path(temp_path).unlink()

    def test_get_metadata_schema_file_not_found(self, monkeypatch):
        """Test error handling when schema file doesn't exist."""
        from app import config
        monkeypatch.setattr(config.settings, "METADATA_SCHEMA_PATH", "/nonexistent/schema.yaml")

        # Clear cache to force reload
        get_metadata_schema.cache_clear()

        with pytest.raises(HTTPException) as exc_info:
            get_metadata_schema()

        assert exc_info.value.status_code == 500
        assert "SCHEMA_NOT_FOUND" in str(exc_info.value.detail)

    def test_get_metadata_schema_invalid_yaml(self, monkeypatch):
        """Test error handling for invalid YAML schema."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: syntax:")
            temp_path = f.name

        try:
            from app import config
            monkeypatch.setattr(config.settings, "METADATA_SCHEMA_PATH", temp_path)

            # Clear cache to force reload
            get_metadata_schema.cache_clear()

            with pytest.raises(HTTPException) as exc_info:
                get_metadata_schema()

            assert exc_info.value.status_code == 500
            assert "INVALID_SCHEMA" in str(exc_info.value.detail)
        finally:
            Path(temp_path).unlink()


@pytest.mark.asyncio
class TestValidateDocumentMetadata:
    """Tests for validate_document_metadata dependency."""

    async def test_validate_metadata_success(self):
        """Test successful metadata validation."""
        schema = MetadataSchema(
            metadata_fields=[
                MetadataFieldDefinition(
                    field_name="author",
                    type=MetadataFieldType.STRING,
                    required=True,
                    description="Author",
                )
            ]
        )
        metadata = {"author": "John Doe"}

        validated = await validate_document_metadata(metadata, schema)
        assert validated["author"] == "John Doe"

    async def test_validate_metadata_missing_required_field(self):
        """Test validation fails for missing required field."""
        schema = MetadataSchema(
            metadata_fields=[
                MetadataFieldDefinition(
                    field_name="author",
                    type=MetadataFieldType.STRING,
                    required=True,
                    description="Author",
                )
            ]
        )
        metadata = {}

        with pytest.raises(HTTPException) as exc_info:
            await validate_document_metadata(metadata, schema)

        assert exc_info.value.status_code == 422
        detail = exc_info.value.detail
        assert detail["error"]["code"] == "INVALID_METADATA"
        assert "validation_errors" in detail["error"]

    async def test_validate_metadata_wrong_type(self):
        """Test validation fails for wrong field type."""
        schema = MetadataSchema(
            metadata_fields=[
                MetadataFieldDefinition(
                    field_name="version",
                    type=MetadataFieldType.INTEGER,
                    required=False,
                    description="Version",
                )
            ]
        )
        metadata = {"version": "not_an_integer"}

        with pytest.raises(HTTPException) as exc_info:
            await validate_document_metadata(metadata, schema)

        assert exc_info.value.status_code == 422
        detail = exc_info.value.detail
        assert detail["error"]["code"] == "INVALID_METADATA"
        assert "version" in str(detail["error"]["validation_errors"])

    async def test_validate_metadata_applies_defaults(self):
        """Test that default values are applied."""
        schema = MetadataSchema(
            metadata_fields=[
                MetadataFieldDefinition(
                    field_name="version",
                    type=MetadataFieldType.INTEGER,
                    required=False,
                    default=1,
                    description="Version",
                ),
                MetadataFieldDefinition(
                    field_name="tags",
                    type=MetadataFieldType.TAGS,
                    required=False,
                    default=[],
                    description="Tags",
                ),
            ]
        )
        metadata = {}

        validated = await validate_document_metadata(metadata, schema)
        assert validated["version"] == 1
        assert validated["tags"] == []

    async def test_validate_metadata_allows_extra_fields(self):
        """Test that extra fields are allowed."""
        schema = MetadataSchema(
            metadata_fields=[
                MetadataFieldDefinition(
                    field_name="author",
                    type=MetadataFieldType.STRING,
                    required=False,
                    description="Author",
                )
            ]
        )
        metadata = {"author": "John Doe", "custom_field": "custom_value"}

        validated = await validate_document_metadata(metadata, schema)
        assert validated["author"] == "John Doe"
        assert validated["custom_field"] == "custom_value"

    async def test_validate_metadata_complex_scenario(self):
        """Test validation with multiple field types."""
        schema = MetadataSchema(
            metadata_fields=[
                MetadataFieldDefinition(
                    field_name="author",
                    type=MetadataFieldType.STRING,
                    required=True,
                    description="Author",
                ),
                MetadataFieldDefinition(
                    field_name="version",
                    type=MetadataFieldType.INTEGER,
                    required=False,
                    default=1,
                    description="Version",
                ),
                MetadataFieldDefinition(
                    field_name="tags",
                    type=MetadataFieldType.TAGS,
                    required=False,
                    default=[],
                    description="Tags",
                ),
                MetadataFieldDefinition(
                    field_name="date_created",
                    type=MetadataFieldType.DATE,
                    required=False,
                    description="Date",
                ),
                MetadataFieldDefinition(
                    field_name="is_public",
                    type=MetadataFieldType.BOOLEAN,
                    required=False,
                    default=False,
                    description="Public",
                ),
            ]
        )
        metadata = {
            "author": "Jane Smith",
            "version": 2,
            "tags": ["important", "reviewed"],
            "date_created": "2024-10-16",
            "is_public": True,
        }

        validated = await validate_document_metadata(metadata, schema)
        assert validated["author"] == "Jane Smith"
        assert validated["version"] == 2
        assert validated["tags"] == ["important", "reviewed"]
        assert validated["is_public"] is True

    async def test_validate_metadata_uses_default_schema(self, monkeypatch):
        """Test that default schema is loaded when not provided."""
        # Create temporary schema file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("""
metadata_fields:
  - field_name: author
    type: string
    required: true
    description: "Author"
""")
            temp_path = f.name

        try:
            from app import config
            monkeypatch.setattr(config.settings, "METADATA_SCHEMA_PATH", temp_path)

            # Clear cache to force reload
            get_metadata_schema.cache_clear()

            metadata = {"author": "Test Author"}
            validated = await validate_document_metadata(metadata, schema=None)
            assert validated["author"] == "Test Author"
        finally:
            Path(temp_path).unlink()
