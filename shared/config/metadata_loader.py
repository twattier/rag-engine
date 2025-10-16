"""Metadata schema loader and validator.

This module provides functions to load metadata schemas from YAML files
and validate metadata dictionaries against those schemas.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Dict

import yaml
from pydantic import ValidationError

from shared.models.metadata import MetadataSchema


def load_metadata_schema(file_path: str) -> MetadataSchema:
    """Load metadata schema from YAML file.

    Args:
        file_path: Path to the YAML schema file

    Returns:
        Loaded and validated MetadataSchema object

    Raises:
        FileNotFoundError: If schema file doesn't exist
        ValueError: If YAML is invalid or schema validation fails
    """
    schema_path = Path(file_path)

    if not schema_path.exists():
        raise FileNotFoundError(f"Metadata schema file not found: {file_path}")

    try:
        with schema_path.open("r") as f:
            schema_data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in schema file: {e}")

    if not schema_data:
        raise ValueError("Schema file is empty")

    if not isinstance(schema_data, dict):
        raise ValueError("Schema file must contain a dictionary")

    try:
        schema = MetadataSchema(**schema_data)
    except ValidationError as e:
        raise ValueError(f"Invalid schema structure: {e}")

    return schema


@lru_cache(maxsize=1)
def load_cached_metadata_schema(file_path: str) -> MetadataSchema:
    """Load metadata schema from YAML file with caching.

    This function caches the loaded schema to avoid repeated file reads.
    Use this in production code for better performance.

    Args:
        file_path: Path to the YAML schema file

    Returns:
        Loaded and validated MetadataSchema object

    Raises:
        FileNotFoundError: If schema file doesn't exist
        ValueError: If YAML is invalid or schema validation fails
    """
    return load_metadata_schema(file_path)


def validate_metadata(
    metadata: Dict[str, Any], schema: MetadataSchema
) -> Dict[str, Any]:
    """Validate metadata dictionary against schema.

    Args:
        metadata: Dictionary of metadata fields to validate
        schema: MetadataSchema to validate against

    Returns:
        Validated metadata dictionary with defaults applied

    Raises:
        ValueError: If validation fails (missing required fields or wrong types)
    """
    return schema.validate_metadata(metadata)
