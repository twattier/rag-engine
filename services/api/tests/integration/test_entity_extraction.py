"""
Integration tests for Story 3.2: Custom Entity Extraction with Entity Types.

Tests the custom entity extraction service (separate from LightRAG's built-in extraction):
- Entity extraction using configured entity types from entity-types.yaml
- Entity storage in Neo4j with proper schema
- Entity deduplication using fuzzy matching
- CONTAINS relationships from documents to entities
- Confidence scores and text spans

Usage:
    pytest services/api/tests/integration/test_entity_extraction.py -v
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from neo4j import AsyncGraphDatabase

from services.lightrag.app.db.neo4j_entity_store import Neo4jEntityStore
from services.lightrag.app.models.entity_types import ExtractedEntity
from services.lightrag.app.services.entity_deduplication import EntityDeduplicator
from services.lightrag.app.services.entity_extractor import EntityExtractor
from services.lightrag.app.utils.entity_config import load_entity_types


@pytest.mark.asyncio
async def test_entity_extraction_with_custom_types(
    test_neo4j_driver, test_entity_types_yaml
):
    """
    Test custom entity extraction using configured entity types.

    This test validates AC 1, 2, 3: Entity type loading, prompt engineering,
    and extraction with metadata.
    """
    # Initialize entity extractor
    extractor = EntityExtractor(
        entity_types_path=test_entity_types_yaml,
        llm_endpoint="http://localhost:11434/v1",
        llm_model="qwen2.5:7b-instruct-q4_K_M",
    )

    # Create test document
    doc_id = uuid4()
    document = {
        "id": str(doc_id),
        "text": "John Doe is a Senior Software Engineer at Google. "
        "He has expertise in Python, Docker, and Kubernetes. "
        "He previously worked at Microsoft as a Data Scientist.",
        "metadata": {"category": "cv"},
    }

    # Extract entities
    # Note: This will call the actual LLM, so test may be slow
    # In a real test environment, you might want to mock the LLM
    try:
        entities = await extractor.extract_entities(document)
    except Exception as e:
        pytest.skip(f"LLM not available for integration test: {e}")

    # Validate extraction results
    assert len(entities) > 0, "No entities extracted"

    # Validate entity structure (AC 3)
    for entity in entities:
        assert isinstance(entity, ExtractedEntity)
        assert entity.entity_name
        assert entity.entity_type
        assert 0.0 <= entity.confidence_score <= 1.0
        assert entity.source_document_id == doc_id
        # text_span may be "not found" for paraphrased entities
        assert entity.text_span is not None

    # Validate entity types match configuration
    entity_types_config = load_entity_types(test_entity_types_yaml)
    configured_types = {et.type_name for et in entity_types_config}
    extracted_types = {e.entity_type for e in entities}

    assert extracted_types.issubset(configured_types), \
        f"Extracted types {extracted_types} not in configured types {configured_types}"

    print(f"\n✓ Extracted {len(entities)} entities:")
    for entity in entities:
        print(
            f"  - {entity.entity_name} ({entity.entity_type}) "
            f"[confidence: {entity.confidence_score:.2f}]"
        )


@pytest.mark.asyncio
async def test_entity_storage_in_neo4j(test_neo4j_driver):
    """
    Test entity storage in Neo4j with proper schema.

    This test validates AC 4: Neo4j graph schema with Entity nodes and
    CONTAINS relationships.
    """
    # Initialize entity store
    entity_store = Neo4jEntityStore(
        driver=test_neo4j_driver, database="neo4j"
    )

    # Create test entity
    doc_id = uuid4()
    entity = ExtractedEntity(
        entity_name="Python",
        entity_type="skill",
        confidence_score=0.95,
        source_document_id=doc_id,
        text_span="char 45-51",
    )

    # Store entity
    entity_id = await entity_store.store_entity(
        entity, embedding=[0.1] * 384  # Mock embedding
    )

    assert entity_id is not None

    # Verify entity in Neo4j
    async with test_neo4j_driver.session(database="neo4j") as session:
        result = await session.run(
            """
            MATCH (e:Entity {id: $entity_id})
            RETURN e.id AS id, e.name AS name, e.type AS type,
                   e.confidence_score AS confidence, e.embedding AS embedding
            """,
            entity_id=entity_id,
        )
        record = await result.single()

        assert record is not None
        assert record["name"] == "Python"
        assert record["type"] == "skill"
        assert record["confidence"] == 0.95
        assert record["embedding"] is not None
        assert len(record["embedding"]) == 384

        # Cleanup
        await session.run(
            "MATCH (e:Entity {id: $entity_id}) DETACH DELETE e",
            entity_id=entity_id,
        )

    print(f"\n✓ Entity stored successfully in Neo4j with ID: {entity_id}")


@pytest.mark.asyncio
async def test_entity_deduplication(test_neo4j_driver):
    """
    Test entity deduplication using fuzzy matching.

    This test validates AC 5: Duplicate entity resolution with >90% similarity.
    """
    # Initialize services
    entity_store = Neo4jEntityStore(
        driver=test_neo4j_driver, database="neo4j"
    )
    deduplicator = EntityDeduplicator(
        entity_store=entity_store, similarity_threshold=90.0
    )

    doc_id = uuid4()

    # Create first entity
    entity1 = ExtractedEntity(
        entity_name="Microsoft",
        entity_type="company",
        confidence_score=0.90,
        source_document_id=doc_id,
        text_span="char 10-19",
    )

    entity1_id = await deduplicator.find_or_create_entity(entity1)
    assert entity1_id is not None

    # Create similar entity (typo variant)
    entity2 = ExtractedEntity(
        entity_name="Micrsoft",  # Typo - 95%+ similar to "Microsoft"
        entity_type="company",
        confidence_score=0.92,
        source_document_id=doc_id,
        text_span="char 50-58",
    )

    entity2_id = await deduplicator.find_or_create_entity(entity2)

    # Should return same ID (deduplicated)
    assert entity2_id == entity1_id, \
        "Similar entities should be deduplicated"

    # Create different entity
    entity3 = ExtractedEntity(
        entity_name="Google",  # Different company
        entity_type="company",
        confidence_score=0.88,
        source_document_id=doc_id,
        text_span="char 80-86",
    )

    entity3_id = await deduplicator.find_or_create_entity(entity3)

    # Should return different ID
    assert entity3_id != entity1_id, \
        "Different entities should not be deduplicated"

    # Cleanup
    async with test_neo4j_driver.session(database="neo4j") as session:
        await session.run(
            "MATCH (e:Entity) WHERE e.id IN [$id1, $id2] DETACH DELETE e",
            id1=entity1_id,
            id2=entity3_id,
        )

    print(f"\n✓ Entity deduplication working correctly")
    print(f"  - Microsoft & Micrsoft → same entity (ID: {entity1_id})")
    print(f"  - Google → different entity (ID: {entity3_id})")


@pytest.mark.asyncio
async def test_document_contains_relationship(test_neo4j_driver):
    """
    Test CONTAINS relationship from Document to Entity.

    This test validates AC 4: (:Document)-[:CONTAINS]->(:Entity) relationships.
    """
    # Initialize entity store
    entity_store = Neo4jEntityStore(
        driver=test_neo4j_driver, database="neo4j"
    )

    # Create test document in Neo4j
    doc_id = uuid4()
    async with test_neo4j_driver.session(database="neo4j") as session:
        await session.run(
            """
            CREATE (d:Document {
                id: $doc_id,
                filename: 'test.txt',
                status: 'indexed'
            })
            """,
            doc_id=str(doc_id),
        )

    # Create and store entity
    entity = ExtractedEntity(
        entity_name="Docker",
        entity_type="technology",
        confidence_score=0.93,
        source_document_id=doc_id,
        text_span="char 120-126",
    )

    entity_id = await entity_store.store_entity(entity)

    # Create CONTAINS relationship
    await entity_store.create_document_contains_relationship(
        document_id=doc_id,
        entity_id=entity_id,
        text_span=entity.text_span,
        confidence=entity.confidence_score,
    )

    # Verify relationship in Neo4j
    async with test_neo4j_driver.session(database="neo4j") as session:
        result = await session.run(
            """
            MATCH (d:Document {id: $doc_id})-[r:CONTAINS]->(e:Entity {id: $entity_id})
            RETURN r.text_span AS text_span, r.confidence AS confidence
            """,
            doc_id=str(doc_id),
            entity_id=entity_id,
        )
        record = await result.single()

        assert record is not None
        assert record["text_span"] == "char 120-126"
        assert record["confidence"] == 0.93

        # Cleanup
        await session.run(
            "MATCH (d:Document {id: $doc_id}) DETACH DELETE d",
            doc_id=str(doc_id),
        )
        await session.run(
            "MATCH (e:Entity {id: $entity_id}) DETACH DELETE e",
            entity_id=entity_id,
        )

    print(f"\n✓ CONTAINS relationship created successfully")
    print(f"  Document {doc_id} → Entity {entity_id}")


# Fixtures for integration tests
@pytest.fixture
def test_entity_types_yaml(tmp_path):
    """Create temporary entity-types.yaml for testing."""
    import yaml

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
                "examples": ["Python", "Docker"],
            },
            {
                "type_name": "technology",
                "description": "Technologies and tools",
                "examples": ["Kubernetes", "AWS"],
            },
            {
                "type_name": "job",
                "description": "Job titles",
                "examples": ["Software Engineer", "Data Scientist"],
            },
        ]
    }

    config_file = tmp_path / "entity-types.yaml"
    with open(config_file, "w") as f:
        yaml.dump(entity_config, f)

    yield str(config_file)


@pytest.fixture
async def test_neo4j_driver():
    """Create Neo4j driver for integration tests."""
    import os

    neo4j_uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    neo4j_auth = os.getenv("NEO4J_AUTH", "neo4j/password")
    username, password = neo4j_auth.split("/")

    driver = AsyncGraphDatabase.driver(neo4j_uri, auth=(username, password))

    yield driver

    await driver.close()
