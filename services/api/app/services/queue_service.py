"""LightRAG queue service for document processing."""
from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional
from uuid import UUID

from shared.utils.logging import get_logger

logger = get_logger(__name__)


class LightRAGQueue:
    """In-memory queue for LightRAG document processing (MVP)."""

    def __init__(self):
        """Initialize queue."""
        self.queue: asyncio.Queue = asyncio.Queue()
        self.processing: Dict[str, str] = {}  # doc_id -> status

    async def enqueue(self, doc_id: str, parsed_content: Dict[str, Any], metadata: Dict[str, Any]) -> None:
        """Add document to LightRAG processing queue.

        Args:
            doc_id: Document UUID
            parsed_content: Parsed content from RAG-Anything
            metadata: Document metadata

        Note:
            Processing worker will be implemented in Epic 3
        """
        await self.queue.put({"doc_id": doc_id, "parsed_content": parsed_content, "metadata": metadata})

        self.processing[doc_id] = "queued"

        logger.info(
            "document_queued_for_lightrag",
            doc_id=doc_id,
            queue_size=self.queue.qsize(),
        )

    async def get_status(self, doc_id: str) -> Optional[str]:
        """Get processing status for document.

        Args:
            doc_id: Document UUID

        Returns:
            Status string if found, None otherwise
        """
        return self.processing.get(doc_id)

    def get_queue_size(self) -> int:
        """Get current queue size.

        Returns:
            Number of documents in queue
        """
        return self.queue.qsize()

    # Note: Processing worker will be implemented in Epic 3
    # async def process_documents(self):
    #     """Background worker to process queued documents."""
    #     pass
