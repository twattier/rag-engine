"""Unit tests for metadata schema definition and validation."""

from __future__ import annotations

import tempfile
from datetime import date
from pathlib import Path

import pytest

from shared.config.metadata_loader import (
    load_cached_metadata_schema,
    load_metadata_schema,
    validate_metadata,
)
from shared.models.metadata import (
    MetadataFieldDefinition,
    MetadataFieldType,
    MetadataSchema,
)


class TestMetadataFieldType:
    """Tests for MetadataFieldType enum."""

    def test_field_types_defined(self):
        """Test that all expected field types are defined."""
        assert MetadataFieldType.STRING == "string"
        assert MetadataFieldType.INTEGER == "integer"
        assert MetadataFieldType.DATE == "date"
        assert MetadataFieldType.BOOLEAN == "boolean"
        assert MetadataFieldType.TAGS == "tags"


class TestMetadataFieldDefinition:
    """Tests for MetadataFieldDefinition model."""

    def test_create_string_field(self):
        """Test creating a string field definition."""
        field = MetadataFieldDefinition(
            field_name="author",
            type=MetadataFieldType.STRING,
            required=True,
            description="Author name",
        )
        assert field.field_name == "author"
        assert field.type == MetadataFieldType.STRING
        assert field.required is True
        assert field.default is None

    def test_create_integer_field_with_default(self):
        """Test creating an integer field with default value."""
        field = MetadataFieldDefinition(
            field_name="version",
            type=MetadataFieldType.INTEGER,
            required=False,
            default=1,
            description="Version number",
        )
        assert field.field_name == "version"
        assert field.type == MetadataFieldType.INTEGER
        assert field.default == 1

    def test_create_tags_field_with_default(self):
        """Test creating a tags field with default empty list."""
        field = MetadataFieldDefinition(
            field_name="tags",
            type=MetadataFieldType.TAGS,
            required=False,
            default=[],
            description="Tags",
        )
        assert field.field_name == "tags"
        assert field.default == []

    def test_validate_default_string_type(self):
        """Test default value validation for string type."""
        with pytest.raises(ValueError, match="Default value must be string"):
            MetadataFieldDefinition(
                field_name="author",
                type=MetadataFieldType.STRING,
                required=False,
                default=123,  # Invalid: integer instead of string
                description="Author",
            )

    def test_validate_default_integer_type(self):
        """Test default value validation for integer type."""
        with pytest.raises(ValueError, match="Default value must be integer"):
            MetadataFieldDefinition(
                field_name="version",
                type=MetadataFieldType.INTEGER,
                required=False,
                default="1",  # Invalid: string instead of integer
                description="Version",
            )

    def test_validate_default_boolean_type(self):
        """Test default value validation for boolean type."""
        with pytest.raises(ValueError, match="Default value must be boolean"):
            MetadataFieldDefinition(
                field_name="is_public",
                type=MetadataFieldType.BOOLEAN,
                required=False,
                default="true",  # Invalid: string instead of boolean
                description="Public",
            )

    def test_validate_default_tags_type(self):
        """Test default value validation for tags type."""
        with pytest.raises(ValueError, match="Default value must be list"):
            MetadataFieldDefinition(
                field_name="tags",
                type=MetadataFieldType.TAGS,
                required=False,
                default="tag1,tag2",  # Invalid: string instead of list
                description="Tags",
            )

    def test_validate_default_tags_contains_strings(self):
        """Test that tags default must contain only strings."""
        with pytest.raises(ValueError, match="All items in tags default must be strings"):
            MetadataFieldDefinition(
                field_name="tags",
                type=MetadataFieldType.TAGS,
                required=False,
                default=[1, 2, 3],  # Invalid: integers instead of strings
                description="Tags",
            )


