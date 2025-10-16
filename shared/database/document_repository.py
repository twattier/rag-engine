"""Document repository for Neo4j operations."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

from neo4j import Session
from shared.utils.logging import get_logger

logger = get_logger(__name__)


async def create_indexes(session: Session) -> None:
    """Create Neo4j indexes for document queries.

    Args:
        session: Neo4j session

    Note:
        Creates indexes if they don't exist (idempotent)
    """
    indexes = [
        "CREATE INDEX document_id_index IF NOT EXISTS FOR (d:Document) ON (d.id)",
        "CREATE INDEX document_metadata_index IF NOT EXISTS FOR (d:Document) ON (d.metadata)",
        "CREATE INDEX document_status_index IF NOT EXISTS FOR (d:Document) ON (d.status)",
    ]

    for index_query in indexes:
        session.run(index_query)

    logger.info("neo4j_indexes_created", index_count=len(indexes))


async def store_document(
    session: Session,
    document_id: str,
    filename: str,
    status: str,
    metadata: Dict[str, Any],
    size_bytes: int,
    expected_entity_types: Optional[List[str]],
    parsed_content: Dict[str, Any],
    format: str,
) -> str:
    """Store document and parsed content in Neo4j.

    Args:
        session: Neo4j session
        document_id: UUID of document
        filename: Original filename
        status: Document status ('parsing', 'queued', 'indexed', 'failed')
        metadata: Custom metadata fields
        size_bytes: File size in bytes
        expected_entity_types: Expected entity types for extraction
        parsed_content: Parsed content from RAG-Anything
        format: File format (pdf, docx, etc.)

    Returns:
        Document ID

    Raises:
        Exception: If storage fails
    """
    try:
        # Extract content summary from parsed_content
        content_list = parsed_content.get("content_list", [])

        # Aggregate content by type
        text_blocks = []
        images = []
        tables = []
        equations = []

        for item in content_list:
            if item.get("type") == "text":
                text_blocks.append(item.get("text", ""))
            elif item.get("type") == "image":
                images.append(item)
            elif item.get("type") == "table":
                tables.append(item)
            elif item.get("type") == "equation":
                equations.append(item)

        # Combine text blocks
        combined_text = "\n".join(text_blocks)

        # Get page count from metadata
        page_count = parsed_content.get("metadata", {}).get("pages", len(content_list))

        # Create Document node
        document_query = """
        CREATE (d:Document {
            id: $document_id,
            filename: $filename,
            status: $status,
            metadata: $metadata,
            ingestion_date: datetime(),
            size_bytes: $size_bytes,
            expected_entity_types: $expected_entity_types
        })
        RETURN d.id AS document_id
        """

        doc_params = {
            "document_id": document_id,
            "filename": filename,
            "status": status,
            "metadata": metadata,
            "size_bytes": size_bytes,
            "expected_entity_types": expected_entity_types or [],
        }

        doc_result = session.run(document_query, doc_params)
        doc_record = doc_result.single()

        if not doc_record:
            raise Exception("Failed to create Document node")

        # Create ParsedContent node
        content_query = """
        MATCH (d:Document {id: $document_id})
        CREATE (pc:ParsedContent {
            id: randomUUID(),
            text: $text,
            format: $format,
            tables: $tables,
            images: $images,
            equations: $equations,
            page_count: $page_count
        })
        CREATE (d)-[:HAS_CONTENT]->(pc)
        RETURN pc.id AS content_id
        """

        content_params = {
            "document_id": document_id,
            "text": combined_text,
            "format": format,
            "tables": tables,
            "images": [img.get("image_ref", "") for img in images],
            "equations": [eq.get("latex", "") for eq in equations],
            "page_count": page_count,
        }

        content_result = session.run(content_query, content_params)
        content_record = content_result.single()

        if not content_record:
            raise Exception("Failed to create ParsedContent node")

        logger.info(
            "document_stored_in_neo4j",
            document_id=document_id,
            filename=filename,
            status=status,
            content_id=content_record["content_id"],
        )

        return document_id

    except Exception as e:
        logger.error(
            "document_storage_failed",
            document_id=document_id,
            filename=filename,
            error=str(e),
            error_type=type(e).__name__,
        )
        raise


async def update_document_status(session: Session, document_id: str, status: str) -> None:
    """Update document status.

    Args:
        session: Neo4j session
        document_id: Document UUID
        status: New status
    """
    query = """
    MATCH (d:Document {id: $document_id})
    SET d.status = $status
    RETURN d.id AS document_id
    """

    params = {"document_id": document_id, "status": status}

    result = session.run(query, params)
    record = result.single()

    if not record:
        raise Exception(f"Document not found: {document_id}")

    logger.info(
        "document_status_updated",
        document_id=document_id,
        status=status,
    )


async def get_document(session: Session, document_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve document by ID.

    Args:
        session: Neo4j session
        document_id: Document UUID

    Returns:
        Document dict if found, None otherwise
    """
    query = """
    MATCH (d:Document {id: $document_id})-[:HAS_CONTENT]->(pc:ParsedContent)
    RETURN d, pc
    """

    params = {"document_id": document_id}

    result = session.run(query, params)
    record = result.single()

    if not record:
        return None

    doc_node = dict(record["d"])
    content_node = dict(record["pc"])

    return {
        "document": doc_node,
        "parsed_content": content_node,
    }
