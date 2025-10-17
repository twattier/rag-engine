"""Unit tests for entity extraction service."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from uuid import uuid4

import httpx
import pytest
import respx
import yaml

from services.lightrag.app.models.entity_types import ExtractedEntity
from services.lightrag.app.services.entity_extractor import EntityExtractor
from services.lightrag.app.utils.entity_config import clear_entity_types_cache


@pytest.fixture(autouse=True)
def reset_cache():
    """Clear entity types cache before each test."""
    clear_entity_types_cache()
    yield
    clear_entity_types_cache()


@pytest.fixture
def sample_entity_types_yaml():
    """Create temporary entity-types.yaml for testing."""
    entity_config = {
        "entity_types": [
            {
                "type_name": "person",
                "description": "Individual names",
                "examples": ["John Doe", "Jane Smith"],
            },
            {
                "type_name": "company",
                "description": "Organizations",
                "examples": ["Google", "Microsoft"],
            },
            {
                "type_name": "skill",
                "description": "Professional skills",
                "examples": ["Python", "Project management"],
            },
        ]
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(entity_config, f)
        temp_path = f.name

    yield temp_path

    Path(temp_path).unlink(missing_ok=True)


@pytest.fixture
def entity_extractor(sample_entity_types_yaml):
    """Create EntityExtractor instance for testing."""
    return EntityExtractor(
        entity_types_path=sample_entity_types_yaml,
        llm_endpoint="http://localhost:11434/v1",
        llm_model="test-model",
    )


def test_entity_extractor_initialization(entity_extractor):
    """Test EntityExtractor initializes correctly."""
    assert entity_extractor.entity_types_path is not None
    assert len(entity_extractor.entity_types) == 3
    assert entity_extractor.llm_model == "test-model"


@pytest.mark.asyncio
@respx.mock
async def test_extract_entities_success(entity_extractor):
    """Test successful entity extraction from document."""
    # Mock LLM response
    llm_response = {
        "choices": [
            {
                "message": {
                    "content": json.dumps([
                        {
                            "entity_name": "John Doe",
                            "entity_type": "person",
                            "confidence": 0.95,
                            "text_span": "char 0-8",
                        },
                        {
                            "entity_name": "Google",
                            "entity_type": "company",
                            "confidence": 0.90,
                            "text_span": "char 18-24",
                        },
                    ])
                }
            }
        ]
    }

    # Mock HTTP request
    respx.post("http://localhost:11434/v1/chat/completions").mock(
        return_value=httpx.Response(200, json=llm_response)
    )

    # Test document
    doc_id = uuid4()
    document = {
        "id": str(doc_id),
        "text": "John Doe works at Google as a Python developer.",
        "metadata": {"category": "cv"},
    }

    # Extract entities
    entities = await entity_extractor.extract_entities(document)

    # Assertions
    assert len(entities) == 2

    # Check first entity
    assert entities[0].entity_name == "John Doe"
    assert entities[0].entity_type == "person"
    assert entities[0].confidence_score == 0.95
    assert entities[0].source_document_id == doc_id

    # Check second entity
    assert entities[1].entity_name == "Google"
    assert entities[1].entity_type == "company"
    assert entities[1].confidence_score == 0.90


@pytest.mark.asyncio
@respx.mock
async def test_extract_entities_with_markdown_code_block(entity_extractor):
    """Test entity extraction when LLM returns JSON in markdown code block."""
    # Mock LLM response with markdown code block
    llm_response = {
        "choices": [
            {
                "message": {
                    "content": f"""Here are the extracted entities:

```json
{json.dumps([
    {
        "entity_name": "Python",
        "entity_type": "skill",
        "confidence": 0.85,
        "text_span": "char 30-36",
    }
])}
```

