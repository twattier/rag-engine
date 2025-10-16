"""PDF parser using pypdf."""
from __future__ import annotations

from pathlib import Path
from pypdf import PdfReader

from app.parsers.base_parser import BaseParser
from app.models import ContentItem


class PDFParser(BaseParser):
    """Parser for PDF files using pypdf."""

    async def parse(self, file_path: Path) -> list[ContentItem]:
        """Parse PDF file and return content."""
        reader = PdfReader(file_path)
        content_list: list[ContentItem] = []

        for page_idx, page in enumerate(reader.pages):
            text = page.extract_text()

            if text.strip():
                content_list.append(
                    ContentItem(
                        type="text",
                        text=text,
                        page_idx=page_idx,
                        structure="pdf_page",
                    )
                )

        return content_list
