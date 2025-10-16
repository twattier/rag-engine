"""Document ingestion API endpoints."""
from __future__ import annotations

import json
from typing import Annotated, Any, Dict, List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, Response, UploadFile, status

from app.config import settings
from app.dependencies import (
    get_batch_service,
    get_document_service,
    get_lightrag_queue,
    get_metadata_schema,
    get_neo4j_client,
    get_rate_limiter,
    validate_document_metadata,
)
from app.middleware.rate_limiter import InMemoryRateLimiter, add_rate_limit_headers
from app.models.responses import BatchIngestResponse, BatchStatusResponse, DocumentIngestResponse, ErrorResponse
from app.services.batch_service import BatchService
from app.services.document_service import DocumentService
from app.services.metadata_mapper import MetadataMapper
from app.services.queue_service import LightRAGQueue
from shared.database.document_repository import create_indexes, store_document, update_document_status
from shared.models.metadata import MetadataSchema
from shared.utils.logging import get_logger
from shared.utils.neo4j_client import Neo4jClient

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

# Supported file formats
SUPPORTED_FORMATS = ["pdf", "txt", "md", "docx", "pptx", "csv"]


def validate_file_format(filename: str) -> str:
    """Validate file format.

    Args:
        filename: Uploaded filename

    Returns:
        File extension

    Raises:
        HTTPException: If format is unsupported
    """
    if "." not in filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "INVALID_FILENAME",
                    "message": f"Filename must have an extension. Supported formats: {', '.join(SUPPORTED_FORMATS)}",
                }
            },
        )

    ext = filename.split(".")[-1].lower()

    if ext not in SUPPORTED_FORMATS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "UNSUPPORTED_FORMAT",
                    "message": f"File format .{ext} is not supported. Supported formats: {', '.join(SUPPORTED_FORMATS)}",
                }
            },
        )

    return ext


async def validate_file_size(file: UploadFile, max_size_bytes: int) -> int:
    """Validate file size.

    Args:
        file: Uploaded file
        max_size_bytes: Maximum allowed size in bytes

    Returns:
        File size in bytes

    Raises:
        HTTPException: If file is too large
    """
    # Read file to get size
    content = await file.read()
    size_bytes = len(content)

    # Reset file pointer
    await file.seek(0)

    if size_bytes > max_size_bytes:
        max_size_mb = max_size_bytes / (1024 * 1024)
        actual_size_mb = size_bytes / (1024 * 1024)

        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={
                "error": {
                    "code": "FILE_TOO_LARGE",
                    "message": f"File size exceeds maximum limit of {max_size_mb:.0f}MB. Uploaded file size: {actual_size_mb:.1f}MB",
                }
            },
        )

    return size_bytes


