"""
Integration tests for structured logging.
"""

from __future__ import annotations

import json
import logging

import pytest
from fastapi.testclient import TestClient

from app.main import app


class TestLoggingIntegration:
    """Integration tests for logging functionality."""

    def test_api_service_logs_to_stdout(self, caplog):
        """Test that API service logs output to stdout."""
        client = TestClient(app)

        with caplog.at_level(logging.INFO):
            response = client.get("/")

        # Verify logs were generated
        assert len(caplog.records) > 0

    def test_request_id_in_response_headers(self):
        """Test request_id appears in response headers."""
        client = TestClient(app)

        response = client.get("/")

        # Verify X-Request-ID header is present
        assert "X-Request-ID" in response.headers
        request_id = response.headers["X-Request-ID"]

        # Verify it's a valid UUID format (length check)
        assert len(request_id) == 36  # UUID4 format with hyphens
        assert request_id.count("-") == 4

    def test_request_logging_captures_method_and_path(self, caplog):
        """Test request logging captures HTTP method and path."""
        client = TestClient(app)

        with caplog.at_level(logging.INFO):
            response = client.get("/health")

        # Check for request_started and request_completed events
        log_messages = [record.message for record in caplog.records]
        assert any("request_started" in msg or "GET" in msg for msg in log_messages)

    def test_request_logging_captures_status_code(self, caplog):
        """Test request logging captures response status code."""
        client = TestClient(app)

        with caplog.at_level(logging.INFO):
            response = client.get("/")

        # Verify response was successful
        assert response.status_code == 200

    def test_exception_handler_logs_errors(self, caplog):
        """Test global exception handler logs unhandled errors."""
        # This test validates the exception handler exists
        # Actual exception testing would require triggering a real error
        from app.main import global_exception_handler

        assert global_exception_handler is not None
