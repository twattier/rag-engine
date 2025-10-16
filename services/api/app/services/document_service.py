"""Document ingestion service with RAG-Anything orchestration."""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4

import httpx
from fastapi import UploadFile

from app.config import Settings
from shared.utils.logging import get_logger

logger = get_logger(__name__)


class DocumentService:
    """Service for document ingestion orchestration."""

    def __init__(self, settings: Settings, rag_anything_url: str):
        """Initialize document service.

        Args:
            settings: Application settings
            rag_anything_url: RAG-Anything service URL
        """
        self.settings = settings
        self.rag_anything_url = rag_anything_url
        self.http_client = httpx.AsyncClient(timeout=300.0)  # 5 min timeout for large files

    async def close(self):
        """Close HTTP client."""
        await self.http_client.aclose()

    async def parse_document(self, file: UploadFile) -> Dict[str, Any]:
        """Parse document using RAG-Anything service.

        Args:
            file: Uploaded file

        Returns:
            Parsed content dictionary

        Raises:
            httpx.HTTPError: If RAG-Anything service fails
            Exception: If parsing fails
        """
        try:
            # Read file content
            file_content = await file.read()
            await file.seek(0)  # Reset for potential re-reading

            # Prepare multipart/form-data request
            files = {"file": (file.filename, file_content, file.content_type)}

            # Call RAG-Anything /parse endpoint
            response = await self.http_client.post(f"{self.rag_anything_url}/parse", files=files)

            response.raise_for_status()

            parsed_data = response.json()

            logger.info(
                "document_parsed_successfully",
                filename=file.filename,
                content_items=len(parsed_data.get("content_list", [])),
            )

            return parsed_data

        except httpx.HTTPError as e:
            logger.error(
                "rag_anything_parsing_failed",
                filename=file.filename,
                error=str(e),
                status_code=getattr(e.response, "status_code", None) if hasattr(e, "response") else None,
            )
            raise Exception(f"Document parsing failed: {str(e)}")

        except Exception as e:
            logger.error(
                "document_parsing_error",
                filename=file.filename,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise

    async def ingest_document(
        self,
        file: UploadFile,
        metadata: Optional[Dict[str, Any]],
        expected_entity_types: Optional[List[str]],
    ) -> Dict[str, Any]:
        """Ingest document with metadata.

        Args:
            file: Uploaded file
            metadata: Custom metadata fields
            expected_entity_types: Expected entity types for extraction

        Returns:
            Ingestion result with document_id and status

        Raises:
            Exception: If ingestion fails
        """
        document_id = str(uuid4())

        try:
            # Get file size
            file_content = await file.read()
            size_bytes = len(file_content)
            await file.seek(0)  # Reset file pointer

            # Extract file format from filename
            file_format = file.filename.split(".")[-1].lower() if "." in file.filename else "unknown"

            # Parse document using RAG-Anything
            parsed_content = await self.parse_document(file)

            # Prepare ingestion result
            result = {
                "document_id": document_id,
                "filename": file.filename,
                "ingestion_status": "parsing",
                "metadata": metadata or {},
                "size_bytes": size_bytes,
                "ingestion_date": datetime.utcnow().isoformat() + "Z",
                "expected_entity_types": expected_entity_types,
                "parsed_content": parsed_content,
                "format": file_format,
            }

            logger.info(
                "document_ingestion_initiated",
                document_id=document_id,
                filename=file.filename,
                size_bytes=size_bytes,
                format=file_format,
            )

            return result

        except Exception as e:
            logger.error(
                "document_ingestion_failed",
                document_id=document_id,
                filename=file.filename,
                error=str(e),
                error_type=type(e).__name__,
            )
            raise

    def calculate_parsed_content_summary(self, parsed_content: Dict[str, Any]) -> Dict[str, int]:
        """Calculate summary of parsed content.

        Args:
            parsed_content: Parsed content from RAG-Anything

        Returns:
            Summary dict with counts by type
        """
        content_list = parsed_content.get("content_list", [])

        summary = {"text_blocks": 0, "images": 0, "tables": 0, "equations": 0}

        for item in content_list:
            item_type = item.get("type", "")
            if item_type == "text":
                summary["text_blocks"] += 1
            elif item_type == "image":
                summary["images"] += 1
            elif item_type == "table":
                summary["tables"] += 1
            elif item_type == "equation":
                summary["equations"] += 1

        return summary