@router.post(
    "/ingest",
    response_model=DocumentIngestResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        202: {"description": "Document accepted for ingestion"},
        400: {"model": ErrorResponse, "description": "Invalid request (unsupported format)"},
        401: {"model": ErrorResponse, "description": "Missing or invalid API key"},
        413: {"model": ErrorResponse, "description": "File too large"},
        422: {"model": ErrorResponse, "description": "Invalid metadata"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
    },
    summary="Ingest document with metadata",
    description="""
    Upload a document for ingestion with optional custom metadata.

    **Supported Formats:** PDF, TXT, MD, DOCX, PPTX, CSV

    **Rate Limit:** 10 requests per minute per API key

    **Max File Size:** 50MB (configurable)

    **Process:**
    1. Validate file size and format
    2. Validate metadata against schema
    3. Parse document using RAG-Anything
    4. Store in Neo4j
    5. Queue for LightRAG processing (Epic 3)
    """,
)
async def ingest_document(
    request: Request,
    response: Response,
    file: Annotated[UploadFile, File(description="Document file to ingest")],
    metadata: Annotated[Optional[str], Form(description="JSON string of custom metadata fields")] = None,
    expected_entity_types: Annotated[
        Optional[str], Form(description="JSON array of expected entity types for extraction")
    ] = None,
    rate_limiter: InMemoryRateLimiter = Depends(get_rate_limiter),
    doc_service: DocumentService = Depends(get_document_service),
    lightrag_queue: LightRAGQueue = Depends(get_lightrag_queue),
    neo4j_client: Neo4jClient = Depends(get_neo4j_client),
) -> DocumentIngestResponse:
    """Ingest document with custom metadata.

    Args:
        request: FastAPI request
        response: FastAPI response
        file: Uploaded file
        metadata: JSON string of metadata fields
        expected_entity_types: JSON array of entity types
        rate_limiter: Rate limiter instance
        doc_service: Document service instance
        lightrag_queue: LightRAG queue instance
        neo4j_client: Neo4j client instance

    Returns:
        DocumentIngestResponse with document_id and status
    """
    # Check rate limit
    await rate_limiter.check_rate_limit(request)

    # Validate file format
    file_ext = validate_file_format(file.filename)

    # Validate file size
    max_size_bytes = settings.get_max_file_size_bytes()
    size_bytes = await validate_file_size(file, max_size_bytes)

    # Parse metadata JSON
    metadata_dict: Dict[str, Any] = {}
    if metadata:
        try:
            metadata_dict = json.loads(metadata)
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": {
                        "code": "INVALID_JSON",
                        "message": f"Invalid metadata JSON: {str(e)}",
                    }
                },
            )

    # Validate metadata against schema
    validated_metadata = await validate_document_metadata(metadata_dict)

    # Parse expected_entity_types JSON
    entity_types_list: Optional[List[str]] = None
    if expected_entity_types:
        try:
            entity_types_list = json.loads(expected_entity_types)
            if not isinstance(entity_types_list, list):
                raise ValueError("expected_entity_types must be a JSON array")
        except (json.JSONDecodeError, ValueError) as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": {
                        "code": "INVALID_JSON",
                        "message": f"Invalid expected_entity_types JSON: {str(e)}",
                    }
                },
            )

    try:
        # Ingest document (parse with RAG-Anything)
        ingestion_result = await doc_service.ingest_document(
            file=file,
            metadata=validated_metadata,
            expected_entity_types=entity_types_list,
        )

        # Store in Neo4j
        with neo4j_client.session() as session:
            # Create indexes if not exist
            await create_indexes(session)

            # Store document
            await store_document(
                session=session,
                document_id=ingestion_result["document_id"],
                filename=ingestion_result["filename"],
                status=ingestion_result["ingestion_status"],
                metadata=validated_metadata,
                size_bytes=size_bytes,
                expected_entity_types=entity_types_list,
                parsed_content=ingestion_result["parsed_content"],
                format=ingestion_result["format"],
            )

            # Update status to queued
            await update_document_status(
                session=session,
                document_id=ingestion_result["document_id"],
                status="queued",
            )

        # Queue for LightRAG processing
        await lightrag_queue.enqueue(
            doc_id=ingestion_result["document_id"],
            parsed_content=ingestion_result["parsed_content"],
            metadata=validated_metadata,
        )

        # Calculate parsed content summary
        parsed_content_summary = doc_service.calculate_parsed_content_summary(ingestion_result["parsed_content"])

        # Build response
        response_data = DocumentIngestResponse(
            documentId=ingestion_result["document_id"],
            filename=ingestion_result["filename"],
            ingestionStatus="queued",
            metadata=validated_metadata,
            sizeBytes=size_bytes,
            ingestionDate=ingestion_result["ingestion_date"],
            expectedEntityTypes=entity_types_list,
            parsedContentSummary=parsed_content_summary,
        )

        # Add rate limit headers
        add_rate_limit_headers(response, request)

        logger.info(
            "document_ingestion_completed",
            document_id=ingestion_result["document_id"],
            filename=ingestion_result["filename"],
            status="queued",
        )

        return response_data

    except HTTPException:
        # Re-raise HTTP exceptions
        raise

    except Exception as e:
        logger.error(
            "document_ingestion_error",
            filename=file.filename,
            error=str(e),
            error_type=type(e).__name__,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "INGESTION_FAILED",
                    "message": f"Document ingestion failed: {str(e)}",
                }
            },
        )


