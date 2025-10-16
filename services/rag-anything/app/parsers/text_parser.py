"""Plain text and Markdown parser."""
from __future__ import annotations

from pathlib import Path

from app.parsers.base_parser import BaseParser
from app.models import ContentItem


class TextParser(BaseParser):
    """Parser for plain text (.txt) and Markdown (.md) files."""

    async def parse(self, file_path: Path) -> list[ContentItem]:
        """Parse text file and return content."""
        with file_path.open("r", encoding="utf-8") as f:
            content = f.read()

        if not content.strip():
            return []

        return [
            ContentItem(
                type="text",
                text=content,
                page_idx=0,
                structure="plain_text",
            )
        ]
