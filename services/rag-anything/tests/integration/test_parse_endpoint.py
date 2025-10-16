"""Integration tests for /parse endpoint."""
from __future__ import annotations

import pytest
from pathlib import Path
from httpx import AsyncClient


class TestParseEndpoint:
    """Integration tests for document parsing endpoint."""

    @pytest.mark.asyncio
    async def test_health_endpoint(self, async_client: AsyncClient):
        """Test health check endpoint."""
        response = await async_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "parsers_available" in data

    @pytest.mark.asyncio
    async def test_parse_txt_success(
        self, async_client: AsyncClient, sample_txt_file: Path
    ):
        """Test successful TXT file parsing."""
        with sample_txt_file.open("rb") as f:
            files = {"file": ("test.txt", f, "text/plain")}
            response = await async_client.post("/parse", files=files)

        assert response.status_code == 200
        data = response.json()
        assert "content_list" in data
        assert "metadata" in data
        assert data["metadata"]["format"] == "txt"
        assert len(data["content_list"]) > 0

    @pytest.mark.asyncio
    async def test_parse_md_success(
        self, async_client: AsyncClient, sample_md_file: Path
    ):
        """Test successful MD file parsing."""
        with sample_md_file.open("rb") as f:
            files = {"file": ("test.md", f, "text/markdown")}
            response = await async_client.post("/parse", files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["metadata"]["format"] == "md"
        assert len(data["content_list"]) > 0

    @pytest.mark.asyncio
    async def test_parse_csv_success(
        self, async_client: AsyncClient, sample_csv_file: Path
    ):
        """Test successful CSV file parsing."""
        with sample_csv_file.open("rb") as f:
            files = {"file": ("test.csv", f, "text/csv")}
            response = await async_client.post("/parse", files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["metadata"]["format"] == "csv"
        assert len(data["content_list"]) > 0
        assert data["content_list"][0]["type"] == "table"

    @pytest.mark.asyncio
    async def test_parse_pdf_success(
        self, async_client: AsyncClient, sample_pdf_file: Path
    ):
        """Test successful PDF file parsing."""
        with sample_pdf_file.open("rb") as f:
            files = {"file": ("test.pdf", f, "application/pdf")}
            response = await async_client.post("/parse", files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["metadata"]["format"] == "pdf"
        assert len(data["content_list"]) > 0

    @pytest.mark.asyncio
    async def test_parse_docx_success(
        self, async_client: AsyncClient, sample_docx_file: Path
    ):
        """Test successful DOCX file parsing."""
        with sample_docx_file.open("rb") as f:
            files = {"file": ("test.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
            response = await async_client.post("/parse", files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["metadata"]["format"] == "docx"
        assert len(data["content_list"]) > 0

    @pytest.mark.asyncio
    async def test_parse_pptx_success(
        self, async_client: AsyncClient, sample_pptx_file: Path
    ):
        """Test successful PPTX file parsing."""
        with sample_pptx_file.open("rb") as f:
            files = {"file": ("test.pptx", f, "application/vnd.openxmlformats-officedocument.presentationml.presentation")}
            response = await async_client.post("/parse", files=files)

        assert response.status_code == 200
        data = response.json()
        assert data["metadata"]["format"] == "pptx"
        assert len(data["content_list"]) > 0

    @pytest.mark.asyncio
    async def test_parse_unsupported_format(self, async_client: AsyncClient):
        """Test parsing unsupported file format."""
        files = {"file": ("test.xyz", b"fake content", "application/octet-stream")}
        response = await async_client.post("/parse", files=files)

        assert response.status_code in (400, 422)
        data = response.json()
        assert "error" in data
        assert data["error"]["code"] == "UNSUPPORTED_FORMAT"

    @pytest.mark.asyncio
    async def test_parse_missing_filename(self, async_client: AsyncClient):
        """Test parsing with missing filename."""
        files = {"file": ("", b"content", "text/plain")}
        response = await async_client.post("/parse", files=files)

        assert response.status_code in (400, 422)
