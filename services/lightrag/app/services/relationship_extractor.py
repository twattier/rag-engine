"""Relationship extraction service using LLM prompting."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List
from uuid import UUID

import httpx
import structlog

from ..models.entity_types import ExtractedEntity, ExtractedRelationship

logger = structlog.get_logger(__name__)


class RelationshipExtractor:
    """Service for extracting relationships between entities using LLM."""

    def __init__(
        self,
        llm_endpoint: str,
        llm_model: str = "gpt-4",
        llm_api_key: str | None = None,
    ):
        """Initialize relationship extractor with configuration.

        Args:
            llm_endpoint: OpenAI-compatible LLM API endpoint
            llm_model: Model name to use for extraction
            llm_api_key: API key for LLM endpoint (optional for local models)
        """
        self.llm_endpoint = llm_endpoint
        self.llm_model = llm_model
        self.llm_api_key = llm_api_key

        logger.info(
            "relationship_extractor_initialized",
            llm_endpoint=llm_endpoint,
            llm_model=llm_model,
        )

    async def extract_relationships(
        self, entities: List[ExtractedEntity], document_text: str
    ) -> List[ExtractedRelationship]:
        """Extract relationships between entities from document text.

        Args:
            entities: List of entities extracted from the document
            document_text: Original document text

        Returns:
            List of extracted relationships

        Raises:
            ValueError: If entities list is empty
            RuntimeError: If LLM call fails
        """
        if not entities:
            logger.warning("extract_relationships_no_entities")
            return []

        doc_id = entities[0].source_document_id

        logger.info(
            "relationship_extraction_started",
            doc_id=str(doc_id),
            entities_count=len(entities),
        )

        # Build relationship extraction prompt
        prompt = self._build_extraction_prompt(entities, document_text)

        # Call LLM to extract relationships
        llm_response = await self._call_llm(prompt)

        # Parse LLM response into structured relationships
        extracted_relationships = self._parse_llm_response(llm_response, doc_id)

        logger.info(
            "relationship_extraction_completed",
            doc_id=str(doc_id),
            relationships_extracted_count=len(extracted_relationships),
        )

        return extracted_relationships

    def _build_extraction_prompt(
        self, entities: List[ExtractedEntity], document_text: str
    ) -> str:
        """Build LLM prompt for relationship extraction.

        Args:
            entities: List of extracted entities
            document_text: Original document text

        Returns:
            Formatted prompt string
        """
        # Format entity list
        entity_list = "\n".join(
            [f"- {e.entity_name} ({e.entity_type})" for e in entities]
        )

        # Build prompt with examples
        prompt = f"""You are an expert at identifying relationships between entities in documents.

DOCUMENT TEXT:
{document_text[:2000]}  # Truncate for token efficiency

EXTRACTED ENTITIES:
{entity_list}

TASK:
Identify relationships between the entities above. For each relationship, provide:
- source_entity_name: Name of the source entity
- target_entity_name: Name of the target entity
- relationship_type: One of [MENTIONS, RELATED_TO, PART_OF, IMPLEMENTS, DEPENDS_ON, LOCATED_IN, AUTHORED_BY]
- confidence_score: Confidence score between 0.0 and 1.0

RELATIONSHIP TYPE DEFINITIONS:
- MENTIONS: Entity A mentions entity B in the text
- RELATED_TO: Generic semantic relationship between entities
- PART_OF: Entity A is part of entity B (e.g., "Database Admin" PART_OF "Engineering")
- IMPLEMENTS: Technology implements a concept (e.g., "PostgreSQL" IMPLEMENTS "Database")
- DEPENDS_ON: Dependency relationship (e.g., "API Service" DEPENDS_ON "Neo4j")
- LOCATED_IN: Geographic relationship (e.g., "Google" LOCATED_IN "San Francisco")
- AUTHORED_BY: Document authorship (e.g., "Resume" AUTHORED_BY "John Doe")

Return ONLY a JSON array of relationships. Example:
```json
[
  {{
    "source_entity_name": "Python",
    "target_entity_name": "Programming Skills",
    "relationship_type": "PART_OF",
    "confidence_score": 0.95
  }},
  {{
    "source_entity_name": "John Doe",
    "target_entity_name": "Software Engineering",
    "relationship_type": "RELATED_TO",
    "confidence_score": 0.90
  }}
]
```

Return the JSON array now:"""

        return prompt

    async def _call_llm(self, prompt: str) -> str:
        """Call LLM endpoint with relationship extraction prompt.

        Args:
            prompt: Formatted relationship extraction prompt

        Returns:
            LLM response text

        Raises:
            RuntimeError: If LLM call fails
        """
        # Prepare headers
        headers = {
            "Content-Type": "application/json",
        }
        if self.llm_api_key:
            headers["Authorization"] = f"Bearer {self.llm_api_key}"

        # Prepare request payload (OpenAI-compatible format)
        payload = {
            "model": self.llm_model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert relationship extraction system. Extract relationships between entities and return valid JSON arrays.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.0,  # Deterministic extraction
            "max_tokens": 4096,
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.llm_endpoint}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()

                result = response.json()
                llm_text = result["choices"][0]["message"]["content"]

                logger.debug(
                    "llm_call_success",
                    response_length=len(llm_text),
                )

                return llm_text

        except httpx.HTTPError as e:
            logger.error(
                "llm_call_failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            raise RuntimeError(f"LLM call failed: {e}") from e

    def _parse_llm_response(
        self, llm_response: str, doc_id: UUID
    ) -> List[ExtractedRelationship]:
        """Parse LLM response into structured ExtractedRelationship objects.

        Args:
            llm_response: Raw LLM response text
            doc_id: Document UUID

        Returns:
            List of ExtractedRelationship objects

        Raises:
            ValueError: If LLM response is not valid JSON
        """
        # Extract JSON array from response (handle markdown code blocks)
        json_match = re.search(r"```(?:json)?\s*(\[.*?\])\s*```", llm_response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find JSON array directly
            json_match = re.search(r"\[.*?\]", llm_response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                logger.warning(
                    "llm_response_no_json_array",
                    response=llm_response[:200],
                )
                return []

        try:
            relationships_raw = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(
                "llm_response_invalid_json",
                error=str(e),
                response=llm_response[:200],
            )
            raise ValueError(f"LLM response is not valid JSON: {e}") from e

        # Parse each relationship
        extracted_relationships: List[ExtractedRelationship] = []

        for rel_data in relationships_raw:
            try:
                # Map 'confidence' to 'confidence_score' if needed
                if "confidence" in rel_data and "confidence_score" not in rel_data:
                    rel_data["confidence_score"] = rel_data.pop("confidence")

                # Add source document ID
                rel_data["source_document_id"] = doc_id

                # Create ExtractedRelationship object (validates fields)
                relationship = ExtractedRelationship(**rel_data)
                extracted_relationships.append(relationship)

                logger.debug(
                    "relationship_extracted",
                    source=relationship.source_entity_name,
                    target=relationship.target_entity_name,
                    relationship_type=relationship.relationship_type,
                    confidence_score=relationship.confidence_score,
                )

            except Exception as e:
                logger.warning(
                    "relationship_parse_failed",
                    rel_data=rel_data,
                    error=str(e),
                )
                continue

        return extracted_relationships
