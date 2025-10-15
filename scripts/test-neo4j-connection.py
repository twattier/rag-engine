#!/usr/bin/env python3
"""
Neo4j connection test script for RAG Engine.
Tests basic connectivity, vector support, and CRUD operations.
"""

import os
import sys
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_AUTH = os.getenv("NEO4J_AUTH", "neo4j/password")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")


def parse_auth(auth_string):
    """Parse NEO4J_AUTH format (username/password)."""
    parts = auth_string.split("/")
    if len(parts) != 2:
        raise ValueError(f"Invalid NEO4J_AUTH format: {auth_string}. Expected 'username/password'")
    return tuple(parts)


def test_connection():
    """Test Neo4j connection and basic operations."""
    print(f"Testing connection to Neo4j at {NEO4J_URI}...")

    try:
        username, password = parse_auth(NEO4J_AUTH)
        driver = GraphDatabase.driver(NEO4J_URI, auth=(username, password))

        # Test 1: Basic connectivity
        print("✓ Connection established")

        with driver.session(database=NEO4J_DATABASE) as session:
            # Test 2: Simple query
            result = session.run("RETURN 1 AS test")
            record = result.single()
            assert record["test"] == 1
            print("✓ Simple query successful")

            # Test 3: Check Neo4j version
            result = session.run("CALL dbms.components() YIELD name, versions, edition RETURN name, versions, edition")
            for record in result:
                print(f"✓ Neo4j {record['name']}: {record['versions'][0]} ({record['edition']} edition)")

            # Test 4: Create test node with properties
            session.run("""
                CREATE (n:TestNode {
                    name: 'RAG Engine Test',
                    created_at: datetime(),
                    test_id: 'test-123'
                })
            """)
            print("✓ Test node created")

            # Test 5: Query test node
            result = session.run("""
                MATCH (n:TestNode {test_id: 'test-123'})
                RETURN n.name AS name, n.test_id AS id
            """)
            record = result.single()
            assert record["name"] == "RAG Engine Test"
            assert record["id"] == "test-123"
            print("✓ Test node queried successfully")

            # Test 6: Test vector property (Neo4j 5.x native vectors)
            # Note: Full vector index testing requires APOC or GDS plugins
            session.run("""
                MATCH (n:TestNode {test_id: 'test-123'})
                SET n.embedding = [0.1, 0.2, 0.3, 0.4, 0.5]
            """)
            print("✓ Vector property set successfully")

            # Test 7: Delete test node
            result = session.run("""
                MATCH (n:TestNode {test_id: 'test-123'})
                DELETE n
                RETURN count(n) AS deleted_count
            """)
            record = result.single()
            assert record["deleted_count"] == 1
            print("✓ Test node deleted")

        driver.close()
        print("\n✅ All Neo4j tests passed!")
        print("\nNeo4j is ready for RAG Engine deployment.")
        return 0

    except Exception as e:
        print(f"\n❌ Neo4j connection test failed: {e}")
        print("\nTroubleshooting steps:")
        print("1. Check that Neo4j container is running: docker ps | grep neo4j")
        print("2. Check Neo4j logs: docker logs rag-engine-neo4j")
        print("3. Verify credentials in .env file match NEO4J_AUTH")
        print("4. Verify ports are not blocked by firewall")
        return 1


if __name__ == "__main__":
    sys.exit(test_connection())
