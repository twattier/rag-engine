"""Entity deduplication service using fuzzy matching."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import structlog
from rapidfuzz import fuzz

from ..db.neo4j_entity_store import Neo4jEntityStore
from ..models.entity_types import ExtractedEntity

logger = structlog.get_logger(__name__)


class EntityDeduplicator:
    """Service for deduplicating entities using fuzzy string matching."""

    def __init__(
        self,
        entity_store: Neo4jEntityStore,
        similarity_threshold: float = 90.0,
    ):
        """Initialize entity deduplicator.

        Args:
            entity_store: Neo4j entity store instance
            similarity_threshold: Minimum similarity score (0-100) to consider duplicate
        """
        self.entity_store = entity_store
        self.similarity_threshold = similarity_threshold

        logger.info(
            "entity_deduplicator_initialized",
            similarity_threshold=similarity_threshold,
        )

    async def find_or_create_entity(
        self, entity: ExtractedEntity, embedding: Optional[List[float]] = None
    ) -> str:
        """Find existing entity or create new one, handling deduplication.

        Args:
            entity: Extracted entity to process
            embedding: Optional vector embedding for entity

        Returns:
            Entity ID (new or existing)
        """
        # First, try exact match
        existing_entity = await self.entity_store.find_entity_by_name_and_type(
            entity.entity_name, entity.entity_type
        )

        if existing_entity:
            logger.debug(
                "entity_exact_match_found",
                entity_name=entity.entity_name,
                entity_type=entity.entity_type,
                entity_id=existing_entity["id"],
            )
            return existing_entity["id"]

        # If no exact match, try fuzzy matching
        duplicate_entity = await self._find_duplicate_entity(
            entity.entity_name, entity.entity_type
        )

        if duplicate_entity:
            # Duplicate found - update confidence if new one is higher
            # Note: Using same ID for source and target updates entity in-place
            # This is intentional - we're not merging two different entities,
            # but updating the existing entity's confidence score
            if entity.confidence_score > duplicate_entity["confidence_score"]:
                await self.entity_store.merge_entities(
                    source_entity_id=duplicate_entity["id"],
                    target_entity_id=duplicate_entity["id"],  # Update in place
                    new_confidence=entity.confidence_score,
                )

            logger.info(
                "entity_deduplicated",
                new_entity_name=entity.entity_name,
                existing_entity_name=duplicate_entity["name"],
                similarity_score=duplicate_entity.get("similarity", 0),
                entity_id=duplicate_entity["id"],
            )

            return duplicate_entity["id"]

        # No duplicate found - create new entity
        entity_id = await self.entity_store.store_entity(entity, embedding)

        logger.debug(
            "entity_created",
            entity_name=entity.entity_name,
            entity_type=entity.entity_type,
            entity_id=entity_id,
        )

        return entity_id

    async def _find_duplicate_entity(
        self, entity_name: str, entity_type: str
    ) -> Optional[Dict[str, Any]]:
        """Find duplicate entity using fuzzy string matching.

        Args:
            entity_name: Entity name to search for
            entity_type: Entity type to filter by

        Returns:
            Dict with entity data and similarity score, or None
        """
        # Get all entities of same type
        similar_entities = await self.entity_store.find_similar_entities(
            entity_name, entity_type
        )

        # Calculate fuzzy similarity for each
        best_match: Optional[Dict[str, Any]] = None
        best_similarity = 0.0

        entity_name_lower = entity_name.lower()

        for candidate in similar_entities:
            candidate_name_lower = candidate["name"].lower()

            # Calculate similarity score using rapidfuzz
            similarity = fuzz.ratio(entity_name_lower, candidate_name_lower)

            logger.debug(
                "fuzzy_match_check",
                entity_name=entity_name,
                candidate_name=candidate["name"],
                similarity=similarity,
                threshold=self.similarity_threshold,
            )

            if similarity > best_similarity and similarity > self.similarity_threshold:
                best_similarity = similarity
                best_match = candidate.copy()
                best_match["similarity"] = similarity

        return best_match
