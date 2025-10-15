"""
Unit tests for Neo4j client connection manager.
"""

from __future__ import annotations

import pytest
from unittest.mock import Mock, patch, MagicMock
from neo4j.exceptions import ServiceUnavailable, AuthError

from shared.utils.neo4j_client import Neo4jClient, parse_neo4j_auth


class TestParseNeo4jAuth:
    """Tests for Neo4j auth string parsing."""

    def test_parse_valid_auth_string(self):
        """Test parsing valid auth string."""
        username, password = parse_neo4j_auth("neo4j/password123")
        assert username == "neo4j"
        assert password == "password123"

    def test_parse_auth_with_special_chars(self):
        """Test parsing auth with special characters in password."""
        username, password = parse_neo4j_auth("admin/P@ssw0rd!")
        assert username == "admin"
        assert password == "P@ssw0rd!"

    def test_parse_invalid_auth_no_separator(self):
        """Test parsing invalid auth string without separator."""
        with pytest.raises(ValueError) as exc_info:
            parse_neo4j_auth("neo4jpassword")
        assert "Invalid NEO4J_AUTH format" in str(exc_info.value)

    def test_parse_invalid_auth_multiple_separators(self):
        """Test parsing auth string with multiple separators."""
        with pytest.raises(ValueError) as exc_info:
            parse_neo4j_auth("neo4j/pass/word")
        assert "Invalid NEO4J_AUTH format" in str(exc_info.value)

    def test_parse_empty_auth_string(self):
        """Test parsing empty auth string."""
        # "/" splits into two empty strings, which is technically valid format
        # but probably not useful in practice
        username, password = parse_neo4j_auth("/")
        assert username == ""
        assert password == ""


