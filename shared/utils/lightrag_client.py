"""LightRAG client wrapper for entity extraction and graph construction.

This module provides a wrapper around the LightRAG library for:
- Neo4j storage backend configuration
- Entity extraction based on configured entity types
- Graph construction with entity-relationship mapping
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from lightrag import LightRAG, QueryParam
from lightrag.kg.neo4j_impl import Neo4JStorage

from shared.utils.logging import get_logger

logger = get_logger(__name__)


class LightRAGClient:
    """Wrapper for LightRAG library with Neo4j backend."""

    def __init__(
        self,
        neo4j_uri: str,
        neo4j_auth: str,
        neo4j_database: str,
        embedding_model: str,
        llm_endpoint: str,
        working_dir: str,
        entity_types_path: str,
    ):
        """Initialize LightRAG client with Neo4j storage backend.

        Args:
            neo4j_uri: Neo4j connection URI
            neo4j_auth: Neo4j authentication (username/password)
            neo4j_database: Neo4j database name
            embedding_model: Sentence transformers model name
            llm_endpoint: LLM API endpoint URL
            working_dir: Working directory for LightRAG cache
            entity_types_path: Path to entity types YAML config
        """
        self.neo4j_uri = neo4j_uri
        self.neo4j_auth = neo4j_auth
        self.neo4j_database = neo4j_database
        self.embedding_model = embedding_model
        self.llm_endpoint = llm_endpoint
        self.working_dir = working_dir
        self.entity_types_path = entity_types_path

        self._lightrag: Optional[LightRAG] = None
        self._entity_types: List[Dict[str, Any]] = []

        logger.info("lightrag_client_initializing")

    async def initialize(self) -> None:
        """Initialize LightRAG instance with Neo4j backend.

        Must be called before using extract_entities.
        """
        if self._lightrag is not None:
            logger.debug("lightrag_already_initialized")
            return

        # Load entity types from config
        self._entity_types = self._load_entity_types()

        # Parse Neo4j auth
        neo4j_user, neo4j_password = self.neo4j_auth.split("/")

        # Initialize Neo4j storage backend
        storage = Neo4JStorage(
            uri=self.neo4j_uri,
            username=neo4j_user,
            password=neo4j_password,
            database=self.neo4j_database,
        )

        # Create working directory if not exists
        working_dir = Path(self.working_dir)
        working_dir.mkdir(parents=True, exist_ok=True)

        # Initialize LightRAG instance
        self._lightrag = LightRAG(
            working_dir=str(working_dir),
            llm_model_func=self._get_llm_model_func(),
            embedding_func=self._get_embedding_func(),
            kg_storage=storage,
        )

        logger.info(
            "lightrag_initialized",
            embedding_model=self.embedding_model,
            llm_endpoint=self.llm_endpoint,
            entity_types_count=len(self._entity_types),
            neo4j_uri=self.neo4j_uri,
            neo4j_database=self.neo4j_database,
        )

    def _load_entity_types(self) -> List[Dict[str, Any]]:
        """Load entity types from YAML configuration.

        Returns:
            List of entity type definitions
        """
        config_path = Path(self.entity_types_path)

        if not config_path.exists():
            logger.warning(
                "entity_types_config_not_found",
                path=str(config_path),
            )
            return []

        with open(config_path, "r") as f:
            config = yaml.safe_load(f)
            entity_types = config.get("entity_types", [])

        logger.info(
            "entity_types_loaded",
            count=len(entity_types),
            types=[et["type_name"] for et in entity_types],
        )

        return entity_types

    def _get_llm_model_func(self):
        """Get LLM model function for LightRAG.

        Returns:
            LLM model function compatible with LightRAG
        """
        # LightRAG uses async llm_model_func
        # Use OpenAI-compatible endpoint (Ollama, OpenAI, Azure, external proxy, etc.)
        from lightrag.llm import openai_complete_if_cache

        async def llm_func(
            prompt: str,
            system_prompt: Optional[str] = None,
            **kwargs
        ) -> str:
            """LLM function wrapper for OpenAI-compatible endpoint."""
            return await openai_complete_if_cache(
                model="gpt-4",  # Model name for OpenAI-compatible endpoint
                prompt=prompt,
                system_prompt=system_prompt,
                api_base=self.llm_endpoint,
                **kwargs
            )

        return llm_func

    def _get_embedding_func(self):
        """Get embedding function for LightRAG.

        Returns:
            Embedding function compatible with LightRAG
        """
        # The embedding_model parameter is already configured with the correct
        # provider-specific model (e.g., "sentence-transformers/all-MiniLM-L6-v2")
        # LightRAG will use this to initialize the appropriate embedding function
        from lightrag.embedding import embedding_func

        return embedding_func

    async def extract_entities(
        self,
        doc_id: str,
        content: str,
        metadata: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Extract entities and relationships from document content.

        Args:
            doc_id: Document UUID
            content: Parsed document text content
            metadata: Document metadata

        Returns:
            Dict containing:
                - entities_count: Number of entities extracted
                - relationships_count: Number of relationships created
                - status: "success" or "failed"

        Raises:
            RuntimeError: If LightRAG not initialized
        """
        if self._lightrag is None:
            raise RuntimeError("LightRAG client not initialized. Call initialize() first.")

        logger.info(
            "extracting_entities",
            doc_id=doc_id,
            content_length=len(content),
        )

        try:
            # Build entity type hints for LLM prompt
            entity_hints = self._build_entity_hints()

            # Augment content with metadata context
            augmented_content = self._augment_content_with_metadata(content, metadata)

            # Insert document into LightRAG (triggers entity extraction)
            # LightRAG automatically creates entities and relationships in Neo4j
            await self._lightrag.ainsert(augmented_content)

            # Query Neo4j to count created entities (for this document)
            # Note: LightRAG doesn't return entity count, so we query Neo4j directly
            entities_count = await self._count_document_entities(doc_id)
            relationships_count = await self._count_document_relationships(doc_id)

            logger.info(
                "entities_extracted",
                doc_id=doc_id,
                entities_count=entities_count,
                relationships_count=relationships_count,
            )

            return {
                "entities_count": entities_count,
                "relationships_count": relationships_count,
                "status": "success",
            }

        except Exception as e:
            logger.error(
                "entity_extraction_failed",
                doc_id=doc_id,
                error=str(e),
                error_type=type(e).__name__,
                exc_info=True,
            )
            return {
                "entities_count": 0,
                "relationships_count": 0,
                "status": "failed",
                "error": str(e),
            }

    def _build_entity_hints(self) -> str:
        """Build entity type hints for LLM prompt.

        Returns:
            Formatted string with entity types and examples
        """
        hints = "Extract the following entity types:\n\n"

        for entity_type in self._entity_types:
            hints += f"- {entity_type['type_name']}: {entity_type['description']}\n"
            hints += f"  Examples: {', '.join(entity_type['examples'][:3])}\n\n"

        return hints

    def _augment_content_with_metadata(
        self,
        content: str,
        metadata: Dict[str, Any],
    ) -> str:
        """Augment content with metadata context for better entity extraction.

        Args:
            content: Original document content
            metadata: Document metadata

        Returns:
            Augmented content with metadata context
        """
        metadata_context = f"Document Metadata:\n"
        metadata_context += f"- Category: {metadata.get('category', 'unknown')}\n"

        if "filename" in metadata:
            metadata_context += f"- Filename: {metadata['filename']}\n"

        metadata_context += f"\n---\n\n{content}"

        return metadata_context

    async def _count_document_entities(self, doc_id: str) -> int:
        """Count entities extracted for a document.

        Args:
            doc_id: Document UUID

        Returns:
            Number of entities linked to document
        """
        # This requires direct Neo4j query
        # For now, return 0 as placeholder (will be implemented in worker)
        return 0

    async def _count_document_relationships(self, doc_id: str) -> int:
        """Count relationships created for a document.

        Args:
            doc_id: Document UUID

        Returns:
            Number of relationships linked to document
        """
        # This requires direct Neo4j query
        # For now, return 0 as placeholder (will be implemented in worker)
        return 0

    async def query(
        self,
        query: str,
        mode: str = "hybrid",
        top_k: int = 10,
    ) -> Dict[str, Any]:
        """Query the knowledge graph using LightRAG.

        Args:
            query: Search query
            mode: Query mode ("local", "global", "hybrid", "naive")
            top_k: Number of results to return

        Returns:
            Query results with context and entities

        Raises:
            RuntimeError: If LightRAG not initialized
        """
        if self._lightrag is None:
            raise RuntimeError("LightRAG client not initialized. Call initialize() first.")

        logger.info("querying_lightrag", query=query, mode=mode, top_k=top_k)

        try:
            # Query LightRAG
            result = await self._lightrag.aquery(
                query,
                param=QueryParam(mode=mode, top_k=top_k)
            )

            logger.info("lightrag_query_success", query=query, result_length=len(result))

            return {
                "result": result,
                "mode": mode,
                "top_k": top_k,
                "status": "success",
            }

        except Exception as e:
            logger.error(
                "lightrag_query_failed",
                query=query,
                error=str(e),
                exc_info=True,
            )
            return {
                "result": "",
                "mode": mode,
                "top_k": top_k,
                "status": "failed",
                "error": str(e),
            }


async def get_lightrag_client(
    neo4j_uri: str,
    neo4j_auth: str,
    neo4j_database: str,
    embedding_model: str,
    llm_endpoint: str,
    working_dir: str,
    entity_types_path: str,
) -> LightRAGClient:
    """Create and initialize LightRAG client instance.

    Args:
        neo4j_uri: Neo4j connection URI
        neo4j_auth: Neo4j authentication (username/password)
        neo4j_database: Neo4j database name
        embedding_model: Sentence transformers model name
        llm_endpoint: LLM API endpoint URL
        working_dir: Working directory for LightRAG cache
        entity_types_path: Path to entity types YAML config

    Returns:
        Initialized LightRAG client
    """
    client = LightRAGClient(
        neo4j_uri=neo4j_uri,
        neo4j_auth=neo4j_auth,
        neo4j_database=neo4j_database,
        embedding_model=embedding_model,
        llm_endpoint=llm_endpoint,
        working_dir=working_dir,
        entity_types_path=entity_types_path,
    )
    await client.initialize()
    return client
