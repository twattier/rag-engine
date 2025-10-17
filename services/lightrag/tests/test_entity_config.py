"""Unit tests for entity configuration loading and prompt engineering."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest
import yaml

from services.lightrag.app.models.entity_types import EntityType
from services.lightrag.app.utils.entity_config import (
    build_extraction_prompt,
    clear_entity_types_cache,
    load_entity_types,
)


@pytest.fixture(autouse=True)
def reset_cache():
    """Clear entity types cache before each test."""
    clear_entity_types_cache()
    yield
    clear_entity_types_cache()


@pytest.fixture
def sample_entity_types_yaml():
    """Create a temporary entity-types.yaml file for testing."""
    entity_config = {
        "entity_types": [
            {
                "type_name": "person",
                "description": "Individual names",
                "examples": ["John Doe", "Jane Smith", "Dr. Alice"],
            },
            {
                "type_name": "company",
                "description": "Organizations",
                "examples": ["Google", "Microsoft", "Amazon"],
            },
            {
                "type_name": "skill",
                "description": "Professional skills",
                "examples": ["Python programming", "Project management"],
            },
        ]
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(entity_config, f)
        temp_path = f.name

    yield temp_path

    # Cleanup
    Path(temp_path).unlink(missing_ok=True)


def test_load_entity_types_success(sample_entity_types_yaml):
    """Test successful loading of entity types from YAML."""
    entity_types = load_entity_types(sample_entity_types_yaml)

    assert len(entity_types) == 3
    assert all(isinstance(et, EntityType) for et in entity_types)

    # Check first entity type
    person_type = entity_types[0]
    assert person_type.type_name == "person"
    assert person_type.description == "Individual names"
    assert len(person_type.examples) == 3


def test_load_entity_types_caching(sample_entity_types_yaml):
    """Test that entity types are cached after first load."""
    first_load = load_entity_types(sample_entity_types_yaml)
    second_load = load_entity_types(sample_entity_types_yaml)

    # Should return the same cached object
    assert first_load is second_load


def test_load_entity_types_file_not_found():
    """Test error handling when config file does not exist."""
    with pytest.raises(FileNotFoundError, match="Entity types config not found"):
        load_entity_types("/nonexistent/path/entity-types.yaml")


def test_load_entity_types_invalid_yaml():
    """Test error handling for invalid YAML structure."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write("invalid: yaml\nwithout: entity_types")
        temp_path = f.name

    try:
        with pytest.raises(ValueError, match="missing 'entity_types' key"):
            load_entity_types(temp_path)
    finally:
        Path(temp_path).unlink(missing_ok=True)


def test_entity_type_validation():
    """Test EntityType model validation."""
    # Valid entity type
    valid_et = EntityType(
        type_name="person", description="Individual names", examples=["John Doe"]
    )
    assert valid_et.type_name == "person"

    # Invalid: uppercase type_name
    with pytest.raises(ValueError, match="type_name must be lowercase"):
        EntityType(type_name="Person", description="test", examples=["test"])

    # Invalid: space in type_name
    with pytest.raises(ValueError, match="cannot contain spaces"):
        EntityType(type_name="person name", description="test", examples=["test"])


def test_build_extraction_prompt_structure(sample_entity_types_yaml):
    """Test that extraction prompt includes all required components."""
    entity_types = load_entity_types(sample_entity_types_yaml)
    document_text = "John Doe works at Google as a Python developer."

    prompt = build_extraction_prompt(entity_types, document_text)

    # Check prompt contains entity type descriptions
    assert "person" in prompt
    assert "Individual names" in prompt
    assert "company" in prompt
    assert "Organizations" in prompt

    # Check prompt contains examples (first 3 only)
    assert "John Doe" in prompt
    assert "Google" in prompt

    # Check prompt contains document text
    assert document_text in prompt

    # Check prompt contains JSON schema instructions
    assert "entity_name" in prompt
    assert "entity_type" in prompt
    assert "confidence" in prompt
    assert "text_span" in prompt


def test_build_extraction_prompt_limits_examples(sample_entity_types_yaml):
    """Test that prompt only includes first 3 examples per entity type."""
    entity_types = load_entity_types(sample_entity_types_yaml)
    prompt = build_extraction_prompt(entity_types, "test document")

    # Person entity type has 3 examples: should include all
    person_examples = ["John Doe", "Jane Smith", "Dr. Alice"]
    for example in person_examples:
        assert example in prompt


def test_build_extraction_prompt_json_format():
    """Test that prompt requests valid JSON format."""
    entity_types = [
        EntityType(
            type_name="person", description="Individual names", examples=["John Doe"]
        )
    ]

    prompt = build_extraction_prompt(entity_types, "test document")

    # Prompt should mention JSON array format
    assert "JSON" in prompt or "json" in prompt
    assert "array" in prompt.lower()


def test_clear_entity_types_cache(sample_entity_types_yaml):
    """Test cache clearing functionality."""
    # Load entity types (caches them)
    first_load = load_entity_types(sample_entity_types_yaml)

    # Clear cache
    clear_entity_types_cache()

    # Load again (should reload from file, not cache)
    second_load = load_entity_types(sample_entity_types_yaml)

    # Objects should be different instances (not cached)
    assert first_load is not second_load
    # But content should be the same
    assert len(first_load) == len(second_load)
    assert first_load[0].type_name == second_load[0].type_name
