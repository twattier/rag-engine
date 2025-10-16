# Epic 3: Graph-Based Retrieval, Knowledge Graph Construction & Visualization

**Status:** Draft
**Epic Goal:** Integrate LightRAG for entity extraction, relationship mapping, hybrid retrieval (vector + graph + BM25), reranking pipeline, and expose graph visualization UI to deliver core RAG functionality with operational transparency. Users can query the knowledge base and receive relevant results leveraging graph-based retrieval superior to simple vector search.

---

## Stories in this Epic

## Story 3.1: Integrate LightRAG Core Library and Initialize Graph Storage

**As a** developer,
**I want** LightRAG integrated with Neo4j for graph-based knowledge representation,
**so that** documents are transformed into entity-relationship graphs.

### Acceptance Criteria

1. `services/lightrag-integration/` contains LightRAG integration service
2. Service initializes LightRAG instance with Neo4j storage backend configuration
3. LightRAG configuration includes: Neo4j connection parameters, embedding model (sentence-transformers), LLM endpoint (via LiteLLM or direct)
4. Service exposes internal API endpoint `POST /build-graph` accepting parsed document content from RAG-Anything service
5. Graph construction extracts entities based on configured entity types (from Epic 2.5)
6. Extracted entities and relationships persisted to Neo4j with vector embeddings
7. `shared/utils/lightrag_client.py` provides reusable LightRAG client wrapper
8. Integration test verifies graph construction for sample document, validates entities exist in Neo4j

## Story 3.2: Implement Entity Extraction with Custom Entity Types

**As a** domain specialist,
**I want** LightRAG to extract domain-specific entities from my documents,
**so that** the knowledge graph reflects my specialized terminology.

### Acceptance Criteria

1. LightRAG entity extraction uses configured entity types from `entity-types.yaml` (Epic 2.5)
2. LLM prompt engineering includes entity type descriptions and examples for improved extraction accuracy
3. Extracted entities include: entity_type, entity_name, confidence_score, source_document_id, text_span (where entity was found)
4. Neo4j graph schema: Entity nodes with properties (name, type, embedding), Document nodes, CONTAINS relationships
5. Duplicate entity resolution: entities with similar names (fuzzy matching >90% similarity) merged into single node
6. Entity extraction logs include: document_id, entities_extracted_count, extraction_duration
7. Validation query in Neo4j confirms entities of all configured types are being created
8. Integration test with technical documentation verifies custom entity types (API, Service, Database) are extracted

## Story 3.3: Implement Relationship Mapping and Graph Construction

**As a** knowledge seeker,
**I want** LightRAG to discover relationships between entities across documents,
**so that** I can explore connected knowledge through graph traversal.

### Acceptance Criteria

1. LightRAG extracts relationships between entities with: relationship_type, source_entity, target_entity, confidence_score
2. Relationship types include: MENTIONS, RELATED_TO, PART_OF, IMPLEMENTS, DEPENDS_ON, LOCATED_IN, AUTHORED_BY (extensible)
3. Neo4j graph schema extended: Relationship edges between Entity nodes with properties (type, confidence, source_document_id)
4. Cross-document relationships: entities mentioned in multiple documents connected through graph
5. Graph construction preserves document hierarchy: Document → Section → Entity relationships
6. Performance optimization: batch entity/relationship creation in Neo4j (transactions of 100 entities)
7. Graph statistics endpoint `GET /api/v1/graph/stats` returns: total_entities, total_relationships, entity_type_distribution
8. Integration test verifies relationships exist between entities from same document and cross-document relationships

## Story 3.4: Implement Hybrid Retrieval Pipeline (Vector + Graph + BM25)

**As a** RAG Engine user,
**I want** queries to leverage vector similarity, graph traversal, and keyword matching,
**so that** retrieval results are more accurate than single-method approaches.

### Acceptance Criteria