These entities were found in the document."""
                }
            }
        ]
    }

    respx.post("http://localhost:11434/v1/chat/completions").mock(
        return_value=httpx.Response(200, json=llm_response)
    )

    doc_id = uuid4()
    document = {
        "id": str(doc_id),
        "text": "John Doe is proficient in Python programming.",
        "metadata": {},
    }

    entities = await entity_extractor.extract_entities(document)

    assert len(entities) == 1
    assert entities[0].entity_name == "Python"
    assert entities[0].entity_type == "skill"


@pytest.mark.asyncio
async def test_extract_entities_missing_document_id(entity_extractor):
    """Test error handling when document is missing ID."""
    document = {
        "text": "Some text",
    }

    with pytest.raises(ValueError, match="Document must have 'id' field"):
        await entity_extractor.extract_entities(document)


@pytest.mark.asyncio
async def test_extract_entities_missing_document_text(entity_extractor):
    """Test error handling when document is missing text."""
    document = {
        "id": str(uuid4()),
    }

    with pytest.raises(ValueError, match="Document must have 'text' field"):
        await entity_extractor.extract_entities(document)


@pytest.mark.asyncio
@respx.mock
async def test_extract_entities_llm_failure(entity_extractor):
    """Test error handling when LLM call fails."""
    # Mock HTTP error
    respx.post("http://localhost:11434/v1/chat/completions").mock(
        return_value=httpx.Response(500, json={"error": "Internal server error"})
    )

    doc_id = uuid4()
    document = {
        "id": str(doc_id),
        "text": "Test document",
        "metadata": {},
    }

    with pytest.raises(RuntimeError, match="LLM call failed"):
        await entity_extractor.extract_entities(document)


@pytest.mark.asyncio
@respx.mock
async def test_extract_entities_auto_text_span(entity_extractor):
    """Test automatic text span calculation when not provided by LLM."""
    # Mock LLM response without text_span
    llm_response = {
        "choices": [
            {
                "message": {
                    "content": json.dumps([
                        {
                            "entity_name": "Docker",
                            "entity_type": "skill",
                            "confidence": 0.88,
                        }
                    ])
                }
            }
        ]
    }

    respx.post("http://localhost:11434/v1/chat/completions").mock(
        return_value=httpx.Response(200, json=llm_response)
    )

    doc_id = uuid4()
    document = {
        "id": str(doc_id),
        "text": "Experience with Docker and Kubernetes.",
        "metadata": {},
    }

    entities = await entity_extractor.extract_entities(document)

    assert len(entities) == 1
    # Text span should be auto-calculated
    assert entities[0].text_span.startswith("char")
    assert "16-22" in entities[0].text_span  # "Docker" position


@pytest.mark.asyncio
@respx.mock
async def test_extract_entities_no_json_in_response(entity_extractor):
    """Test handling when LLM returns no JSON array."""
    # Mock LLM response with no JSON
    llm_response = {
        "choices": [
            {
                "message": {
                    "content": "I could not extract any entities from this document."
                }
            }
        ]
    }

    respx.post("http://localhost:11434/v1/chat/completions").mock(
        return_value=httpx.Response(200, json=llm_response)
    )

    doc_id = uuid4()
    document = {
        "id": str(doc_id),
        "text": "Test document",
        "metadata": {},
    }

    entities = await entity_extractor.extract_entities(document)

    # Should return empty list instead of crashing
    assert len(entities) == 0


def test_find_text_span(entity_extractor):
    """Test text span calculation."""
    document_text = "John Doe works at Google."

    # Test finding entity
    span = entity_extractor._find_text_span("John Doe", document_text)
    assert span == "char 0-8"

    span2 = entity_extractor._find_text_span("Google", document_text)
    assert span2 == "char 18-24"

    # Test entity not found
    span3 = entity_extractor._find_text_span("Microsoft", document_text)
    assert span3 == "not found"


def test_find_text_span_case_insensitive(entity_extractor):
    """Test text span calculation is case-insensitive."""
    document_text = "PYTHON programming language"

    span = entity_extractor._find_text_span("Python", document_text)
    assert span == "char 0-6"
