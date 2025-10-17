"""Unit tests for relationship extraction service."""

from __future__ import annotations

import json
from uuid import uuid4

import httpx
import pytest
import respx

from app.models.entity_types import ExtractedEntity, ExtractedRelationship
from app.services.relationship_extractor import RelationshipExtractor


@pytest.fixture
def llm_endpoint() -> str:
    """LLM endpoint URL for testing."""
    return "http://localhost:11434/v1"


@pytest.fixture
def relationship_extractor(llm_endpoint: str) -> RelationshipExtractor:
    """Create RelationshipExtractor instance for testing."""
    return RelationshipExtractor(
        llm_endpoint=llm_endpoint,
        llm_model="test-model",
        llm_api_key="test-api-key",
    )


@pytest.fixture
def sample_entities() -> list[ExtractedEntity]:
    """Create sample entities for testing."""
    doc_id = uuid4()
    return [
        ExtractedEntity(
            entity_name="Python",
            entity_type="technology",
            confidence_score=0.95,
            source_document_id=doc_id,
            text_span="char 0-6",
        ),
        ExtractedEntity(
            entity_name="Programming Skills",
            entity_type="skill_category",
            confidence_score=0.90,
            source_document_id=doc_id,
            text_span="char 20-38",
        ),
        ExtractedEntity(
            entity_name="John Doe",
            entity_type="person",
            confidence_score=0.98,
            source_document_id=doc_id,
            text_span="char 50-58",
        ),
    ]


@pytest.fixture
def sample_document_text() -> str:
    """Sample document text for testing."""
    return """Python is a powerful programming language. Programming Skills are essential
    for software development. John Doe is an expert Python developer."""


@pytest.mark.asyncio
@respx.mock
async def test_extract_relationships_success(
    relationship_extractor: RelationshipExtractor,
    sample_entities: list[ExtractedEntity],
    sample_document_text: str,
    llm_endpoint: str,
):
    """Test successful relationship extraction."""
    # Mock LLM response
    llm_response = {
        "choices": [
            {
                "message": {
                    "content": """```json
[
  {
    "source_entity_name": "Python",
    "target_entity_name": "Programming Skills",
    "relationship_type": "PART_OF",
    "confidence_score": 0.92
  },
  {
    "source_entity_name": "John Doe",
    "target_entity_name": "Python",
    "relationship_type": "RELATED_TO",
    "confidence_score": 0.95
  }
]
```"""
                }
            }
        ]
    }

    # Mock HTTP request
    respx.post(f"{llm_endpoint}/chat/completions").mock(
        return_value=httpx.Response(200, json=llm_response)
    )

    # Extract relationships
    relationships = await relationship_extractor.extract_relationships(
        sample_entities, sample_document_text
    )

    # Assertions
    assert len(relationships) == 2

    # First relationship
    assert relationships[0].source_entity_name == "Python"
    assert relationships[0].target_entity_name == "Programming Skills"
    assert relationships[0].relationship_type == "PART_OF"
    assert relationships[0].confidence_score == 0.92
    assert relationships[0].source_document_id == sample_entities[0].source_document_id

    # Second relationship
    assert relationships[1].source_entity_name == "John Doe"
    assert relationships[1].target_entity_name == "Python"
    assert relationships[1].relationship_type == "RELATED_TO"
    assert relationships[1].confidence_score == 0.95


@pytest.mark.asyncio
async def test_extract_relationships_empty_entities(
    relationship_extractor: RelationshipExtractor,
    sample_document_text: str,
):
    """Test relationship extraction with empty entities list."""
    relationships = await relationship_extractor.extract_relationships(
        [], sample_document_text
    )

    assert relationships == []


@pytest.mark.asyncio
@respx.mock
async def test_extract_relationships_invalid_json(
    relationship_extractor: RelationshipExtractor,
    sample_entities: list[ExtractedEntity],
    sample_document_text: str,
    llm_endpoint: str,
):
    """Test relationship extraction with invalid JSON response."""
    # Mock invalid LLM response
    llm_response = {
        "choices": [
            {
                "message": {
                    "content": "This is not valid JSON"
                }
            }
        ]
    }

    # Mock HTTP request
    respx.post(f"{llm_endpoint}/chat/completions").mock(
        return_value=httpx.Response(200, json=llm_response)
    )

    # Extract relationships should return empty list for invalid JSON
    relationships = await relationship_extractor.extract_relationships(
        sample_entities, sample_document_text
    )

    assert relationships == []


