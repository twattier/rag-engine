"""Configuration management API endpoints.

This module provides REST API endpoints for managing entity types configuration.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.config import settings
from app.dependencies import get_entity_types_config, verify_api_key
from shared.config.entity_loader import (
    add_entity_type_to_file,
    load_cached_entity_types,
)
from shared.models.entity_types import (
    EntityTypeDefinition,
    EntityTypesConfig,
)

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
