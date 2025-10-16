"""Main FastAPI application for RAG-Anything document parsing service."""
from __future__ import annotations

import sys
import shutil
from pathlib import Path
from contextlib import asynccontextmanager

# Add shared to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "shared"))

from fastapi import FastAPI, File, UploadFile, HTTPException, status
from fastapi.responses import JSONResponse

from shared.utils.logging import configure_logging, get_logger
from app.config import get_settings
from app.models import ParseResponse, ApiError, HealthResponse, ParseMetadata
from app.parsers.parser_factory import ParserFactory

settings = get_settings()

# Configure structured logging using shared utility
configure_logging(
    log_level=settings.LOG_LEVEL,
    log_format="json",
    service_name=settings.SERVICE_NAME,
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    logger.info(
        "service_started",
        service=settings.SERVICE_NAME,
        upload_dir=str(upload_dir),
        supported_formats=settings.SUPPORTED_FORMATS,
    )
    yield
    # Shutdown
    logger.info("service_stopped", service=settings.SERVICE_NAME)


app = FastAPI(
    title="RAG-Anything Document Parsing Service",
    description="Multi-format document parsing service for RAG Engine",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        service=settings.SERVICE_NAME,
        parsers_available=settings.SUPPORTED_FORMATS,
    )


@app.post("/parse", response_model=ParseResponse, responses={400: {"model": ApiError}, 500: {"model": ApiError}})
async def parse_document(file: UploadFile = File(...)) -> ParseResponse:
    """
    Parse uploaded document and extract structured content.

    Accepts multipart/form-data file upload and returns structured JSON with:
    - Text blocks with structure preservation
    - Images (as base64 or references)
    - Tables (as row/column data)
    - Equations (as LaTeX)

    Supported formats: PDF, TXT, MD, DOCX, PPTX, CSV
    """
    if not file.filename:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": {
                    "code": "MISSING_FILENAME",
                    "message": "File must have a filename",
                }
            },
        )

    # Validate file format
    file_ext = Path(file.filename).suffix.lower().lstrip(".")
    if file_ext not in settings.SUPPORTED_FORMATS:
        logger.warning(
            "unsupported_format_attempted",
            filename=file.filename,
            extension=file_ext,
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": {
                    "code": "UNSUPPORTED_FORMAT",
                    "message": f"File format .{file_ext} is not supported. Supported formats: {', '.join(settings.SUPPORTED_FORMATS)}",
                }
            },
        )

    # Save uploaded file
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)  # Ensure directory exists
    temp_file_path = upload_dir / file.filename
    try:
        with temp_file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        file_size = temp_file_path.stat().st_size

        # Validate file size
        if file_size > settings.MAX_FILE_SIZE:
            logger.warning(
                "file_too_large",
                filename=file.filename,
                size=file_size,
                max_size=settings.MAX_FILE_SIZE,
            )
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "error": {
                        "code": "FILE_TOO_LARGE",
                        "message": f"File size {file_size} exceeds maximum {settings.MAX_FILE_SIZE}",
                    }
                },
            )

        logger.info(
            "file_uploaded",
            filename=file.filename,
            size=file_size,
            format=file_ext,
        )

        # Parse document
        parser = ParserFactory.get_parser(file_ext)
        content_list = await parser.parse(temp_file_path)

        # Build metadata
        metadata = ParseMetadata(
            filename=file.filename,
            format=file_ext,
            pages=len(content_list) if content_list else None,
            parse_method=parser.__class__.__name__.lower(),
            file_size=file_size,
        )

        logger.info(
            "parse_completed",
            filename=file.filename,
            content_items=len(content_list),
            parser=metadata.parse_method,
        )

        return ParseResponse(content_list=content_list, metadata=metadata)

    except Exception as e:
        logger.error(
            "parse_failed",
            filename=file.filename,
            error=str(e),
            exc_info=True,
        )
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "PARSING_FAILED",
                    "message": f"Failed to parse document: {str(e)}",
                }
            },
        )

    finally:
        # Clean up temporary file
        if temp_file_path.exists():
            try:
                temp_file_path.unlink()
            except Exception as cleanup_error:
                logger.warning("file_cleanup_failed", filename=file.filename, error=str(cleanup_error))
