"""Integration tests for entity types configuration API endpoints.

This module tests the GET and POST endpoints for entity type management.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from httpx import AsyncClient

from app.config import settings
from app.dependencies import get_entity_types_config
from shared.config.entity_loader import save_entity_types
from shared.models.entity_types import EntityTypeDefinition, EntityTypesConfig


@pytest.fixture
def temp_entity_config_file():
    """Create a temporary entity types configuration file for testing."""
    # Create initial entity types configuration
    initial_config = EntityTypesConfig(
        entity_types=[
            EntityTypeDefinition(
                type_name="person",
                description="Individual people, including names, roles, and titles",
                examples=["John Doe", "Dr. Jane Smith", "CEO Bob Johnson"],
            ),
            EntityTypeDefinition(
                type_name="organization",
                description="Companies, institutions, agencies, and groups",
                examples=["Microsoft Corporation", "Stanford University"],
            ),
            EntityTypeDefinition(
                type_name="concept",
                description="Abstract ideas, theories, methodologies, and principles",
                examples=["Machine Learning", "Agile Methodology"],
            ),
        ]
    )

    # Create temporary file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        temp_path = Path(f.name)

    # Save config to file
    save_entity_types(initial_config, str(temp_path))

    # Override settings for tests
    original_path = settings.ENTITY_TYPES_CONFIG_PATH
    settings.ENTITY_TYPES_CONFIG_PATH = str(temp_path)

    # Clear dependency cache
    get_entity_types_config.cache_clear()

    yield temp_path

    # Cleanup
    settings.ENTITY_TYPES_CONFIG_PATH = original_path
    get_entity_types_config.cache_clear()
    temp_path.unlink(missing_ok=True)


@pytest.mark.asyncio
async def test_get_entity_types_endpoint(
    async_client: AsyncClient, temp_entity_config_file: Path
):
    """Test GET /api/v1/config/entity-types endpoint returns default entity types."""
    response = await async_client.get("/api/v1/config/entity-types")

    assert response.status_code == 200
    result = response.json()

    # Verify response structure
    assert "entity_types" in result
    assert isinstance(result["entity_types"], list)
    assert len(result["entity_types"]) == 3

    # Verify first entity type
    first_entity = result["entity_types"][0]
    assert first_entity["type_name"] == "person"
    assert "description" in first_entity
    assert "examples" in first_entity
    assert isinstance(first_entity["examples"], list)


@pytest.mark.asyncio
async def test_get_entity_types_returns_all_fields(
    async_client: AsyncClient, temp_entity_config_file: Path
):
    """Test GET endpoint returns all required fields for each entity type."""
    response = await async_client.get("/api/v1/config/entity-types")

    assert response.status_code == 200
    result = response.json()

    for entity_type in result["entity_types"]:
        assert "type_name" in entity_type
        assert "description" in entity_type
        assert "examples" in entity_type
        assert isinstance(entity_type["type_name"], str)
        assert isinstance(entity_type["description"], str)
        assert isinstance(entity_type["examples"], list)


@pytest.mark.asyncio
async def test_post_entity_type_success(
    async_client: AsyncClient, temp_entity_config_file: Path
):
    """Test POST /api/v1/config/entity-types successfully adds new entity type."""
    new_entity = {
        "type_name": "patent",
        "description": "Patents, intellectual property, and inventions",
        "examples": ["US Patent 10,123,456", "European Patent EP1234567"],
    }

    response = await async_client.post(
        "/api/v1/config/entity-types",
        json=new_entity,
        headers={"Authorization": "Bearer test-api-key"},
    )

    assert response.status_code == 201
    result = response.json()

    # Verify response structure
    assert "message" in result
    assert "patent" in result["message"]
    assert "entity_type" in result
    assert result["entity_type"]["type_name"] == "patent"
    assert result["entity_type"]["description"] == new_entity["description"]
    assert result["entity_type"]["examples"] == new_entity["examples"]


@pytest.mark.asyncio
async def test_post_entity_type_persisted_to_file(
    async_client: AsyncClient, temp_entity_config_file: Path
):
    """Test POST endpoint persists new entity type to configuration file."""
    new_entity = {
        "type_name": "product",
        "description": "Products, services, tools, and offerings",
        "examples": ["iPhone 15", "Microsoft Azure"],
    }

    # Add entity type
    response = await async_client.post(
        "/api/v1/config/entity-types",
        json=new_entity,
        headers={"Authorization": "Bearer test-api-key"},
    )

    assert response.status_code == 201

    # Verify it was persisted by fetching again
    get_response = await async_client.get("/api/v1/config/entity-types")
    assert get_response.status_code == 200

    result = get_response.json()
    entity_types = result["entity_types"]

    # Should now have 4 entity types (3 initial + 1 new)
    assert len(entity_types) == 4

    # Verify new entity is in the list
    product_entities = [et for et in entity_types if et["type_name"] == "product"]
    assert len(product_entities) == 1
    assert product_entities[0]["description"] == new_entity["description"]


@pytest.mark.asyncio
async def test_post_entity_type_requires_authentication(
    async_client: AsyncClient, temp_entity_config_file: Path
):
    """Test POST endpoint requires X-API-Key authentication."""
    new_entity = {
        "type_name": "location",
        "description": "Geographic locations",
        "examples": ["San Francisco, CA"],
    }

    # Request without Authorization header
    response = await async_client.post(
        "/api/v1/config/entity-types",
        json=new_entity,
    )

    assert response.status_code == 401
    result = response.json()
    assert "detail" in result


@pytest.mark.asyncio
async def test_post_entity_type_invalid_api_key(
    async_client: AsyncClient, temp_entity_config_file: Path
):
    """Test POST endpoint rejects invalid API key."""
    new_entity = {
        "type_name": "location",
        "description": "Geographic locations",
        "examples": ["San Francisco, CA"],
    }

    # Request with invalid API key
    response = await async_client.post(
        "/api/v1/config/entity-types",
        json=new_entity,
        headers={"Authorization": "Bearer invalid-key"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_post_entity_type_duplicate_returns_409(
    async_client: AsyncClient, temp_entity_config_file: Path
):
    """Test POST endpoint returns 409 Conflict for duplicate entity type."""
    duplicate_entity = {
        "type_name": "person",  # Already exists in temp config
        "description": "Different description",
        "examples": ["Example"],
    }

    response = await async_client.post(
        "/api/v1/config/entity-types",
        json=duplicate_entity,
        headers={"Authorization": "Bearer test-api-key"},
    )

    assert response.status_code == 409
    result = response.json()
    assert "error" in result
    assert result["error"]["code"] == "ENTITY_TYPE_EXISTS"
    assert "already exists" in result["error"]["message"]


@pytest.mark.asyncio
async def test_post_entity_type_invalid_type_name_uppercase(
    async_client: AsyncClient, temp_entity_config_file: Path
):
    """Test POST endpoint rejects entity type with uppercase type_name."""
    invalid_entity = {
        "type_name": "Patent",  # Invalid: uppercase
        "description": "Patents and IP",
        "examples": [],
    }

    response = await async_client.post(
        "/api/v1/config/entity-types",
        json=invalid_entity,
        headers={"Authorization": "Bearer test-api-key"},
    )

    assert response.status_code == 422
    result = response.json()
    assert "detail" in result


@pytest.mark.asyncio
async def test_post_entity_type_invalid_type_name_with_spaces(
    async_client: AsyncClient, temp_entity_config_file: Path
):
    """Test POST endpoint rejects entity type with spaces in type_name."""
    invalid_entity = {
        "type_name": "legal case",  # Invalid: contains space
        "description": "Legal cases",
        "examples": [],
    }

    response = await async_client.post(
        "/api/v1/config/entity-types",
        json=invalid_entity,
        headers={"Authorization": "Bearer test-api-key"},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_post_entity_type_missing_required_fields(
    async_client: AsyncClient, temp_entity_config_file: Path
):
    """Test POST endpoint rejects entity type missing required fields."""
    incomplete_entity = {
        "type_name": "technology",
        # Missing description field
        "examples": ["Python"],
    }

    response = await async_client.post(
        "/api/v1/config/entity-types",
        json=incomplete_entity,
        headers={"Authorization": "Bearer test-api-key"},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_post_entity_type_with_empty_examples(
    async_client: AsyncClient, temp_entity_config_file: Path
):
    """Test POST endpoint accepts entity type with empty examples list."""
    entity_with_no_examples = {
        "type_name": "event",
        "description": "Events, meetings, conferences",
        "examples": [],
    }

    response = await async_client.post(
        "/api/v1/config/entity-types",
        json=entity_with_no_examples,
        headers={"Authorization": "Bearer test-api-key"},
    )

    assert response.status_code == 201
    result = response.json()
    assert result["entity_type"]["examples"] == []


@pytest.mark.asyncio
async def test_post_entity_type_invalidates_cache(
    async_client: AsyncClient, temp_entity_config_file: Path
):
    """Test POST endpoint invalidates cache so GET returns fresh data."""
    # First GET request
    response1 = await async_client.get("/api/v1/config/entity-types")
    assert response1.status_code == 200
    initial_count = len(response1.json()["entity_types"])

    # Add new entity type
    new_entity = {
        "type_name": "technology",
        "description": "Technologies and frameworks",
        "examples": ["Python", "Docker"],
    }

    post_response = await async_client.post(
        "/api/v1/config/entity-types",
        json=new_entity,
        headers={"Authorization": "Bearer test-api-key"},
    )

    assert post_response.status_code == 201

    # Second GET request should return updated data (not cached)
    response2 = await async_client.get("/api/v1/config/entity-types")
    assert response2.status_code == 200
    updated_count = len(response2.json()["entity_types"])

    assert updated_count == initial_count + 1


@pytest.mark.asyncio
async def test_get_entity_types_no_authentication_required(
    async_client: AsyncClient, temp_entity_config_file: Path
):
    """Test GET endpoint does not require authentication."""
    response = await async_client.get("/api/v1/config/entity-types")

    # Should succeed without Authorization header
    assert response.status_code == 200
