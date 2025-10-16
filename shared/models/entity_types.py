"""Entity type configuration models for LightRAG knowledge graph construction.

This module defines Pydantic models for configuring entity types that guide
LightRAG's entity extraction during graph construction.
"""

from __future__ import annotations

from typing import List

from pydantic import BaseModel, Field, field_validator


class EntityTypeDefinition(BaseModel):
    """Definition of a single entity type for knowledge graph extraction.

    Attributes:
        type_name: Entity type name (lowercase, no spaces)
        description: Human-readable description of what this entity type represents
        examples: List of example entities of this type
    """

    type_name: str = Field(
        ...,
        description="Entity type name (lowercase, no spaces)",
        examples=["person", "organization", "concept"],
    )
    description: str = Field(
        ...,
        description="Description of what this entity type represents",
        examples=["Individual people, including names, roles, and titles"],
    )
    examples: List[str] = Field(
        default_factory=list,
        description="Example entities of this type",
        examples=[["John Doe", "Dr. Jane Smith", "CEO Bob Johnson"]],
    )

    @field_validator("type_name")
    @classmethod
    def validate_type_name(cls, v: str) -> str:
        """Ensure type_name is lowercase and contains no spaces.

        Args:
            v: The type_name value to validate

        Returns:
            The validated type_name

        Raises:
            ValueError: If type_name is not lowercase or contains spaces
        """
        if not v.islower():
            raise ValueError("type_name must be lowercase")
        if " " in v:
            raise ValueError("type_name cannot contain spaces")
        return v


class EntityTypesConfig(BaseModel):
    """Complete entity types configuration for knowledge graph construction.

    Attributes:
        entity_types: List of entity type definitions
    """

    entity_types: List[EntityTypeDefinition] = Field(
        ...,
        description="List of entity type definitions",
        min_length=1,
    )

    def get_type_names(self) -> List[str]:
        """Return list of entity type names.

        Returns:
            List of type_name strings from all entity type definitions
        """
        return [et.type_name for et in self.entity_types]

    def add_entity_type(self, entity_type: EntityTypeDefinition) -> None:
        """Add new entity type if unique.

        Args:
            entity_type: The entity type definition to add

        Raises:
            ValueError: If entity type with same type_name already exists
        """
        if entity_type.type_name in self.get_type_names():
            raise ValueError(f"Entity type '{entity_type.type_name}' already exists")
        self.entity_types.append(entity_type)

    def get_entity_type(self, type_name: str) -> EntityTypeDefinition | None:
        """Get entity type definition by type_name.

        Args:
            type_name: The type_name to search for

        Returns:
            EntityTypeDefinition if found, None otherwise
        """
        for et in self.entity_types:
            if et.type_name == type_name:
                return et
        return None