@pytest.mark.asyncio
@respx.mock
async def test_extract_relationships_llm_failure(
    relationship_extractor: RelationshipExtractor,
    sample_entities: list[ExtractedEntity],
    sample_document_text: str,
    llm_endpoint: str,
):
    """Test relationship extraction when LLM call fails."""
    # Mock HTTP error
    respx.post(f"{llm_endpoint}/chat/completions").mock(
        return_value=httpx.Response(500, text="Internal Server Error")
    )

    # Should raise RuntimeError
    with pytest.raises(RuntimeError, match="LLM call failed"):
        await relationship_extractor.extract_relationships(
            sample_entities, sample_document_text
        )


@pytest.mark.asyncio
@respx.mock
async def test_extract_relationships_confidence_mapping(
    relationship_extractor: RelationshipExtractor,
    sample_entities: list[ExtractedEntity],
    sample_document_text: str,
    llm_endpoint: str,
):
    """Test that 'confidence' field is mapped to 'confidence_score'."""
    # Mock LLM response with 'confidence' instead of 'confidence_score'
    llm_response = {
        "choices": [
            {
                "message": {
                    "content": json.dumps([
                        {
                            "source_entity_name": "Python",
                            "target_entity_name": "Programming Skills",
                            "relationship_type": "PART_OF",
                            "confidence": 0.88,  # Using 'confidence' instead
                        }
                    ])
                }
            }
        ]
    }

    # Mock HTTP request
    respx.post(f"{llm_endpoint}/chat/completions").mock(
        return_value=httpx.Response(200, json=llm_response)
    )

    # Extract relationships
    relationships = await relationship_extractor.extract_relationships(
        sample_entities, sample_document_text
    )

    # Verify confidence was mapped correctly
    assert len(relationships) == 1
    assert relationships[0].confidence_score == 0.88


@pytest.mark.asyncio
@respx.mock
async def test_extract_relationships_all_relationship_types(
    relationship_extractor: RelationshipExtractor,
    llm_endpoint: str,
):
    """Test all supported relationship types."""
    doc_id = uuid4()
    entities = [
        ExtractedEntity(
            entity_name="Entity1",
            entity_type="test",
            confidence_score=0.9,
            source_document_id=doc_id,
        ),
        ExtractedEntity(
            entity_name="Entity2",
            entity_type="test",
            confidence_score=0.9,
            source_document_id=doc_id,
        ),
    ]

    # Test each relationship type
    relationship_types = [
        "MENTIONS", "RELATED_TO", "PART_OF", "IMPLEMENTS",
        "DEPENDS_ON", "LOCATED_IN", "AUTHORED_BY"
    ]

    for rel_type in relationship_types:
        llm_response = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps([
                            {
                                "source_entity_name": "Entity1",
                                "target_entity_name": "Entity2",
                                "relationship_type": rel_type,
                                "confidence_score": 0.85,
                            }
                        ])
                    }
                }
            ]
        }

        # Mock HTTP request
        respx.post(f"{llm_endpoint}/chat/completions").mock(
            return_value=httpx.Response(200, json=llm_response)
        )

        # Extract relationships
        relationships = await relationship_extractor.extract_relationships(
            entities, "Test document"
        )

        # Verify relationship type
        assert len(relationships) == 1
        assert relationships[0].relationship_type == rel_type


def test_relationship_type_validation():
    """Test relationship type validation in ExtractedRelationship model."""
    doc_id = uuid4()

    # Valid relationship type (lowercase should be converted to uppercase)
    rel = ExtractedRelationship(
        source_entity_name="Entity1",
        target_entity_name="Entity2",
        relationship_type="mentions",  # lowercase
        confidence_score=0.9,
        source_document_id=doc_id,
    )
    assert rel.relationship_type == "MENTIONS"

    # Invalid relationship type should raise error
    with pytest.raises(ValueError, match="relationship_type must be one of"):
        ExtractedRelationship(
            source_entity_name="Entity1",
            target_entity_name="Entity2",
            relationship_type="INVALID_TYPE",
            confidence_score=0.9,
            source_document_id=doc_id,
        )
