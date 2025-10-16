"""Configuration management API endpoints.

This module provides REST API endpoints for managing entity types and metadata schema configuration.
"""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, status, Request

from app.config import settings
from app.dependencies import get_entity_types_config, get_metadata_schema, verify_api_key
from app.models.responses import SchemaIncompatibilityError, SchemaUpdateResponse
from shared.config.entity_loader import (
    add_entity_type_to_file,
    load_cached_entity_types,
)
from shared.config.metadata_loader import (
    load_cached_metadata_schema,
    save_metadata_schema,
)
from shared.models.audit_log import log_schema_change
from shared.models.entity_types import (
    EntityTypeDefinition,
    EntityTypesConfig,
)
from shared.models.metadata import MetadataSchema
from shared.services.schema_validator import validate_schema_compatibility
from shared.utils.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/config", tags=["configuration"])


@router.get("/entity-types")
async def get_entity_types(
    config: EntityTypesConfig = Depends(get_entity_types_config),
) -> EntityTypesConfig:
    """Get currently configured entity types.

    Returns:
        EntityTypesConfig with all configured entity types

    Example Response:
        ```json
        {
            "entity_types": [
                {
                    "type_name": "person",
                    "description": "Individual people, including names, roles, and titles",
                    "examples": ["John Doe", "Dr. Jane Smith"]
                },
                {
                    "type_name": "organization",
                    "description": "Companies, institutions, agencies, and groups",
                    "examples": ["Microsoft Corporation", "Stanford University"]
                }
            ]
        }
        ```
    """
    return config


@router.post(
    "/entity-types",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(verify_api_key)],
)
async def add_entity_type(
    entity_type: EntityTypeDefinition,
) -> dict:
    """Add a new entity type to the configuration.

    This endpoint requires authentication via X-API-Key header.

    Args:
        entity_type: EntityTypeDefinition to add

    Returns:
        Success message with the added entity type

    Raises:
        HTTP 401: If API key is missing or invalid
        HTTP 409: If entity type already exists
        HTTP 500: If configuration file cannot be written

    Example Request:
        ```json
        {
            "type_name": "patent",
            "description": "Patents, intellectual property, and inventions",
            "examples": ["US Patent 10,123,456", "European Patent EP1234567"]
        }
        ```

    Example Response:
        ```json
        {
            "message": "Entity type 'patent' added successfully",
            "entity_type": {
                "type_name": "patent",
                "description": "Patents, intellectual property, and inventions",
                "examples": ["US Patent 10,123,456", "European Patent EP1234567"]
            }
        }
        ```
    """
    try:
        # Add entity type to file (will raise ValueError if duplicate)
        updated_config = add_entity_type_to_file(
            entity_type, settings.ENTITY_TYPES_CONFIG_PATH
        )

        # Invalidate dependency cache so next GET request gets fresh data
        get_entity_types_config.cache_clear()

        return {
            "message": f"Entity type '{entity_type.type_name}' added successfully",
            "entity_type": entity_type.model_dump(),
        }

    except ValueError as e:
        # Duplicate entity type or validation error
        error_msg = str(e)
        if "already exists" in error_msg:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": {
                        "code": "ENTITY_TYPE_EXISTS",
                        "message": error_msg,
                    }
                },
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": {
                        "code": "INVALID_ENTITY_TYPE",
                        "message": error_msg,
                    }
                },
            )

    except PermissionError as e:
        # File write permission error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "ENTITY_CONFIG_WRITE_FAILED",
                    "message": "Failed to persist entity type configuration to file",
                    "details": {
                        "file_path": settings.ENTITY_TYPES_CONFIG_PATH,
                        "reason": "Permission denied",
                    },
                }
            },
        )

    except OSError as e:
        # Other file I/O errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "ENTITY_CONFIG_WRITE_FAILED",
                    "message": "Failed to persist entity type configuration to file",
                    "details": {
                        "file_path": settings.ENTITY_TYPES_CONFIG_PATH,
                        "reason": str(e),
                    },
                }
            },
        )


