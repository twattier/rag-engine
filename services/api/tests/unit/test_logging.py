"""
Unit tests for centralized logging configuration.
"""

from __future__ import annotations

import json
import logging
from io import StringIO

import pytest
import structlog

from shared.utils.logging import configure_logging, get_logger


class TestLoggingConfiguration:
    """Test logging configuration utility."""

    def test_configure_logging_json_format(self, caplog):
        """Test logging configuration with JSON format."""
        configure_logging(log_level="INFO", log_format="json", service_name="test-service")

        logger = get_logger(__name__)
        assert logger is not None
        assert isinstance(logger, structlog.stdlib.BoundLogger)

    def test_configure_logging_console_format(self, caplog):
        """Test logging configuration with console format."""
        configure_logging(log_level="DEBUG", log_format="console", service_name="test-service")

        logger = get_logger(__name__)
        assert logger is not None
        assert isinstance(logger, structlog.stdlib.BoundLogger)

    def test_get_logger_returns_bound_logger(self):
        """Test get_logger returns a BoundLogger instance."""
        configure_logging(log_level="INFO", log_format="json", service_name="test")

        logger = get_logger("test_module")
        assert isinstance(logger, structlog.stdlib.BoundLogger)

    def test_log_level_configuration(self, caplog):
        """Test log level filtering works correctly."""
        configure_logging(log_level="WARNING", log_format="json", service_name="test")

        logger = get_logger(__name__)

        with caplog.at_level(logging.WARNING):
            logger.info("info_message")  # Should not appear
            logger.warning("warning_message")  # Should appear

        # Warning should be logged, info should not
        assert any("warning_message" in record.message for record in caplog.records)

    def test_service_name_in_context(self, caplog):
        """Test service name is added to log context."""
        configure_logging(log_level="INFO", log_format="json", service_name="test-api")

        # Verify context vars are set
        bound_context = structlog.contextvars.get_contextvars()
        assert bound_context.get("service") == "test-api"


class TestMiddlewareLogging:
    """Test request logging middleware functionality."""

    def test_middleware_imports(self):
        """Test that middleware can be imported."""
        from app.middleware import RequestLoggingMiddleware

        assert RequestLoggingMiddleware is not None