1. API endpoint `POST /api/v1/query` accepts: query_text, retrieval_mode ("naive", "local", "global", "hybrid"), top_k (default: 10)
2. Retrieval modes implemented using LightRAG's query modes:
   - **Naive**: Simple vector similarity search
   - **Local**: Entity-centric retrieval with 1-hop graph traversal
   - **Global**: Community detection and high-level concept retrieval
   - **Hybrid**: Combines local + global retrieval strategies
3. BM25 sparse retrieval integrated for keyword matching (complements dense embeddings)
4. Retrieval pipeline returns: list of relevant text chunks, source_document_ids, relevance_scores, retrieved_entities
5. Query response includes retrieval_mode_used and retrieval_latency_ms for transparency
6. Embedding generation uses configured embedding model (sentence-transformers or OpenAI via LiteLLM)
7. Performance target: P95 latency < 2 seconds for 1000-document knowledge base
8. Integration test compares retrieval modes on same query, validates hybrid returns more results than naive

## Story 3.5: Implement Metadata-Based Pre-Filtering for Retrieval

**As a** knowledge base user,
**I want** to filter retrieval by metadata fields before searching,
**so that** queries are faster and more precise by searching only relevant documents.

### Acceptance Criteria

1. Query endpoint accepts `metadata_filters` parameter with JSON object: `{"department": "engineering", "date": {"gte": "2024-01-01"}}`
2. Filter operators supported: equality, inequality, date ranges (`gte`, `lte`), tag inclusion (`in`), boolean logic (`AND`, `OR`)
3. Pre-filtering applies Neo4j Cypher query constraints before retrieval, narrowing search space
4. Filtered retrieval returns only results from documents matching metadata criteria
5. Query response includes `filtered_document_count` showing how many documents matched metadata filters
6. Performance improvement: metadata filtering on 20% of knowledge base demonstrates 40%+ latency reduction vs. unfiltered
7. Neo4j indexes created on common metadata fields (department, date_created, project_name) for performance
8. Integration test verifies metadata filtering with complex queries (AND/OR logic, date ranges)

## Story 3.6: Integrate Reranking Pipeline for Result Refinement

**As a** knowledge seeker,
**I want** retrieval results reranked by relevance to my query,
**so that** the most useful results appear first.

### Acceptance Criteria

1. Reranking service integrated using open-source cross-encoder: Jina AI reranker (`jina-reranker-v2-base-multilingual`) or MS Marco (`ms-marco-MiniLM-L-12-v2`)
2. Query endpoint accepts `rerank` parameter (boolean, default: false for MVP)
3. Reranking applied to top-k retrieval results (configurable, default: rerank top 50, return top 10)
4. Reranked results include: original_score (from retrieval), rerank_score, final_rank
5. Reranking model runs locally (no external API calls) for privacy
6. Reranking adds <500ms latency to query pipeline (measured on 50 candidates)
7. Configuration in `.env`: `RERANKER_MODEL`, `RERANKER_ENABLED` (default: false for performance)
8. Integration test validates reranking changes result order, top result after reranking has higher relevance than before

## Story 3.7: Deploy LightRAG Server as Docker Service

**As a** knowledge base explorer,
**I want** LightRAG Server's graph visualization UI accessible through my browser,
**so that** I can visually explore the knowledge graph structure.

### Acceptance Criteria

1. `docker-compose.yml` includes `lightrag-server` service configuration using LightRAG Server
2. LightRAG Server exposed on port 9621 (configurable via `.env`: `LIGHTRAG_SERVER_PORT`)
3. LightRAG Server configured to connect to shared Neo4j instance
4. Web UI accessible at `http://localhost:9621` after `docker-compose up`
5. UI displays: graph visualization canvas, document list, query interface, settings panel
6. Service health check verifies LightRAG Server is responding
7. Documentation in `docs/graph-visualization.md` with screenshots and usage guide
8. Manual test verifies UI loads and displays graph after documents are ingested (Epic 2 + Epic 3)

## Story 3.8: Configure Neo4j Browser Access and Documentation

**As a** developer,
**I want** direct access to Neo4j Browser for database inspection,
**so that** I can debug graph structure and run custom Cypher queries.

### Acceptance Criteria

