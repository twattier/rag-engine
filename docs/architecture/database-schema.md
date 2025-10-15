# Database Schema

## Neo4j Graph Schema

Neo4j uses a property graph model with labeled nodes and typed relationships. The schema is dynamically created by LightRAG during document ingestion.

**Node Labels:**

```cypher
// Document node
(:Document {
  doc_id: STRING,              // Unique document ID
  file_path: STRING,           // Original file path
  content_type: STRING,        // MIME type
  status: STRING,              // processing status
  metadata: MAP,               // Custom metadata (JSON)
  created_at: DATETIME,
  updated_at: DATETIME,
  chunk_count: INTEGER,
  entity_count: INTEGER,
  error_message: STRING        // nullable
})

// Text chunk node
(:TextChunk {
  chunk_id: STRING,            // Unique chunk ID
  doc_id: STRING,              // Parent document
  content: STRING,             // Text content
  chunk_index: INTEGER,        // Position in document
  token_count: INTEGER,
  metadata: MAP,               // Page number, section, etc.
  created_at: DATETIME
})

// Entity node (LightRAG)
(:Entity {
  entity_name: STRING,         // Canonical name (unique)
  entity_type: STRING,         // Category (person, org, concept)
  description: STRING,         // LLM-generated description
  source_ids: LIST<STRING>,    // Document IDs
  metadata: MAP,               // Entity-specific metadata
  created_at: DATETIME,
  updated_at: DATETIME
})
```

**Relationship Types:**

```cypher
// Document to Chunks
(:Document)-[:HAS_CHUNK]->(:TextChunk)

// Entity to Documents (provenance)
(:Entity)-[:MENTIONED_IN {
  source_id: STRING,           // Document ID
  created_at: DATETIME
}]->(:Document)

// Entity to Entity (knowledge graph)
(:Entity)-[:RELATED_TO {
  relationship_type: STRING,   // Description of relationship
  description: STRING,         // LLM-generated summary
  keywords: STRING,            // Keywords
  weight: FLOAT,               // Strength (0.0-1.0)
  source_ids: LIST<STRING>,    // Supporting documents
  created_at: DATETIME,
  updated_at: DATETIME
}]->(:Entity)

// Chunk to Entities
(:TextChunk)-[:CONTAINS]->(:Entity)

// Chunk sequence (optional)
(:TextChunk)-[:NEXT_CHUNK]->(:TextChunk)
```

**Vector Indexes:**

```cypher
// Vector index for entity embeddings
CREATE VECTOR INDEX entity_embeddings FOR (e:Entity) ON (e.embedding)
OPTIONS {indexConfig: {
  `vector.dimensions`: 384,        // For all-MiniLM-L6-v2 (MVP)
  // `vector.dimensions`: 3072,    // For text-embedding-3-large (optional)
  `vector.similarity_function`: 'cosine'
}}

// Vector index for relationship embeddings
CREATE VECTOR INDEX relationship_embeddings FOR ()-[r:RELATED_TO]->() ON (r.embedding)
OPTIONS {indexConfig: {
  `vector.dimensions`: 384,
  `vector.similarity_function`: 'cosine'
}}

// Vector index for chunk embeddings
CREATE VECTOR INDEX chunk_embeddings FOR (c:TextChunk) ON (c.embedding)
OPTIONS {indexConfig: {
  `vector.dimensions`: 384,
  `vector.similarity_function`: 'cosine'
}}
```

**Performance Indexes:**

```cypher
// Unique constraint and index for document lookup
CREATE CONSTRAINT doc_id_unique FOR (d:Document) REQUIRE d.doc_id IS UNIQUE;

// Unique constraint for entity names
CREATE CONSTRAINT entity_name_unique FOR (e:Entity) REQUIRE e.entity_name IS UNIQUE;

// Index for chunk lookups by document
CREATE INDEX chunk_doc_id FOR (c:TextChunk) ON (c.doc_id);

// Index for entity type filtering
CREATE INDEX entity_type FOR (e:Entity) ON (e.entity_type);

// Composite index for metadata filtering
CREATE INDEX document_metadata FOR (d:Document) ON (d.metadata);
```

**Notes:**
- LightRAG manages schema creation automatically via `initialize_storages()`
- Vector dimensions must be set ONCE during initial table creation (cannot be changed later without recreating indexes)
- When changing embedding models, existing vector indexes must be dropped and recreated
- Neo4j Community Edition supports all features except clustering

---
