"""
Unit tests for dependencies module.
"""

from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.dependencies import verify_api_key
from app.config import settings


@pytest.mark.asyncio
async def test_verify_api_key_valid():
    """Test verify_api_key with valid Bearer token."""
    valid_token = f"Bearer {settings.API_KEY}"

    result = await verify_api_key(authorization=valid_token)
    assert result == settings.API_KEY


@pytest.mark.asyncio
async def test_verify_api_key_missing_header():
    """Test verify_api_key raises 401 when Authorization header is missing."""
    with pytest.raises(HTTPException) as exc_info:
        await verify_api_key(authorization=None)

    assert exc_info.value.status_code == 401
    assert "Missing Authorization header" in exc_info.value.detail


@pytest.mark.asyncio
async def test_verify_api_key_invalid_format():
    """Test verify_api_key raises 401 for invalid header format."""
    with pytest.raises(HTTPException) as exc_info:
        await verify_api_key(authorization="InvalidFormat")

    assert exc_info.value.status_code == 401
    assert "Invalid Authorization header format" in exc_info.value.detail


@pytest.mark.asyncio
async def test_verify_api_key_missing_bearer_prefix():
    """Test verify_api_key raises 401 when Bearer prefix is missing."""
    with pytest.raises(HTTPException) as exc_info:
        await verify_api_key(authorization=settings.API_KEY)

    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_verify_api_key_wrong_key():
    """Test verify_api_key raises 401 for incorrect API key."""
    with pytest.raises(HTTPException) as exc_info:
        await verify_api_key(authorization="Bearer wrong-api-key")

    assert exc_info.value.status_code == 401
    assert "Invalid API key" in exc_info.value.detail


@pytest.mark.asyncio
async def test_verify_api_key_case_insensitive_bearer():
    """Test verify_api_key accepts 'bearer' in any case."""
    valid_token_lower = f"bearer {settings.API_KEY}"

    result = await verify_api_key(authorization=valid_token_lower)
    assert result == settings.API_KEY
