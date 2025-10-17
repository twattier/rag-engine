"""Neo4j entity storage service for entity extraction."""

from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

import structlog
from neo4j import AsyncDriver

from ..models.entity_types import ExtractedEntity

logger = structlog.get_logger(__name__)


class Neo4jEntityStore:
    """Service for storing extracted entities in Neo4j."""

    def __init__(self, driver: AsyncDriver, database: str = "neo4j"):
        """Initialize Neo4j entity store.

        Args:
            driver: Neo4j async driver instance
            database: Database name (default: "neo4j")
        """
        self.driver = driver
        self.database = database

        logger.info("neo4j_entity_store_initialized", database=database)

    async def store_entity(
        self,
        entity: ExtractedEntity,
        embedding: Optional[List[float]] = None,
    ) -> str:
        """Store an entity in Neo4j.

        Args:
            entity: Extracted entity to store
            embedding: Optional vector embedding for entity (384-dim)

        Returns:
            Entity ID (UUID string)
        """
        entity_id = str(uuid4())

        query = """
        CREATE (e:Entity {
            id: $id,
            name: $name,
            type: $type,
            confidence_score: $confidence_score,
            source_doc_id: $source_doc_id,
            embedding: $embedding,
            created_at: datetime()
        })
        RETURN e.id AS id
        """

        params = {
            "id": entity_id,
            "name": entity.entity_name,
            "type": entity.entity_type,
            "confidence_score": entity.confidence_score,
            "source_doc_id": str(entity.source_document_id),
            "embedding": embedding,
        }

        async with self.driver.session(database=self.database) as session:
            result = await session.run(query, **params)
            record = await result.single()

            logger.debug(
                "entity_stored",
                entity_id=entity_id,
                entity_name=entity.entity_name,
                entity_type=entity.entity_type,
            )

            return record["id"]

    async def create_document_contains_relationship(
        self,
        document_id: UUID,
        entity_id: str,
        text_span: str,
        confidence: float,
    ) -> None:
        """Create CONTAINS relationship from Document to Entity.

        Args:
            document_id: Document UUID
            entity_id: Entity UUID
            text_span: Text span where entity appears (e.g., "char 245-260")
            confidence: Confidence score for this relationship
        """
        query = """
        MATCH (d:Document {id: $doc_id})
        MATCH (e:Entity {id: $entity_id})
        MERGE (d)-[r:CONTAINS {
            text_span: $text_span,
            confidence: $confidence
        }]->(e)
        RETURN d.id AS doc_id, e.id AS entity_id
        """

        params = {
            "doc_id": str(document_id),
            "entity_id": entity_id,
            "text_span": text_span,
            "confidence": confidence,
        }

        async with self.driver.session(database=self.database) as session:
            result = await session.run(query, **params)
            record = await result.single()

            if record:
                logger.debug(
                    "document_contains_relationship_created",
                    doc_id=str(document_id),
                    entity_id=entity_id,
                )
            else:
                logger.warning(
                    "document_or_entity_not_found",
                    doc_id=str(document_id),
                    entity_id=entity_id,
                )

    async def find_entity_by_name_and_type(
        self, entity_name: str, entity_type: str
    ) -> Optional[Dict[str, Any]]:
        """Find entity by exact name and type match.

        Args:
            entity_name: Entity name to search for
            entity_type: Entity type to filter by

        Returns:
            Entity dict with id, name, type, confidence_score or None
        """
        query = """
        MATCH (e:Entity {name: $name, type: $type})
        RETURN e.id AS id, e.name AS name, e.type AS type, e.confidence_score AS confidence_score
        LIMIT 1
        """

        params = {"name": entity_name, "type": entity_type}

        async with self.driver.session(database=self.database) as session:
            result = await session.run(query, **params)
            record = await result.single()

            if record:
                return {
                    "id": record["id"],
                    "name": record["name"],
                    "type": record["type"],
                    "confidence_score": record["confidence_score"],
                }

            return None

    async def find_similar_entities(
        self, entity_name: str, entity_type: str
    ) -> List[Dict[str, Any]]:
        """Find entities with similar names (same type).

        Args:
            entity_name: Entity name to search for
            entity_type: Entity type to filter by

        Returns:
            List of entity dicts with id, name, type, confidence_score
        """
        query = """
        MATCH (e:Entity {type: $type})
        RETURN e.id AS id, e.name AS name, e.type AS type, e.confidence_score AS confidence_score
        """

        params = {"type": entity_type}

        async with self.driver.session(database=self.database) as session:
            result = await session.run(query, **params)
            records = await result.data()

            return [
                {
                    "id": rec["id"],
                    "name": rec["name"],
                    "type": rec["type"],
                    "confidence_score": rec["confidence_score"],
                }
                for rec in records
            ]

    async def merge_entities(
        self, source_entity_id: str, target_entity_id: str, new_confidence: float
    ) -> None:
        """Merge source entity into target entity.

        This updates the target entity's confidence score and redirects all
        relationships from source to target, then deletes the source entity.

        Args:
            source_entity_id: Entity to merge (will be deleted)
            target_entity_id: Entity to keep
            new_confidence: Updated confidence score for target
        """
        query = """
        MATCH (source:Entity {id: $source_id})
        MATCH (target:Entity {id: $target_id})

        // Update target confidence score
        SET target.confidence_score = $new_confidence

        // Redirect all CONTAINS relationships
        OPTIONAL MATCH (d:Document)-[r:CONTAINS]->(source)
        MERGE (d)-[new_r:CONTAINS]->(target)
        ON CREATE SET new_r = properties(r)
        DELETE r

        // Delete source entity
        DETACH DELETE source

        RETURN target.id AS target_id
        """

        params = {
            "source_id": source_entity_id,
            "target_id": target_entity_id,
            "new_confidence": new_confidence,
        }

        async with self.driver.session(database=self.database) as session:
            result = await session.run(query, **params)
            record = await result.single()

            if record:
                logger.info(
                    "entities_merged",
                    source_id=source_entity_id,
                    target_id=target_entity_id,
                    new_confidence=new_confidence,
                )
            else:
                logger.warning(
                    "entity_merge_failed",
                    source_id=source_entity_id,
                    target_id=target_entity_id,
                )
