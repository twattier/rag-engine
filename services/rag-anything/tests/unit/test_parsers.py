"""Unit tests for document parsers."""
from __future__ import annotations

import pytest
from pathlib import Path

from app.parsers.text_parser import TextParser
from app.parsers.csv_parser import CSVParser
from app.parsers.pdf_parser import PDFParser
from app.parsers.docx_parser import DOCXParser
from app.parsers.pptx_parser import PPTXParser
from app.parsers.parser_factory import ParserFactory


class TestTextParser:
    """Tests for TextParser."""

    @pytest.mark.asyncio
    async def test_parse_txt_success(self, sample_txt_file: Path):
        """Test successful TXT file parsing."""
        parser = TextParser()
        content_list = await parser.parse(sample_txt_file)

        assert len(content_list) > 0
        assert content_list[0].type == "text"
        assert len(content_list[0].text) > 0
        assert "climate" in content_list[0].text.lower()

    @pytest.mark.asyncio
    async def test_parse_md_success(self, sample_md_file: Path):
        """Test successful MD file parsing."""
        parser = TextParser()
        content_list = await parser.parse(sample_md_file)

        assert len(content_list) > 0
        assert content_list[0].type == "text"
        assert "climate" in content_list[0].text.lower()


class TestCSVParser:
    """Tests for CSVParser."""

    @pytest.mark.asyncio
    async def test_parse_csv_success(self, sample_csv_file: Path):
        """Test successful CSV file parsing."""
        parser = CSVParser()
        content_list = await parser.parse(sample_csv_file)

        assert len(content_list) == 1
        assert content_list[0].type == "table"
        assert content_list[0].rows is not None
        assert len(content_list[0].rows) > 0


class TestPDFParser:
    """Tests for PDFParser."""

    @pytest.mark.asyncio
    async def test_parse_pdf_success(self, sample_pdf_file: Path):
        """Test successful PDF file parsing."""
        parser = PDFParser()
        content_list = await parser.parse(sample_pdf_file)

        assert len(content_list) > 0
        assert content_list[0].type == "text"
        assert content_list[0].page_idx >= 0


class TestDOCXParser:
    """Tests for DOCXParser."""

    @pytest.mark.asyncio
    async def test_parse_docx_success(self, sample_docx_file: Path):
        """Test successful DOCX file parsing."""
        parser = DOCXParser()
        content_list = await parser.parse(sample_docx_file)

        assert len(content_list) > 0
        # Should have at least text content
        text_items = [item for item in content_list if item.type == "text"]
        assert len(text_items) > 0


class TestPPTXParser:
    """Tests for PPTXParser."""

    @pytest.mark.asyncio
    async def test_parse_pptx_success(self, sample_pptx_file: Path):
        """Test successful PPTX file parsing."""
        parser = PPTXParser()
        content_list = await parser.parse(sample_pptx_file)

        assert len(content_list) > 0
        # PPTX should have slide content
        assert any(item.type == "text" for item in content_list)


class TestParserFactory:
    """Tests for ParserFactory."""

    def test_get_parser_txt(self):
        """Test getting TXT parser."""
        parser = ParserFactory.get_parser("txt")
        assert isinstance(parser, TextParser)

    def test_get_parser_md(self):
        """Test getting MD parser."""
        parser = ParserFactory.get_parser("md")
        assert isinstance(parser, TextParser)

    def test_get_parser_csv(self):
        """Test getting CSV parser."""
        parser = ParserFactory.get_parser("csv")
        assert isinstance(parser, CSVParser)

    def test_get_parser_pdf(self):
        """Test getting PDF parser."""
        parser = ParserFactory.get_parser("pdf")
        assert isinstance(parser, PDFParser)

    def test_get_parser_docx(self):
        """Test getting DOCX parser."""
        parser = ParserFactory.get_parser("docx")
        assert isinstance(parser, DOCXParser)

    def test_get_parser_pptx(self):
        """Test getting PPTX parser."""
        parser = ParserFactory.get_parser("pptx")
        assert isinstance(parser, PPTXParser)

    def test_get_parser_unsupported(self):
        """Test getting parser for unsupported format."""
        with pytest.raises(ValueError, match="Unsupported format"):
            ParserFactory.get_parser("xyz")

    def test_get_supported_formats(self):
        """Test getting list of supported formats."""
        formats = ParserFactory.get_supported_formats()
        assert "txt" in formats
        assert "pdf" in formats
        assert "docx" in formats
        assert "pptx" in formats
        assert "csv" in formats
        assert "md" in formats
