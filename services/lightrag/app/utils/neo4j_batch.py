"""Batch writer utility for Neo4j performance optimization."""

from __future__ import annotations

import time
from typing import Any, Dict, List

import structlog
from neo4j import AsyncSession

logger = structlog.get_logger(__name__)


class BatchWriter:
    """Batch writer for Neo4j entities and relationships."""

    def __init__(self, session: AsyncSession, batch_size: int = 100):
        """Initialize batch writer.

        Args:
            session: Neo4j async session
            batch_size: Number of items to batch before executing (default: 100)
        """
        self.session = session
        self.batch_size = batch_size
        self.entity_buffer: List[Dict[str, Any]] = []
        self.relationship_buffer: List[Dict[str, Any]] = []

        logger.info("batch_writer_initialized", batch_size=batch_size)

    async def add_entity(self, entity: Dict[str, Any]) -> None:
        """Add entity to batch buffer.

        Args:
            entity: Entity dictionary with keys: id, name, type, embedding, confidence_score, source_doc_id
        """
        self.entity_buffer.append(entity)

        if len(self.entity_buffer) >= self.batch_size:
            await self.flush_entities()

    async def add_relationship(self, relationship: Dict[str, Any]) -> None:
        """Add relationship to batch buffer.

        Args:
            relationship: Relationship dictionary with keys: id, source_name, target_name, rel_type, confidence, source_doc_id
        """
        self.relationship_buffer.append(relationship)

        if len(self.relationship_buffer) >= self.batch_size:
            await self.flush_relationships()

    async def flush_entities(self) -> None:
        """Flush entity buffer to Neo4j using batched transaction."""
        if not self.entity_buffer:
            return

        start_time = time.time()
        batch_count = len(self.entity_buffer)

        try:
            query = """
            UNWIND $batch AS item
            CREATE (e:Entity {
                id: item.id,
                name: item.name,
                type: item.type,
                embedding: item.embedding,
                confidence_score: item.confidence_score,
                source_doc_id: item.source_doc_id,
                created_at: datetime()
            })
            """

            await self.session.run(query, batch=self.entity_buffer)

            elapsed_time = time.time() - start_time
            entities_per_second = batch_count / elapsed_time if elapsed_time > 0 else 0

            logger.info(
                "batch_entities_flushed",
                count=batch_count,
                elapsed_seconds=round(elapsed_time, 3),
                entities_per_second=round(entities_per_second, 2),
            )

            self.entity_buffer.clear()

        except Exception as e:
            logger.error(
                "batch_entity_flush_failed",
                error=str(e),
                batch_count=batch_count,
            )

            # Retry with smaller batches (binary search approach)
            if batch_count > 1:
                await self._retry_with_smaller_batches(
                    self.entity_buffer, self._create_single_entity
                )
                self.entity_buffer.clear()
            else:
                raise

    async def flush_relationships(self) -> None:
        """Flush relationship buffer to Neo4j using batched transaction."""
        if not self.relationship_buffer:
            return

        start_time = time.time()
        batch_count = len(self.relationship_buffer)

        try:
            query = """
            UNWIND $batch AS item
            MATCH (e1:Entity {name: item.source_name})
            MATCH (e2:Entity {name: item.target_name})
            CREATE (e1)-[r:RELATIONSHIP {
                id: item.id,
                type: item.rel_type,
                confidence: item.confidence,
                source_doc_id: item.source_doc_id,
                created_at: datetime()
            }]->(e2)
            """

            await self.session.run(query, batch=self.relationship_buffer)

            elapsed_time = time.time() - start_time
            relationships_per_second = batch_count / elapsed_time if elapsed_time > 0 else 0

            logger.info(
                "batch_relationships_flushed",
                count=batch_count,
                elapsed_seconds=round(elapsed_time, 3),
                relationships_per_second=round(relationships_per_second, 2),
            )

            self.relationship_buffer.clear()

        except Exception as e:
            logger.error(
                "batch_relationship_flush_failed",
                error=str(e),
                batch_count=batch_count,
            )

            # Retry with smaller batches (binary search approach)
            if batch_count > 1:
                await self._retry_with_smaller_batches(
                    self.relationship_buffer, self._create_single_relationship
                )
                self.relationship_buffer.clear()
            else:
                raise

    async def flush_all(self) -> None:
        """Flush all pending entities and relationships."""
        await self.flush_entities()
        await self.flush_relationships()

    async def _retry_with_smaller_batches(
        self, items: List[Dict[str, Any]], single_item_fn
    ) -> None:
        """Retry failed batch with smaller batch sizes using binary search.

        Args:
            items: List of items to process
            single_item_fn: Function to process a single item
        """
        batch_size = len(items) // 2

        if batch_size == 0:
            # Process items one by one
            for item in items:
                try:
                    await single_item_fn(item)
                except Exception as e:
                    logger.error(
                        "single_item_creation_failed",
                        item=item,
                        error=str(e),
                    )
            return

        # Split and retry with smaller batches
        logger.info(
            "retrying_with_smaller_batch",
            original_size=len(items),
            new_batch_size=batch_size,
        )

        for i in range(0, len(items), batch_size):
            batch = items[i : i + batch_size]

            try:
                if "name" in batch[0] and "type" in batch[0]:  # Entity
                    query = """
                    UNWIND $batch AS item
                    CREATE (e:Entity {
                        id: item.id,
                        name: item.name,
                        type: item.type,
                        embedding: item.embedding,
                        confidence_score: item.confidence_score,
                        source_doc_id: item.source_doc_id,
                        created_at: datetime()
                    })
                    """
                else:  # Relationship
                    query = """
                    UNWIND $batch AS item
                    MATCH (e1:Entity {name: item.source_name})
                    MATCH (e2:Entity {name: item.target_name})
                    CREATE (e1)-[r:RELATIONSHIP {
                        id: item.id,
                        type: item.rel_type,
                        confidence: item.confidence,
                        source_doc_id: item.source_doc_id,
                        created_at: datetime()
                    }]->(e2)
                    """

                await self.session.run(query, batch=batch)

            except Exception as e:
                logger.warning(
                    "smaller_batch_failed",
                    batch_size=len(batch),
                    error=str(e),
                )
                # Recursively retry with even smaller batches
                await self._retry_with_smaller_batches(batch, single_item_fn)

    async def _create_single_entity(self, entity: Dict[str, Any]) -> None:
        """Create a single entity (fallback for failed batches).

        Args:
            entity: Entity dictionary
        """
        query = """
        CREATE (e:Entity {
            id: $id,
            name: $name,
            type: $type,
            embedding: $embedding,
            confidence_score: $confidence_score,
            source_doc_id: $source_doc_id,
            created_at: datetime()
        })
        """

        await self.session.run(query, **entity)

    async def _create_single_relationship(self, relationship: Dict[str, Any]) -> None:
        """Create a single relationship (fallback for failed batches).

        Args:
            relationship: Relationship dictionary
        """
        query = """
        MATCH (e1:Entity {name: $source_name})
        MATCH (e2:Entity {name: $target_name})
        CREATE (e1)-[r:RELATIONSHIP {
            id: $id,
            type: $rel_type,
            confidence: $confidence,
            source_doc_id: $source_doc_id,
            created_at: datetime()
        }]->(e2)
        """

        await self.session.run(query, **relationship)
