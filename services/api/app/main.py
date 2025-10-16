"""
RAG Engine FastAPI application.
Provides REST API endpoints for document ingestion, retrieval, and knowledge graph exploration.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import settings
from app.routers import config, documents, health
# from app.middleware import RequestLoggingMiddleware  # TODO: Implement if needed
from shared.utils.logging import configure_logging, get_logger

# Version
__version__ = "0.1.0"

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager for application startup and shutdown.
    """
    # Startup: Configure logging
    configure_logging(
        log_level=settings.LOG_LEVEL,
        log_format=settings.LOG_FORMAT,
        service_name="api",
    )

    logger.info(
        "api_service_starting",
        version=__version__,
        log_level=settings.LOG_LEVEL,
        log_format=settings.LOG_FORMAT,
        neo4j_uri=settings.NEO4J_URI,
        api_port=settings.API_PORT,
    )

    yield

    # Shutdown
    logger.info("api_service_shutting_down")


# Initialize FastAPI app
app = FastAPI(
    title="RAG Engine API",
    description=(
        "Production-ready RAG API with graph-based retrieval, multi-format document processing, "
        "and multiple integration interfaces (Open-WebUI, MCP, n8n, REST)."
    ),
    version=__version__,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request logging middleware
# app.add_middleware(RequestLoggingMiddleware)  # TODO: Implement if needed

# Include routers
app.include_router(health.router, tags=["health"])
app.include_router(config.router)
app.include_router(documents.router)


@app.get("/", tags=["root"])
async def root() -> dict[str, str]:
    """
    Root endpoint providing API information.

    Returns:
        dict: API metadata including version and documentation URLs
    """
    logger.debug("root_endpoint_accessed")
    return {
        "message": "RAG Engine API",
        "version": __version__,
        "docs_url": "/docs",
        "health_url": "/health",
    }


# Global exception handler for unhandled exceptions
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> dict[str, str]:
    """Log unhandled exceptions with full context."""
    logger.error(
        "unhandled_exception",
        path=request.url.path,
        method=request.method,
        error=str(exc),
        error_type=type(exc).__name__,
        exc_info=True,
    )
    return {
        "error": "internal_server_error",
        "message": "An unexpected error occurred. Please contact support.",
    }
