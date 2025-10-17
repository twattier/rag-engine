"""Entity extraction service with custom entity types and LLM prompting."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List
from uuid import UUID

import httpx
import structlog

from ..models.entity_types import EntityType, ExtractedEntity
from ..utils.entity_config import build_extraction_prompt, load_entity_types

logger = structlog.get_logger(__name__)


class EntityExtractor:
    """Service for extracting entities from documents using LLM."""

    def __init__(
        self,
        entity_types_path: str,
        llm_endpoint: str,
        llm_model: str = "gpt-4",
        llm_api_key: str | None = None,
    ):
        """Initialize entity extractor with configuration.

        Args:
            entity_types_path: Path to entity-types.yaml configuration
            llm_endpoint: OpenAI-compatible LLM API endpoint
            llm_model: Model name to use for extraction
            llm_api_key: API key for LLM endpoint (optional for local models)
        """
        self.entity_types_path = entity_types_path
        self.llm_endpoint = llm_endpoint
        self.llm_model = llm_model
        self.llm_api_key = llm_api_key

        # Load entity types configuration
        self.entity_types: List[EntityType] = load_entity_types(entity_types_path)

        logger.info(
            "entity_extractor_initialized",
            entity_types_count=len(self.entity_types),
            llm_endpoint=llm_endpoint,
            llm_model=llm_model,
        )

    async def extract_entities(
        self, document: Dict[str, Any]
    ) -> List[ExtractedEntity]:
        """Extract entities from a document using LLM.

        Args:
            document: Document dictionary with keys:
                - id (UUID): Document ID
                - text (str): Document text content
                - metadata (Dict): Optional metadata

        Returns:
            List of extracted entities with metadata

        Raises:
            ValueError: If document structure is invalid
            RuntimeError: If LLM call fails
        """
        # Validate document structure
        if "id" not in document:
            raise ValueError("Document must have 'id' field")
        if "text" not in document:
            raise ValueError("Document must have 'text' field")

        doc_id = UUID(document["id"]) if isinstance(document["id"], str) else document["id"]
        text = document["text"]

        logger.info(
            "entity_extraction_started",
            doc_id=str(doc_id),
            text_length=len(text),
            entity_types_count=len(self.entity_types),
        )

        # Build extraction prompt
        prompt = build_extraction_prompt(self.entity_types, text)

        # Call LLM to extract entities
        llm_response = await self._call_llm(prompt)

        # Parse LLM response into structured entities
        extracted_entities = self._parse_llm_response(
            llm_response, doc_id, text
        )

        logger.info(
            "entity_extraction_completed",
            doc_id=str(doc_id),
            entities_extracted_count=len(extracted_entities),
        )

        return extracted_entities

    async def _call_llm(self, prompt: str) -> str:
        """Call LLM endpoint with extraction prompt.

        Args:
            prompt: Formatted entity extraction prompt

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
                    "content": "You are an expert entity extraction system. Extract entities from documents and return valid JSON arrays.",
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
        self, llm_response: str, doc_id: UUID, document_text: str
    ) -> List[ExtractedEntity]:
        """Parse LLM response into structured ExtractedEntity objects.

        Args:
            llm_response: Raw LLM response text
            doc_id: Document UUID
            document_text: Original document text for text_span calculation

        Returns:
            List of ExtractedEntity objects

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
            entities_raw = json.loads(json_str)
        except json.JSONDecodeError as e:
            logger.error(
                "llm_response_invalid_json",
                error=str(e),
                response=llm_response[:200],
            )
            raise ValueError(f"LLM response is not valid JSON: {e}") from e

        # Parse each entity
        extracted_entities: List[ExtractedEntity] = []

        for entity_data in entities_raw:
            try:
                # Map 'confidence' to 'confidence_score' if needed
                if "confidence" in entity_data and "confidence_score" not in entity_data:
                    entity_data["confidence_score"] = entity_data.pop("confidence")

                # Calculate text_span if not provided
                if "text_span" not in entity_data or not entity_data["text_span"]:
                    entity_data["text_span"] = self._find_text_span(
                        entity_data["entity_name"], document_text
                    )

                # Add source document ID
                entity_data["source_document_id"] = doc_id

                # Create ExtractedEntity object (validates fields)
                entity = ExtractedEntity(**entity_data)
                extracted_entities.append(entity)

                logger.debug(
                    "entity_extracted",
                    entity_name=entity.entity_name,
                    entity_type=entity.entity_type,
                    confidence_score=entity.confidence_score,
                )

            except Exception as e:
                logger.warning(
                    "entity_parse_failed",
                    entity_data=entity_data,
                    error=str(e),
                )
                continue

        return extracted_entities

    def _find_text_span(self, entity_name: str, document_text: str) -> str:
        """Find character offset of entity in document text.

        Args:
            entity_name: Name of entity to find
            document_text: Full document text

        Returns:
            Text span string (e.g., "char 245-260")
        """
        # Case-insensitive search
        entity_lower = entity_name.lower()
        doc_lower = document_text.lower()

        start_idx = doc_lower.find(entity_lower)

        if start_idx != -1:
            end_idx = start_idx + len(entity_name)
            return f"char {start_idx}-{end_idx}"

        # Entity not found in text (possibly paraphrased)
        return "not found"