class TestMetadataSchema:
    """Tests for MetadataSchema model."""

    def test_create_schema(self):
        """Test creating a metadata schema."""
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
        assert len(schema.metadata_fields) == 1
        assert schema.metadata_fields[0].field_name == "author"

    def test_validate_metadata_success(self):
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
        validated = schema.validate_metadata(metadata)
        assert validated["author"] == "John Doe"

    def test_validate_metadata_missing_required_field(self):
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
        metadata = {"title": "Test Document"}  # Missing 'author'

        with pytest.raises(ValueError, match="Required field 'author' is missing"):
            schema.validate_metadata(metadata)

    def test_validate_metadata_wrong_type_string(self):
        """Test validation fails for wrong string type."""
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
        metadata = {"author": 123}  # Integer instead of string

        with pytest.raises(ValueError, match="Field 'author' must be string"):
            schema.validate_metadata(metadata)

    def test_validate_metadata_wrong_type_integer(self):
        """Test validation fails for wrong integer type."""
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
        metadata = {"version": "1.0"}  # String instead of integer

        with pytest.raises(ValueError, match="Field 'version' must be integer"):
            schema.validate_metadata(metadata)

    def test_validate_metadata_wrong_type_boolean(self):
        """Test validation fails for wrong boolean type."""
        schema = MetadataSchema(
            metadata_fields=[
                MetadataFieldDefinition(
                    field_name="is_public",
                    type=MetadataFieldType.BOOLEAN,
                    required=False,
                    description="Public",
                )
            ]
        )
        metadata = {"is_public": "true"}  # String instead of boolean

        with pytest.raises(ValueError, match="Field 'is_public' must be boolean"):
            schema.validate_metadata(metadata)

    def test_validate_metadata_wrong_type_tags(self):
        """Test validation fails for wrong tags type."""
        schema = MetadataSchema(
            metadata_fields=[
                MetadataFieldDefinition(
                    field_name="tags",
                    type=MetadataFieldType.TAGS,
                    required=False,
                    description="Tags",
                )
            ]
        )
        metadata = {"tags": "tag1,tag2"}  # String instead of list

        with pytest.raises(ValueError, match="Field 'tags' must be list of strings"):
            schema.validate_metadata(metadata)

    def test_validate_metadata_tags_non_string_items(self):
        """Test validation fails for tags with non-string items."""
        schema = MetadataSchema(
            metadata_fields=[
                MetadataFieldDefinition(
                    field_name="tags",
                    type=MetadataFieldType.TAGS,
                    required=False,
                    description="Tags",
                )
            ]
        )
        metadata = {"tags": [1, 2, 3]}  # Integers instead of strings

        with pytest.raises(ValueError, match="Field 'tags' must contain only strings"):
            schema.validate_metadata(metadata)

    def test_validate_metadata_date_string(self):
        """Test validation accepts ISO 8601 date string."""
        schema = MetadataSchema(
            metadata_fields=[
                MetadataFieldDefinition(
                    field_name="date_created",
                    type=MetadataFieldType.DATE,
                    required=False,
                    description="Date",
                )
            ]
        )
        metadata = {"date_created": "2024-01-15"}
        validated = schema.validate_metadata(metadata)
        assert validated["date_created"] == date(2024, 1, 15)

    def test_validate_metadata_date_object(self):
        """Test validation accepts date object."""
        schema = MetadataSchema(
            metadata_fields=[
                MetadataFieldDefinition(
                    field_name="date_created",
                    type=MetadataFieldType.DATE,
                    required=False,
                    description="Date",
                )
            ]
        )
        test_date = date(2024, 1, 15)
        metadata = {"date_created": test_date}
        validated = schema.validate_metadata(metadata)
        assert validated["date_created"] == test_date

    def test_validate_metadata_date_invalid_format(self):
        """Test validation fails for invalid date format."""
        schema = MetadataSchema(
            metadata_fields=[
                MetadataFieldDefinition(
                    field_name="date_created",
                    type=MetadataFieldType.DATE,
                    required=False,
                    description="Date",
                )
            ]
        )
        metadata = {"date_created": "01/15/2024"}  # Invalid format

        with pytest.raises(ValueError, match="must be valid ISO 8601 date string"):
            schema.validate_metadata(metadata)

    def test_validate_metadata_applies_defaults(self):
        """Test that default values are applied for missing fields."""
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
        metadata = {}  # No fields provided
        validated = schema.validate_metadata(metadata)

        assert validated["version"] == 1
        assert validated["tags"] == []

    def test_validate_metadata_allows_extra_fields(self):
        """Test that extra fields not in schema are allowed."""
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
        metadata = {"author": "John Doe", "extra_field": "extra_value"}
        validated = schema.validate_metadata(metadata)

        assert validated["author"] == "John Doe"
        assert validated["extra_field"] == "extra_value"

    def test_validate_metadata_multiple_errors(self):
        """Test that multiple validation errors are reported."""
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
                    required=True,
                    description="Version",
                ),
            ]
        )
        metadata = {}  # Missing both required fields

        with pytest.raises(ValueError) as exc_info:
            schema.validate_metadata(metadata)

        error_msg = str(exc_info.value)
        assert "author" in error_msg
        assert "version" in error_msg


