#!/usr/bin/env python3
"""
Validation script for entity extraction.

This script queries Neo4j to validate entity extraction results:
- Count entities by type
- Find orphan entities (not linked to documents)
- Show entity distribution per document
- Output validation report
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from typing import Any, Dict, List

from neo4j import AsyncGraphDatabase, AsyncDriver


async def get_entities_by_type(driver: AsyncDriver, database: str) -> List[Dict[str, Any]]:
    """Count entities by type.

    Returns:
        List of dicts with type and count
    """
    query = """
    MATCH (e:Entity)
    RETURN e.type AS type, count(e) AS count
    ORDER BY count DESC
    """

    async with driver.session(database=database) as session:
        result = await session.run(query)
        records = await result.data()
        return records


async def get_orphan_entities(driver: AsyncDriver, database: str) -> List[Dict[str, Any]]:
    """Find orphan entities not linked to documents.

    Returns:
        List of dicts with entity id, name, type
    """
    query = """
    MATCH (e:Entity)
    WHERE NOT (e)<-[:CONTAINS]-()
    RETURN e.id AS id, e.name AS name, e.type AS type
    """

    async with driver.session(database=database) as session:
        result = await session.run(query)
        records = await result.data()
        return records


async def get_entity_distribution_per_document(
    driver: AsyncDriver, database: str
) -> List[Dict[str, Any]]:
    """Get entity count per document.

    Returns:
        List of dicts with document id and entity count
    """
    query = """
    MATCH (d:Document)-[:CONTAINS]->(e:Entity)
    RETURN d.id AS doc_id, count(e) AS entity_count
    ORDER BY entity_count DESC
    """

    async with driver.session(database=database) as session:
        result = await session.run(query)
        records = await result.data()
        return records


async def get_total_entities(driver: AsyncDriver, database: str) -> int:
    """Get total entity count.

    Returns:
        Total number of entities
    """
    query = """
    MATCH (e:Entity)
    RETURN count(e) AS total
    """

    async with driver.session(database=database) as session:
        result = await session.run(query)
        record = await result.single()
        return record["total"] if record else 0


async def validate_entity_extraction(
    neo4j_uri: str, neo4j_auth: str, neo4j_database: str
) -> None:
    """Run validation queries and output report.

    Args:
        neo4j_uri: Neo4j connection URI
        neo4j_auth: Neo4j authentication (username/password)
        neo4j_database: Database name
    """
    # Parse auth
    username, password = neo4j_auth.split("/")

    # Connect to Neo4j
    driver = AsyncGraphDatabase.driver(neo4j_uri, auth=(username, password))

    try:
        # Get validation data
        entities_by_type = await get_entities_by_type(driver, neo4j_database)
        total_entities = await get_total_entities(driver, neo4j_database)
        orphan_entities = await get_orphan_entities(driver, neo4j_database)
        entity_distribution = await get_entity_distribution_per_document(
            driver, neo4j_database
        )

        # Print validation report
        print("=" * 80)
        print("ENTITY EXTRACTION VALIDATION REPORT")
        print("=" * 80)
        print()

        # Total entities
        print(f"📊 Total Entities: {total_entities}")
        print()

        # Entities by type
        print("📋 Entities by Type:")
        if entities_by_type:
            for record in entities_by_type:
                print(f"  - {record['type']}: {record['count']}")
        else:
            print("  (No entities found)")
        print()

        # Orphan entities
        print(f"⚠️  Orphan Entities (not linked to documents): {len(orphan_entities)}")
        if orphan_entities:
            print("  Orphan entities found:")
            for entity in orphan_entities[:10]:  # Show first 10
                print(f"    - {entity['name']} ({entity['type']}) [ID: {entity['id']}]")
            if len(orphan_entities) > 10:
                print(f"    ... and {len(orphan_entities) - 10} more")
        print()

        # Entity distribution
        print(f"📄 Entity Distribution Per Document (Top 10):")
        if entity_distribution:
            for record in entity_distribution[:10]:
                print(f"  - Document {record['doc_id']}: {record['entity_count']} entities")
        else:
            print("  (No documents with entities found)")
        print()

        # Summary
        print("=" * 80)
        print("SUMMARY")
        print("=" * 80)
        print(f"✓ Total Entities: {total_entities}")
        print(f"✓ Entity Types: {len(entities_by_type)}")
        print(f"✓ Documents with Entities: {len(entity_distribution)}")

        if orphan_entities:
            print(f"⚠️  WARNING: {len(orphan_entities)} orphan entities found!")
            print("   These entities are not linked to any document.")
        else:
            print("✓ No orphan entities")

        print("=" * 80)

    finally:
        await driver.close()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate entity extraction in Neo4j"
    )
    parser.add_argument(
        "--uri",
        default="bolt://localhost:7687",
        help="Neo4j URI (default: bolt://localhost:7687)",
    )
    parser.add_argument(
        "--auth",
        default="neo4j/password",
        help="Neo4j auth (username/password, default: neo4j/password)",
    )
    parser.add_argument(
        "--database",
        default="neo4j",
        help="Neo4j database name (default: neo4j)",
    )

    args = parser.parse_args()

    try:
        asyncio.run(
            validate_entity_extraction(args.uri, args.auth, args.database)
        )
    except KeyboardInterrupt:
        print("\n\nValidation interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