@router.post(
    "/ingest/batch",
    response_model=BatchIngestResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        202: {"description": "Batch ingestion started"},
        400: {"model": ErrorResponse, "description": "Invalid request (batch too large)"},
        401: {"model": ErrorResponse, "description": "Missing or invalid API key"},
        422: {"model": ErrorResponse, "description": "Invalid metadata mapping"},
        429: {"model": ErrorResponse, "description": "Rate limit exceeded"},
    },
    summary="Batch ingest documents",
    description="""
    Upload multiple documents in a single batch operation.

    **Batch Limit:** Maximum 100 files per batch

    **Metadata Mapping:** Optional CSV or JSON file mapping filenames to metadata

    **Process:**
    1. Validates batch size (max 100 files)
    2. Parses optional metadata mapping file
    3. Starts background batch processing
    4. Returns batch_id immediately for status tracking
    """,
)
async def batch_ingest_documents(
    request: Request,
    response: Response,
    files: Annotated[List[UploadFile], File(description="List of document files to ingest")],
    metadata_mapping: Annotated[Optional[UploadFile], File(description="CSV or JSON metadata mapping")] = None,
    rate_limiter: InMemoryRateLimiter = Depends(get_rate_limiter),
    batch_service: BatchService = Depends(get_batch_service),
) -> BatchIngestResponse:
    """Batch ingest documents.

    Args:
        request: FastAPI request
        response: FastAPI response
        files: List of uploaded files
        metadata_mapping: Optional metadata mapping file (CSV or JSON)
        rate_limiter: Rate limiter instance
        batch_service: Batch service instance

    Returns:
        BatchIngestResponse with batch_id
    """
    # Check rate limit
    await rate_limiter.check_rate_limit(request)

    # Validate batch size (max 100 files)
    MAX_BATCH_SIZE = 100
    if len(files) > MAX_BATCH_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "BATCH_TOO_LARGE",
                    "message": f"Batch exceeds maximum size of {MAX_BATCH_SIZE} files. Uploaded: {len(files)} files",
                }
            },
        )

    # Parse metadata mapping if provided
    metadata_map: Dict[str, Dict[str, Any]] = {}
    if metadata_mapping:
        try:
            metadata_map = await MetadataMapper.parse_metadata_mapping(metadata_mapping)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "error": {
                        "code": "INVALID_METADATA_MAPPING",
                        "message": str(e),
                    }
                },
            )

    try:
        # Start batch processing
        batch_id = await batch_service.start_batch(
            files=files,
            metadata_mapping=metadata_map,
        )

        # Build response
        response_data = BatchIngestResponse(
            batch_id=str(batch_id),
            total_documents=len(files),
            status="in_progress",
            message="Batch ingestion started. Use batch_id to check status",
        )

        # Add rate limit headers
        add_rate_limit_headers(response, request)

        return response_data

    except Exception as e:
        logger.error(
            "batch_ingestion_error",
            error=str(e),
            error_type=type(e).__name__,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "BATCH_INGESTION_FAILED",
                    "message": f"Batch ingestion failed: {str(e)}",
                }
            },
        )


@router.get(
    "/ingest/batch/{batch_id}/status",
    response_model=BatchStatusResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Batch status retrieved"},
        404: {"model": ErrorResponse, "description": "Batch not found"},
    },
    summary="Get batch ingestion status",
    description="""
    Get the current status of a batch ingestion operation.

    **Status Values:**
    - `in_progress`: Batch is currently being processed
    - `completed`: All documents processed successfully
    - `partial_failure`: Some documents failed, but at least one succeeded
    - `failed`: All documents failed
    """,
)
async def get_batch_status(
    batch_id: str,
    batch_service: BatchService = Depends(get_batch_service),
) -> BatchStatusResponse:
    """Get batch ingestion status.

    Args:
        batch_id: Batch UUID
        batch_service: Batch service instance

    Returns:
        BatchStatusResponse with current status
    """
    try:
        from uuid import UUID

        # Convert string to UUID
        batch_uuid = UUID(batch_id)

        # Get batch status
        batch_status = batch_service.get_batch_status(batch_uuid)

        # Build response
        return BatchStatusResponse(
            batch_id=str(batch_status.batch_id),
            total_documents=batch_status.total_documents,
            processed_count=batch_status.processed_count,
            failed_count=batch_status.failed_count,
            status=batch_status.status,
            failed_documents=[
                {"filename": doc["filename"], "error": doc["error"]}
                for doc in batch_status.failed_documents
            ],
            completed_at=batch_status.completed_at,
            processing_time_seconds=batch_status.processing_time_seconds,
        )

    except ValueError as e:
        # Batch not found or invalid UUID
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "BATCH_NOT_FOUND",
                    "message": str(e),
                }
            },
        )

    except Exception as e:
        logger.error(
            "batch_status_error",
            batch_id=batch_id,
            error=str(e),
            error_type=type(e).__name__,
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": {
                    "code": "BATCH_STATUS_FAILED",
                    "message": f"Failed to retrieve batch status: {str(e)}",
                }
            },
        )