class TestNeo4jClient:
    """Tests for Neo4jClient class."""

    @pytest.fixture
    def mock_driver(self):
        """Create mock Neo4j driver."""
        driver = Mock()
        driver.close = Mock()
        return driver

    @pytest.fixture
    def mock_session(self):
        """Create mock Neo4j session."""
        session = Mock()
        session.close = Mock()
        return session

    @pytest.fixture
    def client(self):
        """Create Neo4jClient instance for testing."""
        return Neo4jClient(
            uri="bolt://localhost:7687",
            auth=("neo4j", "password"),
            database="neo4j",
        )

    def test_client_initialization(self, client):
        """Test Neo4j client initialization."""
        assert client.uri == "bolt://localhost:7687"
        assert client.auth == ("neo4j", "password")
        assert client.database == "neo4j"
        assert client.max_connection_pool_size == 50
        assert client.connection_timeout == 5.0
        assert client._driver is None

    @patch("shared.utils.neo4j_client.GraphDatabase.driver")
    def test_connect_creates_driver(self, mock_graph_database, client, mock_driver):
        """Test that connect creates a driver instance."""
        mock_graph_database.return_value = mock_driver

        driver = client.connect()

        assert driver == mock_driver
        mock_graph_database.assert_called_once_with(
            "bolt://localhost:7687",
            auth=("neo4j", "password"),
            max_connection_pool_size=50,
            connection_timeout=5.0,
        )

    @patch("shared.utils.neo4j_client.GraphDatabase.driver")
    def test_connect_reuses_existing_driver(self, mock_graph_database, client, mock_driver):
        """Test that connect reuses existing driver."""
        mock_graph_database.return_value = mock_driver

        driver1 = client.connect()
        driver2 = client.connect()

        assert driver1 == driver2
        # Should only be called once
        assert mock_graph_database.call_count == 1

    @patch("shared.utils.neo4j_client.GraphDatabase.driver")
    def test_connect_handles_service_unavailable(self, mock_graph_database, client):
        """Test connect handles ServiceUnavailable exception."""
        mock_graph_database.side_effect = ServiceUnavailable("Cannot connect")

        with pytest.raises(ServiceUnavailable):
            client.connect()

    @patch("shared.utils.neo4j_client.GraphDatabase.driver")
    def test_connect_handles_auth_error(self, mock_graph_database, client):
        """Test connect handles AuthError exception."""
        mock_graph_database.side_effect = AuthError("Invalid credentials")

        with pytest.raises(AuthError):
            client.connect()

    def test_close_driver(self, client, mock_driver):
        """Test closing the driver."""
        client._driver = mock_driver

        client.close()

        mock_driver.close.assert_called_once()
        assert client._driver is None

    def test_close_when_no_driver(self, client):
        """Test close when no driver exists."""
        # Should not raise exception
        client.close()
        assert client._driver is None

    @patch("shared.utils.neo4j_client.GraphDatabase.driver")
    def test_session_context_manager(self, mock_graph_database, client, mock_driver, mock_session):
        """Test session context manager."""
        mock_graph_database.return_value = mock_driver
        mock_driver.session.return_value = mock_session

        with client.session() as session:
            assert session == mock_session

        mock_driver.session.assert_called_once_with(database="neo4j")
        mock_session.close.assert_called_once()

    @patch("shared.utils.neo4j_client.GraphDatabase.driver")
    def test_verify_connectivity_success(self, mock_graph_database, client, mock_driver, mock_session):
        """Test successful connectivity verification."""
        mock_graph_database.return_value = mock_driver
        mock_driver.session.return_value = mock_session

        # Mock query result
        mock_result = Mock()
        mock_record = Mock()
        mock_record.__getitem__ = Mock(return_value=1)
        mock_result.single.return_value = mock_record
        mock_session.run.return_value = mock_result
        mock_session.__enter__ = Mock(return_value=mock_session)
        mock_session.__exit__ = Mock(return_value=None)

        success, response_time_ms, error_msg = client.verify_connectivity(retries=1)

        assert success is True
        assert response_time_ms is not None
        assert response_time_ms > 0
        assert error_msg is None
        mock_session.run.assert_called_once_with("RETURN 1 AS test")

    @patch("shared.utils.neo4j_client.GraphDatabase.driver")
    @patch("shared.utils.neo4j_client.time.sleep")
    def test_verify_connectivity_retry_logic(self, mock_sleep, mock_graph_database, client, mock_driver, mock_session):
        """Test connectivity verification retry logic with exponential backoff."""
        mock_graph_database.return_value = mock_driver
        mock_driver.session.return_value = mock_session
        mock_session.__enter__ = Mock(return_value=mock_session)
        mock_session.__exit__ = Mock(return_value=None)

        # Fail twice, then succeed
        mock_session.run.side_effect = [
            ServiceUnavailable("Connection failed"),
            ServiceUnavailable("Connection failed"),
            Mock(single=Mock(return_value=Mock(__getitem__=Mock(return_value=1)))),
        ]

        success, response_time_ms, error_msg = client.verify_connectivity(retries=3)

        assert success is True
        assert mock_sleep.call_count == 2  # Called for first two failures
        # Check exponential backoff: 2^0=1, 2^1=2
        mock_sleep.assert_any_call(1)
        mock_sleep.assert_any_call(2)

    @patch("shared.utils.neo4j_client.GraphDatabase.driver")
    @patch("shared.utils.neo4j_client.time.sleep")
    def test_verify_connectivity_all_retries_fail(self, mock_sleep, mock_graph_database, client, mock_driver, mock_session):
        """Test connectivity verification when all retries fail."""
        mock_graph_database.return_value = mock_driver
        mock_driver.session.return_value = mock_session
        mock_session.__enter__ = Mock(return_value=mock_session)
        mock_session.__exit__ = Mock(return_value=None)

        mock_session.run.side_effect = ServiceUnavailable("Connection failed")

        success, response_time_ms, error_msg = client.verify_connectivity(retries=3)

        assert success is False
        assert response_time_ms is None
        assert error_msg is not None
        assert "ServiceUnavailable" in error_msg
        assert mock_sleep.call_count == 2  # No sleep after last attempt

    @patch("shared.utils.neo4j_client.GraphDatabase.driver")
    def test_execute_query_success(self, mock_graph_database, client, mock_driver, mock_session):
        """Test successful query execution."""
        mock_graph_database.return_value = mock_driver
        mock_driver.session.return_value = mock_session
        mock_session.__enter__ = Mock(return_value=mock_session)
        mock_session.__exit__ = Mock(return_value=None)

        # Mock query results
        mock_record1 = {"id": 1, "name": "Alice"}
        mock_record2 = {"id": 2, "name": "Bob"}
        mock_result = [mock_record1, mock_record2]
        mock_session.run.return_value = mock_result

        results = client.execute_query("MATCH (n) RETURN n", {"limit": 10})

        assert results == mock_result
        mock_session.run.assert_called_once_with("MATCH (n) RETURN n", {"limit": 10})

    @patch("shared.utils.neo4j_client.GraphDatabase.driver")
    def test_execute_query_no_parameters(self, mock_graph_database, client, mock_driver, mock_session):
        """Test query execution without parameters."""
        mock_graph_database.return_value = mock_driver
        mock_driver.session.return_value = mock_session
        mock_session.__enter__ = Mock(return_value=mock_session)
        mock_session.__exit__ = Mock(return_value=None)

        mock_result = []
        mock_session.run.return_value = mock_result

        results = client.execute_query("RETURN 1")

        assert results == mock_result
        mock_session.run.assert_called_once_with("RETURN 1", {})

    @patch("shared.utils.neo4j_client.GraphDatabase.driver")
    def test_execute_query_service_unavailable(self, mock_graph_database, client, mock_driver, mock_session):
        """Test query execution when Neo4j is unavailable."""
        mock_graph_database.return_value = mock_driver
        mock_driver.session.return_value = mock_session
        mock_session.__enter__ = Mock(return_value=mock_session)
        mock_session.__exit__ = Mock(return_value=None)

        mock_session.run.side_effect = ServiceUnavailable("Connection lost")

        with pytest.raises(ServiceUnavailable):
            client.execute_query("RETURN 1")
