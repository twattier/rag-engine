"""Metadata mapping parser for batch ingestion."""
from __future__ import annotations

import csv
import io
import json
from typing import Any, Dict

from fastapi import UploadFile

from shared.utils.logging import get_logger

logger = get_logger(__name__)


class MetadataMapper:
    """Parser for CSV and JSON metadata mappings."""

    @staticmethod
    async def parse_metadata_mapping(file: UploadFile) -> Dict[str, Dict[str, Any]]:
        """Parse metadata mapping file (CSV or JSON).

        Args:
            file: Uploaded metadata mapping file

        Returns:
            Dict mapping filename to metadata dict

        Raises:
            ValueError: If file format is unsupported or parsing fails
        """
        if not file.filename:
            raise ValueError("Metadata mapping file must have a filename")

        # Determine format from extension
        ext = file.filename.split(".")[-1].lower() if "." in file.filename else ""

        content = await file.read()
        await file.seek(0)  # Reset for potential re-reading

        if ext == "csv":
            return MetadataMapper._parse_csv(content)
        elif ext == "json":
            return MetadataMapper._parse_json(content)
        else:
            raise ValueError(
                f"Unsupported metadata mapping format: .{ext}. Supported formats: csv, json"
            )

    @staticmethod
    def _parse_csv(content: bytes) -> Dict[str, Dict[str, Any]]:
        """Parse CSV metadata mapping.

        CSV Format:
        filename,author,department,date_created,tags,category
        doc1.pdf,John Doe,Engineering,2025-10-16,"technical,api",specification

        Args:
            content: CSV file content

        Returns:
            Dict mapping filename to metadata dict

        Raises:
            ValueError: If CSV parsing fails
        """
        try:
            # Decode bytes to string
            text_content = content.decode("utf-8")

            # Parse CSV
            reader = csv.DictReader(io.StringIO(text_content))

            mapping: Dict[str, Dict[str, Any]] = {}

            for row in reader:
                if "filename" not in row:
                    raise ValueError("CSV must have 'filename' column")

                filename = row.pop("filename")

                # Convert tags string to list if present
                if "tags" in row and row["tags"]:
                    # Split comma-separated tags and strip whitespace
                    row["tags"] = [tag.strip() for tag in row["tags"].split(",")]

                # Remove empty values
                metadata = {k: v for k, v in row.items() if v}

                mapping[filename] = metadata

            logger.info(
                "csv_metadata_mapping_parsed",
                file_count=len(mapping),
            )

            return mapping

        except Exception as e:
            logger.error(
                "csv_metadata_parsing_failed",
                error=str(e),
                error_type=type(e).__name__,
            )
            raise ValueError(f"Failed to parse CSV metadata mapping: {str(e)}")

    @staticmethod
    def _parse_json(content: bytes) -> Dict[str, Dict[str, Any]]:
        """Parse JSON metadata mapping.

        JSON Format:
        {
          "doc1.pdf": {
            "author": "John Doe",
            "department": "Engineering",
            "tags": ["technical", "api"]
          }
        }

        Args:
            content: JSON file content

        Returns:
            Dict mapping filename to metadata dict

        Raises:
            ValueError: If JSON parsing fails
        """
        try:
            # Decode bytes to string and parse JSON
            text_content = content.decode("utf-8")
            mapping = json.loads(text_content)

            if not isinstance(mapping, dict):
                raise ValueError("JSON metadata mapping must be an object/dict")

            # Validate all values are dicts
            for filename, metadata in mapping.items():
                if not isinstance(metadata, dict):
                    raise ValueError(
                        f"Metadata for '{filename}' must be an object/dict"
                    )

            logger.info(
                "json_metadata_mapping_parsed",
                file_count=len(mapping),
            )

            return mapping

        except json.JSONDecodeError as e:
            logger.error(
                "json_metadata_parsing_failed",
                error=str(e),
            )
            raise ValueError(f"Failed to parse JSON metadata mapping: {str(e)}")

        except Exception as e:
            logger.error(
                "json_metadata_parsing_error",
                error=str(e),
                error_type=type(e).__name__,
            )
            raise ValueError(f"Failed to parse JSON metadata mapping: {str(e)}")
