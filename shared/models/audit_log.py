"""Audit logging models for schema changes.

This module provides Pydantic models for tracking and logging schema changes
for audit and compliance purposes.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List

from pydantic import BaseModel, Field

import structlog

from shared.models.metadata import MetadataSchema

logger = structlog.get_logger(__name__)


class SchemaChangeLog(BaseModel):
    """Audit log entry for schema changes.

    Attributes:
        timestamp: When the change occurred
        user: User or API key that made the change
        old_schema_version: Version identifier of old schema
        new_schema_version: Version identifier of new schema
        change_description: Human-readable description of changes
        added_fields: List of field names that were added
        removed_fields: List of field names that were removed
        modified_fields: List of field names that were modified
    """

    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    user: str = Field(..., description="User or API key identifier")
    old_schema_version: str = Field(default="1.0")
    new_schema_version: str = Field(default="2.0")
    change_description: str
    added_fields: List[str] = Field(default_factory=list)
    removed_fields: List[str] = Field(default_factory=list)
    modified_fields: List[str] = Field(default_factory=list)


def log_schema_change(
    old_schema: MetadataSchema,
    new_schema: MetadataSchema,
    user: str,
) -> None:
    """Log schema change to structured logs.

    Args:
        old_schema: Previous metadata schema
        new_schema: New metadata schema
        user: User or API key that made the change
    """
    old_fields = {f.field_name for f in old_schema.metadata_fields}
    new_fields = {f.field_name for f in new_schema.metadata_fields}

    added = list(new_fields - old_fields)
    removed = list(old_fields - new_fields)

    # Check for modified fields (type or required changes)
    modified = []
    old_field_defs = {f.field_name: f for f in old_schema.metadata_fields}
    new_field_defs = {f.field_name: f for f in new_schema.metadata_fields}

    for field_name in old_fields.intersection(new_fields):
        old_def = old_field_defs[field_name]
        new_def = new_field_defs[field_name]
        if old_def.type != new_def.type or old_def.required != new_def.required:
            modified.append(field_name)

    change_description = (
        f"Added {len(added)} field(s), "
        f"removed {len(removed)} field(s), "
        f"modified {len(modified)} field(s)"
    )

    change_log = SchemaChangeLog(
        user=user,
        change_description=change_description,
        added_fields=added,
        removed_fields=removed,
        modified_fields=modified,
    )

    logger.info(
        "Metadata schema updated",
        audit_log=change_log.model_dump(),
    )
