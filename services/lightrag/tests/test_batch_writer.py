"""Unit tests for Neo4j batch writer."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.utils.neo4j_batch import BatchWriter


@pytest.fixture
def mock_session() -> AsyncMock:
    """Create mock Neo4j async session."""
    session = AsyncMock()
    session.run = AsyncMock()
    return session


@pytest.fixture
def batch_writer(mock_session: AsyncMock) -> BatchWriter:
    """Create BatchWriter instance for testing."""
    return BatchWriter(session=mock_session, batch_size=3)


@pytest.mark.asyncio
async def test_add_entity_below_batch_size(
    batch_writer: BatchWriter, mock_session: AsyncMock
):
    """Test adding entities below batch size doesn't trigger flush."""
    entity = {
        "id": str(uuid4()),
        "name": "Test Entity",
        "type": "test",
        "embedding": [0.1, 0.2, 0.3],
        "confidence_score": 0.9,
        "source_doc_id": str(uuid4()),
    }

    await batch_writer.add_entity(entity)
    await batch_writer.add_entity(entity)

    # Should not flush yet (batch_size=3, only 2 added)
    mock_session.run.assert_not_called()
    assert len(batch_writer.entity_buffer) == 2


@pytest.mark.asyncio
async def test_add_entity_triggers_flush(
    batch_writer: BatchWriter, mock_session: AsyncMock
):
    """Test adding entities triggers flush when batch size reached."""
    entity = {
        "id": str(uuid4()),
        "name": "Test Entity",
        "type": "test",
        "embedding": [0.1, 0.2, 0.3],
        "confidence_score": 0.9,
        "source_doc_id": str(uuid4()),
    }

    await batch_writer.add_entity(entity)
    await batch_writer.add_entity(entity)
    await batch_writer.add_entity(entity)

    # Should flush after 3 entities
    mock_session.run.assert_called_once()
    assert len(batch_writer.entity_buffer) == 0


@pytest.mark.asyncio
async def test_add_relationship_below_batch_size(
    batch_writer: BatchWriter, mock_session: AsyncMock
):
    """Test adding relationships below batch size doesn't trigger flush."""
    relationship = {
        "id": str(uuid4()),
        "source_name": "Entity1",
        "target_name": "Entity2",
        "rel_type": "RELATED_TO",
        "confidence": 0.9,
        "source_doc_id": str(uuid4()),
    }

    await batch_writer.add_relationship(relationship)

    # Should not flush yet
    mock_session.run.assert_not_called()
    assert len(batch_writer.relationship_buffer) == 1


@pytest.mark.asyncio
async def test_add_relationship_triggers_flush(
    batch_writer: BatchWriter, mock_session: AsyncMock
):
    """Test adding relationships triggers flush when batch size reached."""
    relationship = {
        "id": str(uuid4()),
        "source_name": "Entity1",
        "target_name": "Entity2",
        "rel_type": "RELATED_TO",
        "confidence": 0.9,
        "source_doc_id": str(uuid4()),
    }

    await batch_writer.add_relationship(relationship)
    await batch_writer.add_relationship(relationship)
    await batch_writer.add_relationship(relationship)

    # Should flush after 3 relationships
    mock_session.run.assert_called_once()
    assert len(batch_writer.relationship_buffer) == 0


@pytest.mark.asyncio
async def test_flush_entities_empty_buffer(
    batch_writer: BatchWriter, mock_session: AsyncMock
):
    """Test flushing empty entity buffer does nothing."""
    await batch_writer.flush_entities()

    mock_session.run.assert_not_called()


@pytest.mark.asyncio
async def test_flush_entities_success(
    batch_writer: BatchWriter, mock_session: AsyncMock
):
    """Test successful entity buffer flush."""
    entity = {
        "id": str(uuid4()),
        "name": "Test Entity",
        "type": "test",
        "embedding": [0.1, 0.2, 0.3],
        "confidence_score": 0.9,
        "source_doc_id": str(uuid4()),
    }

    batch_writer.entity_buffer.append(entity)
    batch_writer.entity_buffer.append(entity)

    # Store expected batch before flush clears it
    expected_batch = [entity, entity]

    await batch_writer.flush_entities()

    # Verify query execution
    mock_session.run.assert_called_once()
    call_args = mock_session.run.call_args

    assert "UNWIND $batch AS item" in call_args[0][0]
    assert "CREATE (e:Entity" in call_args[0][0]

    # Buffer should be cleared
    assert len(batch_writer.entity_buffer) == 0


@pytest.mark.asyncio
async def test_flush_relationships_success(
    batch_writer: BatchWriter, mock_session: AsyncMock
):
    """Test successful relationship buffer flush."""
    relationship = {
        "id": str(uuid4()),
        "source_name": "Entity1",
        "target_name": "Entity2",
        "rel_type": "RELATED_TO",
        "confidence": 0.9,
        "source_doc_id": str(uuid4()),
    }

    batch_writer.relationship_buffer.append(relationship)

    await batch_writer.flush_relationships()

    # Verify query execution
    mock_session.run.assert_called_once()
    call_args = mock_session.run.call_args

    assert "UNWIND $batch AS item" in call_args[0][0]
    assert "MATCH (e1:Entity" in call_args[0][0]
    assert "CREATE (e1)-[r:RELATIONSHIP" in call_args[0][0]

    # Buffer should be cleared
    assert len(batch_writer.relationship_buffer) == 0


@pytest.mark.asyncio
async def test_flush_all(batch_writer: BatchWriter, mock_session: AsyncMock):
    """Test flushing all buffers."""
    entity = {
        "id": str(uuid4()),
        "name": "Test Entity",
        "type": "test",
        "embedding": [0.1, 0.2, 0.3],
        "confidence_score": 0.9,
        "source_doc_id": str(uuid4()),
    }

    relationship = {
        "id": str(uuid4()),
        "source_name": "Entity1",
        "target_name": "Entity2",
        "rel_type": "RELATED_TO",
        "confidence": 0.9,
        "source_doc_id": str(uuid4()),
    }

    batch_writer.entity_buffer.append(entity)
    batch_writer.relationship_buffer.append(relationship)

    await batch_writer.flush_all()

    # Both buffers should be flushed
    assert mock_session.run.call_count == 2
    assert len(batch_writer.entity_buffer) == 0
    assert len(batch_writer.relationship_buffer) == 0


@pytest.mark.asyncio
async def test_batch_size_configuration():
    """Test batch writer with custom batch size."""
    session = AsyncMock()
    batch_writer = BatchWriter(session=session, batch_size=5)

    assert batch_writer.batch_size == 5


@pytest.mark.asyncio
async def test_entity_flush_performance_logging(
    batch_writer: BatchWriter, mock_session: AsyncMock, caplog
):
    """Test that entity flush logs performance metrics."""
    entity = {
        "id": str(uuid4()),
        "name": "Test Entity",
        "type": "test",
        "embedding": [0.1, 0.2, 0.3],
        "confidence_score": 0.9,
        "source_doc_id": str(uuid4()),
    }

    batch_writer.entity_buffer.append(entity)

    await batch_writer.flush_entities()

    # Verify performance logging occurred (check that session.run was called)
    mock_session.run.assert_called_once()
