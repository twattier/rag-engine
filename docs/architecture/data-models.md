# Data Models

## Document

**Purpose:** Represents an ingested document with processing status and metadata

**Key Attributes:**
- `doc_id: string` - Unique document identifier (auto-generated or user-provided)
- `file_path: string` - Original file path or identifier
- `content_type: string` - MIME type or format (pdf, docx, markdown, etc.)
- `status: string` - Processing status (pending, processing, indexed, failed)
- `metadata: dict` - Custom metadata fields (author, department, date, tags, etc.)
- `created_at: datetime` - Timestamp of ingestion
- `updated_at: datetime` - Last processing update
- `chunk_count: integer` - Number of text chunks created
- `entity_count: integer` - Number of entities extracted
- `error_message: string?` - Error details if processing failed

### TypeScript Interface

```typescript
interface Document {
  docId: string;
  filePath: string;
  contentType: string;
  status: 'pending' | 'processing' | 'indexed' | 'failed';
  metadata: Record<string, any>;
  createdAt: string; // ISO 8601
  updatedAt: string;
  chunkCount: number;
  entityCount: number;
  errorMessage?: string;
}
```

### Relationships

- **HAS_CHUNKS** → TextChunk (1:many)
- **CONTAINS_ENTITIES** → Entity (many:many)
- **BELONGS_TO** → KnowledgeBase (many:1)

---

## Entity

**Purpose:** Represents a knowledge graph entity extracted from documents (person, organization, concept, etc.)

**Key Attributes:**
- `entity_name: string` - Canonical entity name
- `entity_type: string` - Entity category (person, organization, concept, etc.)
- `description: string` - LLM-generated entity description
- `source_ids: list[string]` - Document IDs where entity appears
- `metadata: dict` - Entity-specific metadata
- `embedding: vector` - Embedding vector for similarity search
- `created_at: datetime` - First extraction timestamp
- `updated_at: datetime` - Last update timestamp

### TypeScript Interface

```typescript
interface Entity {
  entityName: string;
  entityType: string;
  description: string;
  sourceIds: string[];
  metadata: Record<string, any>;
  embedding?: number[]; // Optional for API responses
  createdAt: string;
  updatedAt: string;
}
```

### Relationships

- **MENTIONED_IN** → Document (many:many)
- **RELATED_TO** → Entity (many:many) with relationship properties
- **PART_OF** → TextChunk (many:many)

---

## Relationship

**Purpose:** Represents semantic connections between entities in the knowledge graph

**Key Attributes:**
- `src_entity: string` - Source entity name
- `tgt_entity: string` - Target entity name
- `relationship_type: string` - Relationship description or type
- `description: string` - LLM-generated relationship summary
- `keywords: string` - Keywords describing the relationship
- `weight: float` - Relationship strength (0.0-1.0)
- `source_ids: list[string]` - Documents supporting this relationship
- `embedding: vector` - Embedding vector for relationship
- `created_at: datetime` - First extraction timestamp
- `updated_at: datetime` - Last update timestamp

### TypeScript Interface

```typescript
interface Relationship {
  srcEntity: string;
  tgtEntity: string;
  relationshipType: string;
  description: string;
  keywords: string;
  weight: number;
  sourceIds: string[];
  embedding?: number[];
  createdAt: string;
  updatedAt: string;
}
```

### Relationships

- **CONNECTS** → (Entity, Entity)
- **SUPPORTED_BY** → Document (many:many)

---

## TextChunk

**Purpose:** Represents a text segment from a document, used for retrieval

**Key Attributes:**
- `chunk_id: string` - Unique chunk identifier
- `doc_id: string` - Parent document ID
- `content: string` - Actual text content
- `chunk_index: integer` - Position within document
- `token_count: integer` - Number of tokens in chunk
- `embedding: vector` - Embedding vector for similarity search
- `metadata: dict` - Chunk-specific metadata (page number, section, etc.)
- `created_at: datetime` - Creation timestamp

### TypeScript Interface

```typescript
interface TextChunk {
  chunkId: string;
  docId: string;
  content: string;
  chunkIndex: number;
  tokenCount: number;
  embedding?: number[];
  metadata: Record<string, any>;
  createdAt: string;
}
```

### Relationships

- **BELONGS_TO** → Document (many:1)
- **CONTAINS** → Entity (many:many)
- **NEXT_CHUNK** → TextChunk (1:1, optional for sequence)

---

## QueryResult

**Purpose:** Represents the result of a RAG query, including context and generated response

**Key Attributes:**
- `query_id: string` - Unique query identifier
- `query_text: string` - Original user query
- `mode: string` - Retrieval mode (local, global, hybrid, naive, mix)
- `response: string` - Generated response from LLM
- `context_chunks: list[TextChunk]` - Retrieved text chunks
- `entities: list[Entity]` - Relevant entities
- `relationships: list[Relationship]` - Relevant relationships
- `metadata: dict` - Query metadata (filters, top_k, etc.)
- `latency_ms: integer` - Total query latency
- `created_at: datetime` - Query timestamp

### TypeScript Interface

```typescript
interface QueryResult {
  queryId: string;
  queryText: string;
  mode: 'local' | 'global' | 'hybrid' | 'naive' | 'mix';
  response: string;
  contextChunks: TextChunk[];
  entities: Entity[];
  relationships: Relationship[];
  metadata: Record<string, any>;
  latencyMs: number;
  createdAt: string;
}
```

### Relationships

- **RETRIEVES** → (TextChunk[], Entity[], Relationship[])

---
