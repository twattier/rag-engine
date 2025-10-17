"""Integration tests for relationship mapping and graph construction."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_graph_stats_endpoint():
    """Test graph statistics endpoint returns valid response."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/graph/stats")

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "totalEntities" in data
        assert "totalRelationships" in data
        assert "entityTypeDistribution" in data
        assert "relationshipTypeDistribution" in data
        assert "totalDocuments" in data
        assert "crossDocumentEntities" in data

        # Verify types
        assert isinstance(data["totalEntities"], int)
        assert isinstance(data["totalRelationships"], int)
        assert isinstance(data["entityTypeDistribution"], dict)
        assert isinstance(data["relationshipTypeDistribution"], dict)
        assert isinstance(data["totalDocuments"], int)
        assert isinstance(data["crossDocumentEntities"], int)
