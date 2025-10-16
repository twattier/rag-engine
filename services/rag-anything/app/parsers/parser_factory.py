"""Parser factory for selecting appropriate parser by file type."""
from __future__ import annotations

from app.parsers.base_parser import BaseParser
from app.parsers.text_parser import TextParser
from app.parsers.csv_parser import CSVParser
from app.parsers.pdf_parser import PDFParser
from app.parsers.docx_parser import DOCXParser
from app.parsers.pptx_parser import PPTXParser


class ParserFactory:
    """Factory for creating appropriate parser based on file format."""

    _parsers: dict[str, type[BaseParser]] = {
        "txt": TextParser,
        "md": TextParser,
        "csv": CSVParser,
        "pdf": PDFParser,
        "docx": DOCXParser,
        "pptx": PPTXParser,
    }

    @classmethod
    def get_parser(cls, file_format: str) -> BaseParser:
        """
        Get parser instance for given file format.

        Args:
            file_format: File extension (without dot) - e.g., "pdf", "docx"

        Returns:
            Parser instance for the format

        Raises:
            ValueError: If format is not supported
        """
        parser_class = cls._parsers.get(file_format.lower())
        if not parser_class:
            raise ValueError(
                f"Unsupported format: {file_format}. "
                f"Supported formats: {', '.join(cls._parsers.keys())}"
            )
        return parser_class()

    @classmethod
    def get_supported_formats(cls) -> list[str]:
        """Get list of supported file formats."""
        return list(cls._parsers.keys())
