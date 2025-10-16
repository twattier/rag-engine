"""Pytest fixtures for RAG-Anything service tests."""
from __future__ import annotations

import sys
from pathlib import Path
from typing import AsyncGenerator

import pytest
from httpx import AsyncClient, ASGITransport

# Add app and shared to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "shared"))

from app.service import app


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client for testing FastAPI endpoints."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def fixtures_dir() -> Path:
    """Path to test fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def sample_txt_file(fixtures_dir: Path) -> Path:
    """Path to sample TXT file."""
    return fixtures_dir / "climate-abstract.txt"


@pytest.fixture
def sample_md_file(fixtures_dir: Path) -> Path:
    """Path to sample MD file."""
    return fixtures_dir / "climate-report.md"


@pytest.fixture
def sample_csv_file(fixtures_dir: Path) -> Path:
    """Path to sample CSV file."""
    return fixtures_dir / "climate-data.csv"


@pytest.fixture
def sample_pdf_file(fixtures_dir: Path) -> Path:
    """Path to sample PDF file."""
    return fixtures_dir / "climate-research-paper.pdf"


@pytest.fixture
def sample_docx_file(fixtures_dir: Path) -> Path:
    """Path to sample DOCX file."""
    return fixtures_dir / "climate-mitigation-strategies.docx"


@pytest.fixture
def sample_pptx_file(fixtures_dir: Path) -> Path:
    """Path to sample PPTX file."""
    return fixtures_dir / "climate-science-presentation.pptx"