class TestLoadMetadataSchema:
    """Tests for schema loading functionality."""

    def test_load_schema_success(self, tmp_path):
        """Test successful schema loading from YAML."""
        schema_file = tmp_path / "schema.yaml"
        schema_file.write_text("""
metadata_fields:
  - field_name: author
    type: string
    required: true
    description: "Document author"
""")

        schema = load_metadata_schema(str(schema_file))

        assert len(schema.metadata_fields) == 1
        assert schema.metadata_fields[0].field_name == "author"
        assert schema.metadata_fields[0].type == MetadataFieldType.STRING
        assert schema.metadata_fields[0].required is True

    def test_load_schema_file_not_found(self):
        """Test error handling for missing schema file."""
        with pytest.raises(FileNotFoundError, match="Metadata schema file not found"):
            load_metadata_schema("/nonexistent/schema.yaml")

    def test_load_schema_invalid_yaml(self, tmp_path):
        """Test error handling for invalid YAML."""
        schema_file = tmp_path / "invalid.yaml"
        schema_file.write_text("invalid: yaml: syntax:")

        with pytest.raises(ValueError, match="Invalid YAML in schema file"):
            load_metadata_schema(str(schema_file))

    def test_load_schema_empty_file(self, tmp_path):
        """Test error handling for empty schema file."""
        schema_file = tmp_path / "empty.yaml"
        schema_file.write_text("")

        with pytest.raises(ValueError, match="Schema file is empty"):
            load_metadata_schema(str(schema_file))

    def test_load_schema_invalid_structure(self, tmp_path):
        """Test error handling for invalid schema structure."""
        schema_file = tmp_path / "invalid.yaml"
        schema_file.write_text("""
metadata_fields:
  - field_name: broken
    type: invalid_type
    required: not_a_boolean
    description: "Broken"
""")

        with pytest.raises(ValueError, match="Invalid schema structure"):
            load_metadata_schema(str(schema_file))

    def test_load_cached_schema(self, tmp_path):
        """Test that cached schema loading works."""
        schema_file = tmp_path / "schema.yaml"
        schema_file.write_text("""
metadata_fields:
  - field_name: author
    type: string
    required: true
    description: "Author"
""")

        # Clear cache first
        load_cached_metadata_schema.cache_clear()

        # Load twice - second should be cached
        schema1 = load_cached_metadata_schema(str(schema_file))
        schema2 = load_cached_metadata_schema(str(schema_file))

        assert schema1 is schema2  # Same object from cache
        assert len(schema1.metadata_fields) == 1


class TestValidateMetadata:
    """Tests for validate_metadata function."""

    def test_validate_metadata_function(self):
        """Test the standalone validate_metadata function."""
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

        validated = validate_metadata(metadata, schema)
        assert validated["author"] == "John Doe"

    def test_validate_metadata_function_error(self):
        """Test error handling in standalone validate_metadata function."""
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
        metadata = {}  # Missing required field

        with pytest.raises(ValueError, match="Required field 'author' is missing"):
            validate_metadata(metadata, schema)


class TestMetadataIntegration:
    """Integration tests using fixture files."""

    def test_load_valid_schema_fixture(self):
        """Test loading the valid schema fixture."""
        fixture_path = Path(__file__).parent / "fixtures" / "valid-schema.yaml"
        schema = load_metadata_schema(str(fixture_path))

        assert len(schema.metadata_fields) == 5
        field_names = [f.field_name for f in schema.metadata_fields]
        assert "author" in field_names
        assert "version" in field_names
        assert "tags" in field_names
        assert "date_created" in field_names
        assert "is_public" in field_names

    def test_load_invalid_schema_fixture(self):
        """Test loading the invalid schema fixture fails."""
        fixture_path = Path(__file__).parent / "fixtures" / "invalid-schema.yaml"

        with pytest.raises(ValueError, match="Invalid schema structure"):
            load_metadata_schema(str(fixture_path))

    def test_validate_with_fixture_schema(self):
        """Test metadata validation using fixture schema."""
        fixture_path = Path(__file__).parent / "fixtures" / "valid-schema.yaml"
        schema = load_metadata_schema(str(fixture_path))

        # Valid metadata
        metadata = {
            "author": "Jane Smith",
            "version": 2,
            "tags": ["important", "reviewed"],
            "date_created": "2024-10-16",
            "is_public": True,
        }
        validated = schema.validate_metadata(metadata)

        assert validated["author"] == "Jane Smith"
        assert validated["version"] == 2
        assert validated["tags"] == ["important", "reviewed"]
        assert validated["date_created"] == date(2024, 10, 16)
        assert validated["is_public"] is True

    def test_validate_with_defaults_fixture_schema(self):
        """Test that defaults are applied using fixture schema."""
        fixture_path = Path(__file__).parent / "fixtures" / "valid-schema.yaml"
        schema = load_metadata_schema(str(fixture_path))

        # Only provide required field
        metadata = {"author": "Jane Smith"}
        validated = schema.validate_metadata(metadata)

        assert validated["author"] == "Jane Smith"
        assert validated["version"] == 1  # Default
        assert validated["tags"] == []  # Default
        assert validated["is_public"] is False  # Default
