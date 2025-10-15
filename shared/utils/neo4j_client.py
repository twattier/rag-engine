"""
Neo4j connection manager with connection pooling and retry logic.
"""

import time
from typing import Optional, Any
from contextlib import contextmanager
from neo4j import GraphDatabase, Driver, Session
from neo4j.exceptions import ServiceUnavailable, AuthError
import structlog

logger = structlog.get_logger(__name__)


class Neo4jClient:
    """
    Neo4j connection manager with connection pooling and error handling.
    """

    def __init__(
        self,
        uri: str,
        auth: tuple[str, str],
        database: str = "neo4j",
        max_connection_pool_size: int = 50,
        connection_timeout: float = 5.0,
    ):
        """
        Initialize Neo4j client.

        Args:
            uri: Neo4j connection URI (e.g., "bolt://localhost:7687")
            auth: Tuple of (username, password)
            database: Database name
            max_connection_pool_size: Maximum connection pool size
            connection_timeout: Connection timeout in seconds
        """
        self.uri = uri
        self.auth = auth
        self.database = database
        self.max_connection_pool_size = max_connection_pool_size
        self.connection_timeout = connection_timeout
        self._driver: Optional[Driver] = None

        logger.info(
            "neo4j_client_initialized",
            uri=uri,
            database=database,
        )

    def connect(self) -> Driver:
        """
        Create Neo4j driver with connection pooling.

        Returns:
            Neo4j driver instance

        Raises:
            ServiceUnavailable: If Neo4j is not reachable
            AuthError: If authentication fails
        """
        if self._driver is None:
            try:
                self._driver = GraphDatabase.driver(
                    self.uri,
                    auth=self.auth,
                    max_connection_pool_size=self.max_connection_pool_size,
                    connection_timeout=self.connection_timeout,
                )
                logger.info("neo4j_driver_connected", uri=self.uri)
            except (ServiceUnavailable, AuthError) as e:
                logger.error(
                    "neo4j_connection_failed",
                    uri=self.uri,
                    error=str(e),
                    error_type=type(e).__name__,
                )
                raise

        return self._driver

    def close(self):
        """Close Neo4j driver and connection pool."""
        if self._driver is not None:
            self._driver.close()
            self._driver = None
            logger.info("neo4j_driver_closed", uri=self.uri)

    @contextmanager
    def session(self) -> Session:
        """
        Context manager for Neo4j session.

        Yields:
            Neo4j session

        Example:
            ```python
            with client.session() as session:
                result = session.run("RETURN 1 AS num")
                print(result.single()["num"])
            ```
        """
        driver = self.connect()
        session = driver.session(database=self.database)
        try:
            yield session
        finally:
            session.close()

    def verify_connectivity(self, retries: int = 3) -> tuple[bool, Optional[float], Optional[str]]:
        """
        Verify Neo4j connectivity with retry logic.

        Args:
            retries: Number of connection attempts

        Returns:
            Tuple of (success, response_time_ms, error_message)
        """
        for attempt in range(retries):
            try:
                start_time = time.time()

                with self.session() as session:
                    result = session.run("RETURN 1 AS test")
                    record = result.single()
                    assert record["test"] == 1

                response_time_ms = (time.time() - start_time) * 1000

                logger.info(
                    "neo4j_connectivity_verified",
                    response_time_ms=response_time_ms,
                    attempt=attempt + 1,
                )

                return True, response_time_ms, None

            except (ServiceUnavailable, AuthError, Exception) as e:
                error_msg = f"{type(e).__name__}: {str(e)}"

                if attempt < retries - 1:
                    # Exponential backoff: 1s, 2s, 4s
                    wait_time = 2 ** attempt
                    logger.warning(
                        "neo4j_connectivity_check_failed_retrying",
                        attempt=attempt + 1,
                        retries=retries,
                        wait_time=wait_time,
                        error=error_msg,
                    )
                    time.sleep(wait_time)
                else:
                    logger.error(
                        "neo4j_connectivity_check_failed",
                        attempts=retries,
                        error=error_msg,
                    )
                    return False, None, error_msg

        return False, None, "Max retries exceeded"

    def execute_query(self, query: str, parameters: dict[str, Any] = None) -> list[dict]:
        """
        Execute Cypher query and return results.

        Args:
            query: Cypher query string
            parameters: Query parameters

        Returns:
            List of result records as dictionaries

        Raises:
            ServiceUnavailable: If Neo4j is not reachable
        """
        with self.session() as session:
            result = session.run(query, parameters or {})
            return [dict(record) for record in result]


def parse_neo4j_auth(auth_string: str) -> tuple[str, str]:
    """
    Parse NEO4J_AUTH environment variable format.

    Args:
        auth_string: Auth string in format "username/password"

    Returns:
        Tuple of (username, password)

    Raises:
        ValueError: If auth string format is invalid
    """
    parts = auth_string.split("/")
    if len(parts) != 2:
        raise ValueError(
            f"Invalid NEO4J_AUTH format: {auth_string}. Expected 'username/password'"
        )
    return tuple(parts)
