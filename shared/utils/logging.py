"""
Centralized structured logging configuration for RAG Engine.

Provides consistent logging setup across all services using structlog.
"""

from __future__ import annotations

import logging
import sys

import structlog
from typing import Literal


LogFormat = Literal["json", "console"]


def configure_logging(
    log_level: str = "INFO",
    log_format: LogFormat = "json",
    service_name: str = "rag-engine",
) -> None:
    """
    Configure structured logging for RAG Engine services.

    Args:
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_format: Output format ("json" for production, "console" for development)
        service_name: Name of the service (for log context)

    Example:
        ```python
        from shared.utils.logging import configure_logging

        configure_logging(log_level="INFO", log_format="json", service_name="api")

        logger = structlog.get_logger(__name__)
        logger.info("service_started", port=8000)
        ```
    """
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper(), logging.INFO),
    )

    # Common processors for all log formats
    common_processors = [
        structlog.stdlib.filter_by_level,
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    # Add service name to all log entries
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(service=service_name)

    if log_format == "json":
        # Production: JSON logs for parsing and aggregation
        processors = common_processors + [
            structlog.processors.JSONRenderer(),
        ]
    else:
        # Development: Human-readable console logs with colors
        processors = common_processors + [
            structlog.dev.ConsoleRenderer(colors=True),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Structured logger instance

    Example:
        ```python
        logger = get_logger(__name__)
        logger.info("user_login", user_id="user123", ip_address="192.168.1.1")
        ```
    """
    return structlog.get_logger(name)
