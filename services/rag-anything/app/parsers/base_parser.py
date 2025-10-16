"""Base parser interface for document parsers."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path

from app.models import ContentItem


class BaseParser(ABC):
    """Abstract base class for document parsers."""

    @abstractmethod
    async def parse(self, file_path: Path) -> list[ContentItem]:
        """
        Parse document and return structured content list.

        Args:
            file_path: Path to document file

        Returns:
            List of ContentItem objects with extracted content

        Raises:
            Exception: If parsing fails
        """
        pass
