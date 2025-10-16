"""Unit tests for entity types models and configuration loading.

This module tests EntityTypeDefinition, EntityTypesConfig, and entity_loader functions.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

from shared.config.entity_loader import (
    add_entity_type_to_file,
    load_cached_entity_types,
    load_entity_types,
    save_entity_types,
)
from shared.models.entity_types import EntityTypeDefinition, EntityTypesConfig


class TestEntityTypeDefinition:
    """Tests for EntityTypeDefinition Pydantic model."""

    def test_valid_entity_type_definition(self):
        """Test creating a valid entity type definition."""
        entity_type = EntityTypeDefinition(
            type_name="person",
            description="Individual people",
            examples=["John Doe", "Jane Smith"],
        )

        assert entity_type.type_name == "person"
        assert entity_type.description == "Individual people"
        assert len(entity_type.examples) == 2
        assert "John Doe" in entity_type.examples

    def test_entity_type_validation_lowercase(self):
        """Test type_name must be lowercase."""
        with pytest.raises(ValidationError, match="lowercase"):
            EntityTypeDefinition(
                type_name="Person",  # Invalid: uppercase
                description="Test",
                examples=[],
            )

    def test_entity_type_validation_no_spaces(self):
        """Test type_name cannot contain spaces."""
        with pytest.raises(ValidationError, match="spaces"):
            EntityTypeDefinition(
                type_name="legal case",  # Invalid: contains space
                description="Test",
                examples=[],
            )

    def test_entity_type_with_empty_examples(self):
        """Test entity type with empty examples list is valid."""
        entity_type = EntityTypeDefinition(
            type_name="concept",
            description="Abstract concepts",
            examples=[],
        )

        assert entity_type.type_name == "concept"
        assert entity_type.examples == []

    def test_entity_type_without_examples_field(self):
        """Test entity type without examples field defaults to empty list."""
        entity_type = EntityTypeDefinition(
            type_name="organization",
            description="Companies and institutions",
        )

        assert entity_type.examples == []


class TestEntityTypesConfig:
    """Tests for EntityTypesConfig Pydantic model."""

    def test_valid_entity_types_config(self):
        """Test creating a valid entity types configuration."""
        config = EntityTypesConfig(
            entity_types=[
                EntityTypeDefinition(
                    type_name="person",
                    description="People",
                    examples=["John Doe"],
                ),
                EntityTypeDefinition(
                    type_name="organization",
                    description="Organizations",
                    examples=["Acme Inc."],
                ),
            ]
        )

        assert len(config.entity_types) == 2
        assert config.entity_types[0].type_name == "person"
        assert config.entity_types[1].type_name == "organization"

    def test_get_type_names(self):
        """Test get_type_names returns list of type names."""
        config = EntityTypesConfig(
            entity_types=[
                EntityTypeDefinition(
                    type_name="person",
                    description="People",
                    examples=[],
                ),
                EntityTypeDefinition(
                    type_name="concept",
                    description="Concepts",
                    examples=[],
                ),
            ]
        )

        type_names = config.get_type_names()
        assert type_names == ["person", "concept"]

    def test_add_entity_type_unique(self):
        """Test adding unique entity type succeeds."""
        config = EntityTypesConfig(
            entity_types=[
                EntityTypeDefinition(
                    type_name="person",
                    description="People",
                    examples=[],
                )
            ]
        )

        new_type = EntityTypeDefinition(
            type_name="organization",
            description="Organizations",
            examples=[],
        )

        config.add_entity_type(new_type)
        assert len(config.entity_types) == 2
        assert config.entity_types[1].type_name == "organization"

    def test_add_entity_type_duplicate(self):
        """Test adding duplicate entity type raises error."""
        config = EntityTypesConfig(
            entity_types=[
                EntityTypeDefinition(
                    type_name="person",
                    description="People",
                    examples=[],
                )
            ]
        )

        duplicate = EntityTypeDefinition(
            type_name="person",  # Duplicate
            description="Different description",
            examples=[],
        )

        with pytest.raises(ValueError, match="already exists"):
            config.add_entity_type(duplicate)

    def test_get_entity_type(self):
        """Test get_entity_type returns correct entity type."""
        config = EntityTypesConfig(
            entity_types=[
                EntityTypeDefinition(
                    type_name="person",
                    description="People",
                    examples=[],
                ),
                EntityTypeDefinition(
                    type_name="organization",
                    description="Organizations",
                    examples=[],
                ),
            ]
        )

        entity_type = config.get_entity_type("organization")
        assert entity_type is not None
        assert entity_type.type_name == "organization"
        assert entity_type.description == "Organizations"

    def test_get_entity_type_not_found(self):
        """Test get_entity_type returns None for non-existent type."""
        config = EntityTypesConfig(
            entity_types=[
                EntityTypeDefinition(
                    type_name="person",
                    description="People",
                    examples=[],
                )
            ]
        )

        entity_type = config.get_entity_type("nonexistent")
        assert entity_type is None

    def test_empty_entity_types_list_invalid(self):
        """Test creating config with empty entity_types list is invalid."""
        with pytest.raises(ValidationError, match="at least 1 item"):
            EntityTypesConfig(entity_types=[])


class TestEntityLoader:
    """Tests for entity_loader module functions."""

    def test_load_entity_types_from_yaml(self, tmp_path: Path):
        """Test loading entity types from YAML file."""
        yaml_content = """
entity_types:
  - type_name: person
    description: "People"
    examples: ["John Doe"]
  - type_name: organization
    description: "Organizations"
    examples: ["Acme Inc."]
