"""
RAG Engine FastAPI application.
Provides REST API endpoints for document ingestion, retrieval, and knowledge graph exploration.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import structlog

from app.config import settings
from app.routers import health

# Version
__version__ = "0.1.0"


def configure_logging():
    """Configure structured logging with structlog."""
    if settings.LOG_FORMAT == "json":
        # Production: JSON logs
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.processors.JSONRenderer(),
            ],
            wrapper_class=structlog.stdlib.BoundLogger,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )
    else:
        # Development: Console logs
        structlog.configure(
            processors=[
                structlog.stdlib.filter_by_level,
                structlog.stdlib.add_logger_name,
                structlog.stdlib.add_log_level,
                structlog.stdlib.PositionalArgumentsFormatter(),
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.StackInfoRenderer(),
                structlog.processors.format_exc_info,
                structlog.processors.UnicodeDecoder(),
                structlog.dev.ConsoleRenderer(),
            ],
            wrapper_class=structlog.stdlib.BoundLogger,
            logger_factory=structlog.stdlib.LoggerFactory(),
            cache_logger_on_first_use=True,
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager for application startup and shutdown.
    """
    # Startup
    configure_logging()
    logger = structlog.get_logger(__name__)

    logger.info(
        "api_service_starting",
        version=__version__,
        log_level=settings.LOG_LEVEL,
        neo4j_uri=settings.NEO4J_URI,
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

# Include routers
app.include_router(health.router, tags=["health"])


@app.get("/", tags=["root"])
async def root() -> dict[str, str]:
    """
    Root endpoint providing API information.

    Returns:
        dict: API metadata including version and documentation URLs
    """
    return {
        "message": "RAG Engine API",
        "version": __version__,
        "docs_url": "/docs",
        "health_url": "/health",
    }
