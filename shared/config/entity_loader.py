"""Entity types configuration loader and persister.

This module provides functions to load entity types from YAML files,
persist configurations to YAML, and manage entity type configurations.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import ValidationError

from shared.models.entity_types import EntityTypesConfig, EntityTypeDefinition


def load_entity_types(file_path: str) -> EntityTypesConfig:
    """Load entity types from YAML configuration file.

    Args:
        file_path: Path to the YAML entity types file

    Returns:
        Loaded and validated EntityTypesConfig object

    Raises:
        FileNotFoundError: If configuration file doesn't exist
        ValueError: If YAML is invalid or configuration validation fails
    """
    config_path = Path(file_path)

    if not config_path.exists():
        raise FileNotFoundError(f"Entity types configuration file not found: {file_path}")

    try:
        with config_path.open("r") as f:
            config_data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in configuration file: {e}")

    if not config_data:
        raise ValueError("Configuration file is empty")

    if not isinstance(config_data, dict):
        raise ValueError("Configuration file must contain a dictionary")

    try:
        config = EntityTypesConfig(**config_data)
    except ValidationError as e:
        raise ValueError(f"Invalid configuration structure: {e}")

    return config


@lru_cache(maxsize=1)
def load_cached_entity_types(file_path: str) -> EntityTypesConfig:
    """Load entity types from YAML file with caching.

    This function caches the loaded configuration to avoid repeated file reads.
    Use this in production code for better performance.

    To invalidate the cache (e.g., after adding new entity types via API):
        load_cached_entity_types.cache_clear()

    Args:
        file_path: Path to the YAML entity types file

    Returns:
        Loaded and validated EntityTypesConfig object

    Raises:
        FileNotFoundError: If configuration file doesn't exist
        ValueError: If YAML is invalid or configuration validation fails
    """
    return load_entity_types(file_path)


def save_entity_types(config: EntityTypesConfig, file_path: str) -> None:
    """Save entity types configuration to YAML file.

    Args:
        config: EntityTypesConfig object to persist
        file_path: Path to the YAML file to write

    Raises:
        PermissionError: If file cannot be written due to permissions
        OSError: If file write fails for other reasons
    """
    config_path = Path(file_path)

    # Ensure parent directory exists
    config_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Convert Pydantic model to dict
        data = config.model_dump()

        # Write to YAML file
        with config_path.open("w") as f:
            yaml.dump(
                data,
                f,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
            )
    except PermissionError as e:
        raise PermissionError(f"Permission denied writing to {file_path}: {e}")
    except OSError as e:
        raise OSError(f"Failed to write entity types configuration: {e}")


def add_entity_type_to_file(
    entity_type: EntityTypeDefinition, file_path: str
) -> EntityTypesConfig:
    """Add a new entity type to the configuration file.

    This is a convenience function that loads the current configuration,
    adds the new entity type, and saves it back to the file.

    Args:
        entity_type: EntityTypeDefinition to add
        file_path: Path to the YAML configuration file

    Returns:
        Updated EntityTypesConfig with the new entity type

    Raises:
        FileNotFoundError: If configuration file doesn't exist
        ValueError: If entity type already exists or validation fails
        PermissionError: If file cannot be written
    """
    # Load current configuration
    config = load_entity_types(file_path)

    # Add new entity type (will raise ValueError if duplicate)
    config.add_entity_type(entity_type)

    # Save updated configuration
    save_entity_types(config, file_path)

    # Invalidate cache so next load gets fresh data
    load_cached_entity_types.cache_clear()

    return config
