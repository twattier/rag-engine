"""Schema compatibility validation service.

This module provides validation functions to ensure backward compatibility
when updating metadata schemas.
"""

from __future__ import annotations

from typing import List

from pydantic import BaseModel

from shared.models.metadata import MetadataSchema, MetadataFieldDefinition


class SchemaIncompatibility(BaseModel):
    """Represents a schema incompatibility issue.

    Attributes:
        field: Field name that has incompatibility
        issue: Description of the incompatibility
    """

    field: str
    issue: str


def validate_schema_compatibility(
    old_schema: MetadataSchema,
    new_schema: MetadataSchema,
) -> List[SchemaIncompatibility]:
    """Validate backward compatibility between schemas.

    Checks for:
    1. Removed required fields (breaking change)
    2. Field type changes (breaking change)
    3. New required fields without defaults (breaking change)

    Args:
        old_schema: Current/old metadata schema
        new_schema: Proposed new metadata schema

    Returns:
        List of incompatibilities (empty if compatible)
    """
    incompatibilities: List[SchemaIncompatibility] = []

    # Create lookup dictionaries for field definitions
    old_fields = {f.field_name: f for f in old_schema.metadata_fields}
    new_fields = {f.field_name: f for f in new_schema.metadata_fields}

    # Check for removed required fields
    for field_name, field_def in old_fields.items():
        if field_name not in new_fields and field_def.required:
            incompatibilities.append(
                SchemaIncompatibility(
                    field=field_name,
                    issue="Cannot remove required field",
                )
            )

    # Check for field type changes
    for field_name, new_field in new_fields.items():
        if field_name in old_fields:
            old_field = old_fields[field_name]
            if old_field.type != new_field.type:
                incompatibilities.append(
                    SchemaIncompatibility(
                        field=field_name,
                        issue=f"Cannot change field type from '{old_field.type}' to '{new_field.type}'",
                    )
                )

    # Check for new required fields without defaults
    for field_name, new_field in new_fields.items():
        if (
            field_name not in old_fields
            and new_field.required
            and new_field.default is None
        ):
            incompatibilities.append(
                SchemaIncompatibility(
                    field=field_name,
                    issue="Cannot add required field without default value",
                )
            )

    return incompatibilities
