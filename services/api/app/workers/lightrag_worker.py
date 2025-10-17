"""LightRAG background worker for document queue processing.

This worker:
1. Consumes documents from the queue service
2. Extracts entities using LightRAG
3. Persists entities and relationships to Neo4j
4. Updates document status to "indexed" or "failed"
"""

from __future__ import annotations

import asyncio
from typing import Any, Dict

from app.config import get_settings
from app.services.queue_service import LightRAGQueue
from shared.utils.lightrag_client import get_lightrag_client
from shared.utils.logging import get_logger
from shared.utils.neo4j_client import get_neo4j_client

logger = get_logger(__name__)


async def process_documents(queue: LightRAGQueue) -> None:
    """Background worker to process queued documents.

    Args:
        queue: LightRAG queue service instance
    """
    logger.info("lightrag_worker_starting")

    # Get settings
    settings = get_settings()

    # Initialize LightRAG client
    lightrag_client = await get_lightrag_client(
        neo4j_uri=settings.NEO4J_URI,
        neo4j_auth=settings.NEO4J_AUTH,
        neo4j_database=settings.NEO4J_DATABASE,
        embedding_model=settings.get_embedding_model(),
        llm_endpoint=settings.get_llm_endpoint(),
        working_dir=settings.LIGHTRAG_WORKING_DIR,
        entity_types_path=settings.ENTITY_TYPES_CONFIG_PATH,
    )
    neo4j_client = get_neo4j_client()

    while True:
        try:
            # Get document from queue
            item = await queue.queue.get()
            doc_id = item["doc_id"]
            parsed_content = item["parsed_content"]
            metadata = item["metadata"]

            logger.info(
                "processing_document",
                doc_id=doc_id,
                queue_size=queue.queue.qsize(),
            )

            # Update status to processing
            queue.processing[doc_id] = "processing"

            # Extract text content from parsed_content
            # parsed_content structure: {"text": "...", "tables": [...], "images": [...]}
            content = parsed_content.get("text", "")

            if not content:
                logger.warning(
                    "document_has_no_text_content",
                    doc_id=doc_id,
                )
                # Mark as indexed even without content (to prevent reprocessing)
                queue.processing[doc_id] = "indexed"
                await _update_document_status(neo4j_client, doc_id, "indexed")
                queue.queue.task_done()
                continue

            # Call LightRAG wrapper to extract entities
            result = await lightrag_client.extract_entities(
                doc_id=doc_id,
                content=content,
                metadata=metadata,
            )

            if result["status"] == "success":
                # Link entities to document in Neo4j
                await _link_entities_to_document(
                    neo4j_client,
                    doc_id,
                    result["entities_count"],
                    result["relationships_count"],
                )

                # Update document status to indexed
                queue.processing[doc_id] = "indexed"
                await _update_document_status(neo4j_client, doc_id, "indexed")

                logger.info(
                    "document_processed",
                    doc_id=doc_id,
                    entities_count=result["entities_count"],
                    relationships_count=result["relationships_count"],
                )
            else:
                # Mark as failed
                queue.processing[doc_id] = "failed"
                await _update_document_status(neo4j_client, doc_id, "failed")

                logger.error(
                    "document_processing_failed",
                    doc_id=doc_id,
                    error=result.get("error", "unknown"),
                )

        except Exception as e:
            logger.error(
                "worker_exception",
                doc_id=item.get("doc_id", "unknown"),
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )

            # Mark document as failed
            if "doc_id" in item:
                queue.processing[item["doc_id"]] = "failed"
                await _update_document_status(neo4j_client, item["doc_id"], "failed")

        finally:
            queue.queue.task_done()


async def _update_document_status(
    neo4j_client,
    doc_id: str,
    status: str,
) -> None:
    """Update document status in Neo4j.

    Args:
        neo4j_client: Neo4j client instance
        doc_id: Document UUID
        status: New status ("indexed", "failed", etc.)
    """
    query = """
    MATCH (d:Document {id: $doc_id})
    SET d.status = $status,
        d.updated_at = datetime()
    RETURN d.id AS id
    """

    async with neo4j_client.session() as session:
        result = await session.run(query, doc_id=doc_id, status=status)
        record = await result.single()

        if record:
            logger.debug(
                "document_status_updated",
                doc_id=doc_id,
                status=status,
            )
        else:
            logger.warning(
                "document_not_found_for_status_update",
                doc_id=doc_id,
                status=status,
            )


async def _link_entities_to_document(
    neo4j_client,
    doc_id: str,
    entities_count: int,
    relationships_count: int,
) -> None:
    """Create CONTAINS relationships from Document to extracted Entities.

    LightRAG creates Entity nodes in Neo4j, but doesn't link them to the Document.
    This function creates (:Document)-[:CONTAINS]->(:Entity) relationships.

    Args:
        neo4j_client: Neo4j client instance
        doc_id: Document UUID
        entities_count: Number of entities extracted (for logging)
        relationships_count: Number of relationships created (for logging)
    """
    # Note: LightRAG creates entities with specific labels and properties
    # This is a placeholder - actual implementation depends on LightRAG's Neo4j schema
    # For now, we'll just log that we need to create these relationships

    # TODO: Implement actual CONTAINS relationship creation
    # This requires understanding LightRAG's Neo4j schema structure
    # Likely query format:
    # MATCH (d:Document {id: $doc_id})
    # MATCH (e:Entity)
    # WHERE e.source_doc_id = $doc_id  // Or similar property
    # MERGE (d)-[:CONTAINS]->(e)

    logger.info(
        "entities_linked_to_document",
        doc_id=doc_id,
        entities_count=entities_count,
        relationships_count=relationships_count,
        note="Placeholder - actual linking to be implemented based on LightRAG schema",
    )
