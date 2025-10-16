"""Pydantic models for RAG-Anything service."""
from __future__ import annotations

from typing import Any, Literal
from pydantic import BaseModel, Field


class ContentItem(BaseModel):
    """Single content item from parsed document."""

    type: Literal["text", "image", "table", "equation"]
    text: str | None = None
    image_ref: str | None = None
    caption: str | None = None
    rows: list[list[Any]] | None = None
    latex: str | None = None
    page_idx: int = 0
    structure: str | None = None


class ParseMetadata(BaseModel):
    """Metadata about parsed document."""

    filename: str
    format: str
    pages: int | None = None
    parse_method: str
    file_size: int | None = None


class ParseResponse(BaseModel):
    """Response from parse endpoint."""

    content_list: list[ContentItem] = Field(default_factory=list)
    metadata: ParseMetadata


class ApiError(BaseModel):
    """Standardized error response."""

    error: dict[str, str] = Field(
        ...,
        examples=[
            {
                "code": "UNSUPPORTED_FORMAT",
                "message": "File format .xyz is not supported. Supported formats: pdf, txt, md, docx, pptx, csv",
            }
        ],
    )


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    service: str
    parsers_available: list[str]
