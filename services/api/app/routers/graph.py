"""Graph statistics endpoints."""

from __future__ import annotations

from typing import Dict

import structlog
from fastapi import APIRouter, Depends, status
from neo4j import AsyncDriver

from ..dependencies import get_neo4j_driver, get_settings
from ..config import Settings
from ..models.responses import GraphStatsResponse

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/api/v1/graph", tags=["graph"])


@router.get(
    "/stats",
    response_model=GraphStatsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get graph statistics",
    description="Retrieve comprehensive statistics about the knowledge graph including entity counts, relationship counts, and type distributions.",
)
async def get_graph_stats(
    driver: AsyncDriver = Depends(get_neo4j_driver),
    settings: Settings = Depends(get_settings),
) -> GraphStatsResponse:
    """Get knowledge graph statistics.

    Returns:
        GraphStatsResponse with statistics about entities, relationships, and their distributions.
    """
    logger.info("get_graph_stats_requested")

    async with driver.session(database=settings.neo4j_database) as session:
        # Get total entities
        total_entities_result = await session.run("MATCH (e:Entity) RETURN count(e) as count")
        total_entities_record = await total_entities_result.single()
        total_entities = total_entities_record["count"] if total_entities_record else 0

        # Get total relationships
        total_relationships_result = await session.run(
            "MATCH ()-[r:RELATIONSHIP]->() RETURN count(r) as count"
        )
        total_relationships_record = await total_relationships_result.single()
        total_relationships = total_relationships_record["count"] if total_relationships_record else 0

        # Get entity type distribution
        entity_type_result = await session.run(
            "MATCH (e:Entity) RETURN e.type as type, count(e) as count ORDER BY count DESC"
        )
        entity_type_records = await entity_type_result.data()
        entity_type_distribution: Dict[str, int] = {
            record["type"]: record["count"] for record in entity_type_records
        }

        # Get relationship type distribution
        rel_type_result = await session.run(
            "MATCH ()-[r:RELATIONSHIP]->() RETURN r.type as type, count(r) as count ORDER BY count DESC"
        )
        rel_type_records = await rel_type_result.data()
        relationship_type_distribution: Dict[str, int] = {
            record["type"]: record["count"] for record in rel_type_records
        }

        # Get total documents
        total_documents_result = await session.run("MATCH (d:Document) RETURN count(d) as count")
        total_documents_record = await total_documents_result.single()
        total_documents = total_documents_record["count"] if total_documents_record else 0

        # Get cross-document entities (entities appearing in >1 document)
        cross_doc_result = await session.run("""
            MATCH (e:Entity)-[:APPEARS_IN]->(d:Document)
            WITH e, count(d) as doc_count
            WHERE doc_count > 1
            RETURN count(e) as count
        """)
        cross_doc_record = await cross_doc_result.single()
        cross_document_entities = cross_doc_record["count"] if cross_doc_record else 0

    logger.info(
        "get_graph_stats_completed",
        total_entities=total_entities,
        total_relationships=total_relationships,
        total_documents=total_documents,
        cross_document_entities=cross_document_entities,
    )

    return GraphStatsResponse(
        total_entities=total_entities,
        total_relationships=total_relationships,
        entity_type_distribution=entity_type_distribution,
        relationship_type_distribution=relationship_type_distribution,
        total_documents=total_documents,
        cross_document_entities=cross_document_entities,
    )