1. Neo4j Browser accessible at `http://localhost:7474` (configured in Epic 1.2)
2. Documentation in `docs/neo4j-browser-guide.md` covering:
   - Accessing Neo4j Browser and authentication
   - Common Cypher queries for inspecting documents, entities, relationships
   - Example queries: "Show all entities of type X", "Find relationships between entities", "Count documents by metadata field"
3. Example Cypher query collection in `docs/example-queries.cypher`
4. Screenshots showing graph schema visualization in Neo4j Browser
5. Troubleshooting section for authentication issues and connection failures
6. Query performance tips: using indexes, limiting result sizes

## Story 3.9: Document Graph Exploration Workflows

**As a** knowledge base user,
**I want** clear guidance on exploring the knowledge graph visually,
**so that** I understand how documents are connected and validate retrieval quality.

### Acceptance Criteria

1. `docs/graph-exploration-workflows.md` provides step-by-step workflows for:
   - Finding a specific document in the graph
   - Exploring entities extracted from a document
   - Tracing relationships between entities across documents
   - Filtering graph view by metadata fields
   - Filtering graph view by entity types
   - Understanding retrieval paths (why a document was retrieved for a query)
2. Workflow documentation includes screenshots from LightRAG Server UI
3. Each workflow includes: goal, steps, expected outcome, common issues
4. Video tutorial (screencast) demonstrating graph exploration workflows (optional, time permitting)
5. Examples use real sample documents from integration tests
6. Documentation cross-references API endpoints for programmatic graph queries

## Story 3.10: Implement Graph Metadata and Entity Type Filtering

**As a** knowledge graph explorer,
**I want** to filter the graph visualization by metadata fields and entity types,
**so that** I can focus on specific subsets of knowledge.

### Acceptance Criteria

1. LightRAG Server UI supports filtering (if built-in capability exists) or documentation provides Cypher queries for filtering
2. Filtering capabilities documented for:
   - Show only documents with specific metadata (e.g., department=engineering)
   - Show only entities of specific types (e.g., only "Person" and "Organization")
   - Show documents within date range
   - Combine multiple filters (AND/OR logic)
3. Filtered views dynamically update graph visualization
4. Documentation includes example filter configurations with expected results
5. API endpoint `GET /api/v1/graph/query` provides programmatic filtered graph queries (returns nodes/edges as JSON)
6. Integration test verifies filtered graph queries return correct subset of entities/relationships

## Story 3.11: Implement Entity Type Schema Evolution and Re-Extraction

**As a** domain specialist,
**I want** to add new entity types without losing existing graph data,
**so that** I can refine entity extraction as my understanding of the domain improves.

### Acceptance Criteria

1. API endpoint `POST /api/v1/config/entity-types` adds new entity types to `entity-types.yaml`:
   - Accepts: type_name, description, examples
   - Validates type_name uniqueness
   - Persists immediately (no service restart required)

2. New entity types immediately available for future document ingestion

3. Existing documents not automatically re-extracted (opt-in re-extraction):
   - Avoids unexpected LLM costs
   - User explicitly triggers re-extraction when ready

4. API endpoint `POST /api/v1/graph/re-extract` triggers entity re-extraction:
   - Accepts: entity_types (list of new types to extract), document_filters (optional)
   - Returns re_extraction_job_id for progress tracking
   - Re-extraction uses LLM to identify entities of new types in existing document content

5. Re-extraction adds new entities without removing existing ones:
   - Preserves existing entity nodes and relationships
   - Adds new entity nodes of new types
   - Creates new relationships between new and existing entities

6. API endpoint `GET /api/v1/graph/re-extract/{job_id}/status` returns:
   - total_documents, processed_count, entities_added_count, status

7. Entity type changes logged with timestamp, user, and rationale to audit log

8. Documentation in `docs/entity-evolution.md` explains:
   - When to add new entity types
   - Re-extraction cost considerations (LLM API usage)
   - Examples: adding "API Endpoint" type to technical docs, adding "Regulation" type to legal docs

9. Graph statistics endpoint `GET /api/v1/graph/stats` updated to show entity distribution by type (including new types post-re-extraction)

---
