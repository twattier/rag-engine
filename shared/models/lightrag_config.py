"""LightRAG configuration integration interface.

This module provides integration interfaces for passing entity types
to LightRAG during graph construction (Epic 3 integration point).
"""

from __future__ import annotations

from typing import List


class LightRAGConfig:
    """Configuration for LightRAG service (Epic 3).

    This is a placeholder interface for Epic 3 LightRAG integration.
    It will be implemented fully in Epic 3 when LightRAG service is integrated.

    Attributes:
        entity_types: List of entity type names to guide extraction
    """

    def __init__(self, entity_types: List[str]):
        """Initialize LightRAG configuration.

        Args:
            entity_types: List of entity type names (e.g., ["person", "organization"])
        """
        self.entity_types = entity_types

    def get_entity_extraction_prompt(self) -> str:
        """Generate prompt for entity extraction with configured types.

        This method will be used by LightRAG to generate entity extraction prompts
        that include the configured entity types.

        TODO: Epic 3 - Implement full LightRAG entity extraction prompt generation
        with detailed instructions for each entity type based on their descriptions.

        Returns:
            Prompt string for entity extraction
        """
        # TODO: Epic 3 - Implement LightRAG entity extraction prompt
        entity_list = ", ".join(self.entity_types)
        return f"Extract entities of these types: {entity_list}"

    def to_lightrag_params(self) -> dict:
        """Convert configuration to LightRAG initialization parameters.

        TODO: Epic 3 - Implement conversion to actual LightRAG parameters
        based on LightRAG service interface requirements.

        Returns:
            Dictionary of LightRAG initialization parameters
        """
        # TODO: Epic 3 - Map to actual LightRAG service parameters
        return {
            "entity_types": self.entity_types,
            # Additional parameters will be added in Epic 3
        }