"""
        config_file = tmp_path / "entity-types.yaml"
        config_file.write_text(yaml_content)

        config = load_entity_types(str(config_file))

        assert len(config.entity_types) == 2
        assert config.entity_types[0].type_name == "person"
        assert config.entity_types[1].type_name == "organization"

    def test_load_entity_types_file_not_found(self):
        """Test loading entity types from non-existent file raises error."""
        with pytest.raises(FileNotFoundError, match="not found"):
            load_entity_types("/nonexistent/path/entity-types.yaml")

    def test_load_entity_types_invalid_yaml(self, tmp_path: Path):
        """Test loading entity types from invalid YAML raises error."""
        config_file = tmp_path / "invalid.yaml"
        config_file.write_text("invalid: yaml: content:")

        with pytest.raises(ValueError, match="Invalid YAML"):
            load_entity_types(str(config_file))

    def test_load_entity_types_empty_file(self, tmp_path: Path):
        """Test loading entity types from empty file raises error."""
        config_file = tmp_path / "empty.yaml"
        config_file.write_text("")

        with pytest.raises(ValueError, match="empty"):
            load_entity_types(str(config_file))

    def test_load_entity_types_invalid_structure(self, tmp_path: Path):
        """Test loading entity types with invalid structure raises error."""
        yaml_content = """
entity_types:
  - type_name: "Person"  # Invalid: uppercase
    description: "Test"
    examples: []
"""
        config_file = tmp_path / "invalid-structure.yaml"
        config_file.write_text(yaml_content)

        with pytest.raises(ValueError, match="Invalid configuration structure"):
            load_entity_types(str(config_file))

    def test_save_entity_types_to_yaml(self, tmp_path: Path):
        """Test saving entity types to YAML file."""
        config = EntityTypesConfig(
            entity_types=[
                EntityTypeDefinition(
                    type_name="person",
                    description="People",
                    examples=["John Doe"],
                )
            ]
        )

        config_file = tmp_path / "entity-types.yaml"
        save_entity_types(config, str(config_file))

        # Verify file was created and is valid
        assert config_file.exists()
        loaded_config = load_entity_types(str(config_file))
        assert len(loaded_config.entity_types) == 1
        assert loaded_config.entity_types[0].type_name == "person"

    def test_save_entity_types_creates_parent_directory(self, tmp_path: Path):
        """Test save_entity_types creates parent directory if needed."""
        config = EntityTypesConfig(
            entity_types=[
                EntityTypeDefinition(
                    type_name="person",
                    description="People",
                    examples=[],
                )
            ]
        )

        config_file = tmp_path / "nested" / "dir" / "entity-types.yaml"
        save_entity_types(config, str(config_file))

        # Verify directory and file were created
        assert config_file.parent.exists()
        assert config_file.exists()

    def test_add_entity_type_to_file(self, tmp_path: Path):
        """Test add_entity_type_to_file adds entity type and saves."""
        # Create initial config file
        initial_config = EntityTypesConfig(
            entity_types=[
                EntityTypeDefinition(
                    type_name="person",
                    description="People",
                    examples=[],
                )
            ]
        )

        config_file = tmp_path / "entity-types.yaml"
        save_entity_types(initial_config, str(config_file))

        # Add new entity type
        new_entity = EntityTypeDefinition(
            type_name="organization",
            description="Organizations",
            examples=["Acme Inc."],
        )

        updated_config = add_entity_type_to_file(new_entity, str(config_file))

        # Verify entity was added
        assert len(updated_config.entity_types) == 2
        assert updated_config.entity_types[1].type_name == "organization"

        # Verify file was updated
        loaded_config = load_entity_types(str(config_file))
        assert len(loaded_config.entity_types) == 2

    def test_add_entity_type_to_file_duplicate_raises_error(self, tmp_path: Path):
        """Test add_entity_type_to_file raises error for duplicate."""
        # Create initial config file
        initial_config = EntityTypesConfig(
            entity_types=[
                EntityTypeDefinition(
                    type_name="person",
                    description="People",
                    examples=[],
                )
            ]
        )

        config_file = tmp_path / "entity-types.yaml"
        save_entity_types(initial_config, str(config_file))

        # Try to add duplicate
        duplicate_entity = EntityTypeDefinition(
            type_name="person",
            description="Different description",
            examples=[],
        )

        with pytest.raises(ValueError, match="already exists"):
            add_entity_type_to_file(duplicate_entity, str(config_file))

    def test_load_cached_entity_types(self, tmp_path: Path):
        """Test load_cached_entity_types caches configuration."""
        yaml_content = """
entity_types:
  - type_name: person
    description: "People"
    examples: []
"""
        config_file = tmp_path / "entity-types.yaml"
        config_file.write_text(yaml_content)

        # Clear cache first
        load_cached_entity_types.cache_clear()

        # First load
        config1 = load_cached_entity_types(str(config_file))

        # Second load should return cached version
        config2 = load_cached_entity_types(str(config_file))

        # They should be the same object (cached)
        assert config1 is config2

    def test_cache_invalidation_after_add(self, tmp_path: Path):
        """Test cache is invalidated after add_entity_type_to_file."""
        # Create initial config
        initial_config = EntityTypesConfig(
            entity_types=[
                EntityTypeDefinition(
                    type_name="person",
                    description="People",
                    examples=[],
                )
            ]
        )

        config_file = tmp_path / "entity-types.yaml"
        save_entity_types(initial_config, str(config_file))

        # Clear cache and load
        load_cached_entity_types.cache_clear()
        config1 = load_cached_entity_types(str(config_file))
        assert len(config1.entity_types) == 1

        # Add entity type (should invalidate cache)
        new_entity = EntityTypeDefinition(
            type_name="organization",
            description="Organizations",
            examples=[],
        )
        add_entity_type_to_file(new_entity, str(config_file))

        # Load again - should get fresh data with 2 entity types
        config2 = load_cached_entity_types(str(config_file))
        assert len(config2.entity_types) == 2
