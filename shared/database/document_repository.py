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
        "CREATE INDEX document_status_index IF NOT EXISTS FOR (d:Document) ON (d.status)",
        "CREATE INDEX document_ingestion_date_index IF NOT EXISTS FOR (d:Document) ON (d.ingestion_date)",
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

        # Create Document node with flattened metadata
        # Note: Neo4j requires metadata fields as individual properties
        # Store as JSON string for complex nested structures
        import json

        document_query = """
        CREATE (d:Document {
            id: $document_id,
            filename: $filename,
            status: $status,
            metadata_json: $metadata_json,
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
            "metadata_json": json.dumps(metadata),
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


async def list_documents(
    session: Session,
    filters: Dict[str, Any],
    limit: int = 50,
    offset: int = 0,
) -> List[Dict[str, Any]]:
    """List documents with filtering and pagination.

    Args:
        session: Neo4j session
        filters: Filter criteria (status, ingestion_date_from, ingestion_date_to, metadata fields)
        limit: Number of documents to return (default: 50, max: 500)
        offset: Pagination offset (default: 0)

    Returns:
        List of document dictionaries
    """
    import json

    # Build WHERE clause dynamically for metadata filters
    where_clauses = []
    params = {"limit": limit, "offset": offset}

    # Status filter
    if filters.get("status"):
        where_clauses.append("d.status = $status")
        params["status"] = filters["status"]

    # Date range filters
    if filters.get("ingestion_date_from"):
        where_clauses.append("d.ingestion_date >= datetime($ingestion_date_from)")
        params["ingestion_date_from"] = filters["ingestion_date_from"]

    if filters.get("ingestion_date_to"):
        where_clauses.append("d.ingestion_date <= datetime($ingestion_date_to)")
        params["ingestion_date_to"] = filters["ingestion_date_to"]

    # Metadata field filters (dynamic)
    # Note: Metadata filtering not supported when stored as JSON string
    # This would require JSON parsing in Cypher (APOC) or post-filtering in Python
    metadata_filters = {k: v for k, v in filters.items() if k not in ["status", "ingestion_date_from", "ingestion_date_to"]}
    if metadata_filters:
        logger.warning(
            "metadata_filtering_not_supported",
            message="Metadata field filtering requires APOC or post-processing"
        )

    # Construct WHERE clause
    where_clause = " AND ".join(where_clauses) if where_clauses else "true"

    query = f"""
    MATCH (d:Document)
    WHERE {where_clause}
    RETURN d.id AS document_id,
           d.filename AS filename,
           d.metadata_json AS metadata_json,
           d.ingestion_date AS ingestion_date,
           d.status AS status,
           d.size_bytes AS size_bytes
    ORDER BY d.ingestion_date DESC
    SKIP $offset
    LIMIT $limit
    """

    result = session.run(query, params)
    documents = []
    for record in result:
        doc = dict(record)
        # Parse metadata JSON string back to dict
        try:
            doc["metadata"] = json.loads(doc["metadata_json"]) if doc.get("metadata_json") else {}
        except (json.JSONDecodeError, TypeError):
            doc["metadata"] = {}
        doc.pop("metadata_json", None)
        documents.append(doc)

    logger.info(
        "documents_listed",
        count=len(documents),
        filters=filters,
        limit=limit,
        offset=offset,
    )

    return documents


async def count_documents(session: Session, filters: Dict[str, Any]) -> int:
    """Count documents matching filters.

    Args:
        session: Neo4j session
        filters: Filter criteria (status, ingestion_date_from, ingestion_date_to, metadata fields)

    Returns:
        Total count of matching documents
    """
    # Build WHERE clause dynamically for metadata filters
    where_clauses = []
    params = {}

    # Status filter
    if filters.get("status"):
        where_clauses.append("d.status = $status")
        params["status"] = filters["status"]

    # Date range filters
    if filters.get("ingestion_date_from"):
        where_clauses.append("d.ingestion_date >= datetime($ingestion_date_from)")
        params["ingestion_date_from"] = filters["ingestion_date_from"]

    if filters.get("ingestion_date_to"):
        where_clauses.append("d.ingestion_date <= datetime($ingestion_date_to)")
        params["ingestion_date_to"] = filters["ingestion_date_to"]

    # Metadata field filters (dynamic)
    # Note: Metadata filtering not supported when stored as JSON string
    metadata_filters = {k: v for k, v in filters.items() if k not in ["status", "ingestion_date_from", "ingestion_date_to"]}
    if metadata_filters:
        logger.warning(
            "metadata_filtering_not_supported",
            message="Metadata field filtering requires APOC or post-processing"
        )

    # Construct WHERE clause
    where_clause = " AND ".join(where_clauses) if where_clauses else "true"

    query = f"""
    MATCH (d:Document)
    WHERE {where_clause}
    RETURN count(d) AS total_count
    """

    result = session.run(query, params)
    record = result.single()

    total_count = record["total_count"] if record else 0

    logger.info("documents_counted", total_count=total_count, filters=filters)

    return total_count


async def get_document_by_id(session: Session, document_id: str) -> Optional[Dict[str, Any]]:
    """Get document details by ID with parsed content.

    Args:
        session: Neo4j session
        document_id: Document UUID

    Returns:
        Document details with parsed content, or None if not found
    """
    import json

    query = """
    MATCH (d:Document {id: $document_id})
    OPTIONAL MATCH (d)-[:HAS_CONTENT]->(pc:ParsedContent)
    RETURN d.id AS document_id,
           d.filename AS filename,
           d.metadata_json AS metadata_json,
           d.ingestion_date AS ingestion_date,
           d.status AS status,
           d.size_bytes AS size_bytes,
           pc.format AS format,
           pc.text AS text,
           pc.tables AS tables,
           pc.images AS images,
           pc.page_count AS page_count
    """

    params = {"document_id": document_id}

    result = session.run(query, params)
    record = result.single()

    if not record:
        logger.info("document_not_found", document_id=document_id)
        return None

    # Build parsed content preview (first 500 characters)
    text = record["text"] if record["text"] else ""
    preview = text[:500] if text else ""

    # Parse metadata JSON
    try:
        metadata = json.loads(record["metadata_json"]) if record.get("metadata_json") else {}
    except (json.JSONDecodeError, TypeError):
        metadata = {}

    document_detail = {
        "document_id": record["document_id"],
        "filename": record["filename"],
        "metadata": metadata,
        "ingestion_date": record["ingestion_date"],
        "status": record["status"],
        "size_bytes": record["size_bytes"],
        "parsed_content": {
            "format": record["format"],
            "page_count": record["page_count"],
            "text_blocks": len(text.split("\n")) if text else 0,
            "images": len(record["images"]) if record["images"] else 0,
            "tables": len(record["tables"]) if record["tables"] else 0,
            "preview": preview,
        } if record["format"] else None,
    }

    logger.info("document_retrieved", document_id=document_id)

    return document_detail


async def delete_document(session: Session, document_id: str) -> None:
    """Delete document and associated content (idempotent).

    Args:
        session: Neo4j session
        document_id: Document UUID

    Note:
        This operation is idempotent - deleting a non-existent document succeeds silently.
    """
    query = """
    MATCH (d:Document {id: $document_id})
    OPTIONAL MATCH (d)-[:HAS_CONTENT]->(pc:ParsedContent)
    DETACH DELETE d, pc
    """

    params = {"document_id": document_id}

    session.run(query, params)

    logger.info("document_deleted", document_id=document_id)


async def update_document_metadata(
    session: Session,
    document_id: str,
    metadata: Dict[str, Any],
) -> None:
    """Update document metadata fields.

    Args:
        session: Neo4j session
        document_id: Document UUID
        metadata: New metadata dictionary to replace existing metadata

    Raises:
        Exception: If document not found
    """
    import json

    query = """
    MATCH (d:Document {id: $document_id})
    SET d.metadata_json = $metadata_json
    RETURN d.id AS document_id
    """

    params = {
        "document_id": document_id,
        "metadata_json": json.dumps(metadata),
    }

    result = session.run(query, params)
    record = result.single()

    if not record:
        raise Exception(f"Document not found: {document_id}")

    logger.info(
        "document_metadata_updated",
        document_id=document_id,
        metadata_keys=list(metadata.keys()),
    )
