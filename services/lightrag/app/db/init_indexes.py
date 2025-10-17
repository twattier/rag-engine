"""Neo4j index initialization for entity extraction."""

from __future__ import annotations

import structlog
from neo4j import AsyncDriver

logger = structlog.get_logger(__name__)


async def ensure_neo4j_indexes(driver: AsyncDriver, database: str = "neo4j") -> None:
    """Create Neo4j indexes for Entity nodes if they don't exist.

    Args:
        driver: Neo4j async driver instance
        database: Database name (default: "neo4j")
    """
    logger.info("ensuring_neo4j_indexes", database=database)

    async with driver.session(database=database) as session:
        # Create index on entity name
        await session.run("""
            CREATE INDEX entity_name_idx IF NOT EXISTS
            FOR (e:Entity) ON (e.name)
        """)
        logger.info("neo4j_index_created", index="entity_name_idx")

        # Create index on entity type
        await session.run("""
            CREATE INDEX entity_type_idx IF NOT EXISTS
            FOR (e:Entity) ON (e.type)
        """)
        logger.info("neo4j_index_created", index="entity_type_idx")

        # Create vector index for entity embeddings
        # Note: Vector indexes require Neo4j 5.11+
        try:
            await session.run("""
                CREATE VECTOR INDEX entity_embedding_idx IF NOT EXISTS
                FOR (e:Entity) ON (e.embedding)
                OPTIONS {
                    indexConfig: {
                        `vector.dimensions`: 384,
                        `vector.similarity_function`: 'cosine'
                    }
                }
            """)
            logger.info(
                "neo4j_vector_index_created",
                index="entity_embedding_idx",
                dimensions=384,
            )
        except Exception as e:
            logger.warning(
                "neo4j_vector_index_creation_failed",
                index="entity_embedding_idx",
                error=str(e),
                note="Vector indexes require Neo4j 5.11+ - continuing without vector index",
            )

    logger.info("neo4j_indexes_ensured")
