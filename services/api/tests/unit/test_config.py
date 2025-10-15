"""
Unit tests for configuration module.
"""

from __future__ import annotations

import pytest
import os

from app.config import Settings


def test_settings_default_values():
    """Test that Settings has correct default values."""
    settings = Settings()

    assert settings.APP_NAME == "RAG Engine API"
    assert settings.VERSION == "0.1.0"
    assert settings.API_PORT == 8000
    assert settings.API_WORKERS == 1
    assert settings.LOG_LEVEL == "INFO"
    assert settings.LOG_FORMAT == "json"


def test_settings_cors_origins_parsing():
    """Test that CORS origins string is parsed correctly to list."""
    settings = Settings(CORS_ORIGINS="http://localhost:3000,http://localhost:8080")

    origins_list = settings.get_cors_origins_list()
    assert isinstance(origins_list, list)
    assert len(origins_list) == 2
    assert "http://localhost:3000" in origins_list
    assert "http://localhost:8080" in origins_list


def test_settings_cors_origins_parsing_with_spaces():
    """Test that CORS origins parsing handles spaces correctly."""
    settings = Settings(CORS_ORIGINS="http://localhost:3000, http://localhost:8080 , http://example.com")

    origins_list = settings.get_cors_origins_list()
    assert len(origins_list) == 3
    assert "http://localhost:3000" in origins_list
    assert "http://localhost:8080" in origins_list
    assert "http://example.com" in origins_list


def test_settings_cors_origins_single_value():
    """Test that CORS origins parsing handles single value."""
    settings = Settings(CORS_ORIGINS="http://localhost:3000")

    origins_list = settings.get_cors_origins_list()
    assert isinstance(origins_list, list)
    assert len(origins_list) == 1
    assert origins_list[0] == "http://localhost:3000"


def test_settings_environment_variable_override(monkeypatch):
    """Test that environment variables override default settings."""
    monkeypatch.setenv("API_PORT", "9000")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("NEO4J_URI", "bolt://custom:7687")

    settings = Settings()

    assert settings.API_PORT == 9000
    assert settings.LOG_LEVEL == "DEBUG"
    assert settings.NEO4J_URI == "bolt://custom:7687"


def test_settings_neo4j_configuration():
    """Test Neo4j configuration defaults."""
    settings = Settings()

    assert settings.NEO4J_URI == "bolt://neo4j:7687"
    assert settings.NEO4J_AUTH == "neo4j/password"
    assert settings.NEO4J_DATABASE == "neo4j"


def test_settings_api_key_default():
    """Test API key has secure default placeholder."""
    settings = Settings()

    assert settings.API_KEY == "change-me-in-production"
    # Ensure it's not empty or None
    assert len(settings.API_KEY) > 0


def test_settings_request_configuration():
    """Test request configuration defaults."""
    settings = Settings()

    assert settings.REQUEST_TIMEOUT == 120
    assert settings.MAX_CONCURRENT_REQUESTS == 10
    assert settings.RATE_LIMIT_PER_MINUTE == 100
