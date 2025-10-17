"""Entity type configuration loading and prompt engineering."""

from __future__ import annotations

import json
from pathlib import Path
from typing import List

import yaml

from ..models.entity_types import EntityType


# Cache for loaded entity types (reloads on service restart only)
_entity_types_cache: List[EntityType] | None = None


def load_entity_types(path: str) -> List[EntityType]:
    """
    Load entity types from YAML configuration file.

    Args:
        path: Absolute or relative path to entity-types.yaml

    Returns:
        List of EntityType objects

    Raises:
        FileNotFoundError: If config file does not exist
        ValueError: If YAML structure is invalid
    """
    global _entity_types_cache

    # Return cached entity types if already loaded
    if _entity_types_cache is not None:
        return _entity_types_cache

    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"Entity types config not found: {path}")

    with open(config_path, "r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f)

    if not config_data or "entity_types" not in config_data:
        raise ValueError("Invalid entity-types.yaml: missing 'entity_types' key")

    entity_types = [EntityType(**et) for et in config_data["entity_types"]]

    # Cache for future calls
    _entity_types_cache = entity_types

    return entity_types


def build_extraction_prompt(entity_types: List[EntityType], document_text: str) -> str:
    """
    Build LLM prompt for entity extraction with entity type descriptions and examples.

    Args:
        entity_types: List of configured entity types
        document_text: Text content to extract entities from

    Returns:
        Formatted prompt string for LLM
    """
    # Build entity type descriptions with examples
    types_description = "\n".join(
        [
            f"- **{et.type_name}**: {et.description}\n  Examples: {', '.join(et.examples[:3])}"
            for et in entity_types
        ]
    )

    # Construct JSON schema for expected response
    json_schema = {
        "entity_name": "string",
        "entity_type": "string (one of the types listed above)",
        "confidence": "float (0.0-1.0)",
        "text_span": "string (e.g., 'char 245-260')",
    }

    prompt = f"""You are an expert entity extraction system. Extract entities from the following document and return them as a JSON array.

**Entity Types to Extract:**
{types_description}

**Output Format:**
Return a valid JSON array with this structure:
{json.dumps([json_schema], indent=2)}

**Instructions:**
1. Extract ALL relevant entities that match the entity types listed above
2. Assign a confidence score (0.0-1.0) based on extraction certainty
3. Record the text_span where the entity appears (character range or page/paragraph)
4. Only extract entities that clearly match one of the defined types
5. Return ONLY the JSON array, no additional text or explanation

**Document Text:**
{document_text}

**Extracted Entities (JSON Array):**
"""

    return prompt


def clear_entity_types_cache() -> None:
    """Clear the entity types cache. Used for testing."""
    global _entity_types_cache
    _entity_types_cache = None