@router.put(
    "/metadata-schema",
    status_code=status.HTTP_200_OK,
    response_model=SchemaUpdateResponse,
    responses={
        400: {"model": Dict[str, SchemaIncompatibilityError]},
        401: {"description": "Unauthorized - invalid or missing API key"},
        500: {"description": "Failed to save schema to file"},
    },
    dependencies=[Depends(verify_api_key)],
)
async def update_metadata_schema(
    new_schema: MetadataSchema,
    request: Request,
    current_schema: MetadataSchema = Depends(get_metadata_schema),
) -> SchemaUpdateResponse:
    """Update metadata schema with backward compatibility validation.

    This endpoint validates that the new schema is backward compatible with the
    existing schema before persisting changes.

    Args:
        new_schema: New metadata schema
        request: FastAPI request (for extracting API key)
        current_schema: Current metadata schema (injected dependency)

    Returns:
        SchemaUpdateResponse with change summary

    Raises:
        HTTP 400: If schema changes are not backward compatible
        HTTP 401: If API key is missing or invalid
        HTTP 500: If schema file cannot be written
    """
    try:
        # Validate backward compatibility
        incompatibilities = validate_schema_compatibility(current_schema, new_schema)

        if incompatibilities:
            # Convert to response model format
            incomp_dicts = [
                {"field": inc.field, "issue": inc.issue} for inc in incompatibilities
            ]

            logger.warning(
                "schema_update_rejected_incompatible",
                incompatibilities_count=len(incompatibilities),
                incompatibilities=incomp_dicts,
            )

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": {
                        "code": "SCHEMA_INCOMPATIBLE",
                        "message": "Schema update rejected: Breaking changes detected",
                        "incompatibilities": incomp_dicts,
                    }
                },
            )

        # Detect changes for audit log
        old_fields = {f.field_name for f in current_schema.metadata_fields}
        new_fields = {f.field_name for f in new_schema.metadata_fields}

        added_fields = list(new_fields - old_fields)
        removed_fields = list(old_fields - new_fields)

        # Check for modified fields (type or required changes)
        modified_fields = []
        old_field_defs = {f.field_name: f for f in current_schema.metadata_fields}
        new_field_defs = {f.field_name: f for f in new_schema.metadata_fields}

        for field_name in old_fields.intersection(new_fields):
            old_def = old_field_defs[field_name]
            new_def = new_field_defs[field_name]
            if old_def.default != new_def.default or old_def.description != new_def.description:
                modified_fields.append(field_name)

        changes_detected = bool(added_fields or removed_fields or modified_fields)
        reindex_required = bool(added_fields)  # Reindex needed if new fields added

        # Extract user from API key header
        api_key = request.headers.get("X-API-Key", "unknown")

        # Log schema change for audit trail
        log_schema_change(
            old_schema=current_schema,
            new_schema=new_schema,
            user=api_key[:8] + "..." if len(api_key) > 8 else api_key,
        )

        # Save to file
        save_metadata_schema(new_schema, settings.METADATA_SCHEMA_PATH)

        # Invalidate cache so next request gets fresh schema
        get_metadata_schema.cache_clear()

        logger.info(
            "metadata_schema_updated",
            added_fields=added_fields,
            removed_fields=removed_fields,
            modified_fields=modified_fields,
            reindex_required=reindex_required,
        )

        return SchemaUpdateResponse(
            message="Metadata schema updated successfully",
            schema_version="2.0",  # TODO: Implement proper versioning
            changes_detected=changes_detected,
            reindex_required=reindex_required,
            reindex_status="pending" if reindex_required else "not_required",
            added_fields=added_fields,
            removed_fields=removed_fields,
            modified_fields=modified_fields,
        )

    except PermissionError:
        logger.error(
            "metadata_schema_save_failed",
            file_path=settings.METADATA_SCHEMA_PATH,
            error="Permission denied",
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "SCHEMA_SAVE_FAILED",
                    "message": "Failed to save metadata schema to file",
                    "details": {
                        "file_path": settings.METADATA_SCHEMA_PATH,
                        "reason": "Permission denied",
                    },
                }
            },
        )

    except OSError as e:
        logger.error(
            "metadata_schema_save_failed",
            file_path=settings.METADATA_SCHEMA_PATH,
            error=str(e),
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "SCHEMA_SAVE_FAILED",
                    "message": "Failed to save metadata schema to file",
                    "details": {
                        "file_path": settings.METADATA_SCHEMA_PATH,
                        "reason": str(e),
                    },
                }
            },
        )
