# Epic 3: Graph-Based Retrieval, Knowledge Graph Construction & Visualization

**Status:** ✅ Ready for Development
**Epic Goal:** Integrate LightRAG for entity extraction, relationship mapping, hybrid retrieval (vector + graph + BM25), reranking pipeline, and expose graph visualization UI to deliver core RAG functionality with operational transparency. Users can query the knowledge base and receive relevant results leveraging graph-based retrieval superior to simple vector search.

**Story Files Status:** ✅ All 11 story files created
**Dependencies Status:** ✅ Epic 1 Complete, Epic 2 Complete
**Estimated Duration:** 3-4 weeks (48 story points)

---

## Story Files Index

All story files created with comprehensive details:

### Phase 1: LightRAG Core Integration (24 points, ~2 weeks)
- ✅ **[Story 3.1](3.1.lightrag-integration.md)** (8 points) - Integrate LightRAG Core Library and Initialize Graph Storage
- ✅ **[Story 3.2](3.2.entity-extraction.md)** (8 points) - Implement Entity Extraction with Custom Entity Types
- ✅ **[Story 3.3](3.3.relationship-mapping.md)** (8 points) - Implement Relationship Mapping and Graph Construction

### Phase 2: Retrieval Pipeline (16 points, ~1 week)
- ✅ **[Story 3.4](3.4.hybrid-retrieval.md)** (8 points) - Implement Hybrid Retrieval Pipeline (Vector + Graph + BM25)
- ✅ **[Story 3.5](3.5.metadata-filtering.md)** (4 points) - Implement Metadata-Based Pre-Filtering for Retrieval
- ✅ **[Story 3.6](3.6.reranking-pipeline.md)** (4 points) - Integrate Reranking Pipeline for Result Refinement

### Phase 3: Visualization & Documentation (8 points, ~1 week)
- ✅ **[Story 3.7](3.7.lightrag-server-deployment.md)** (2 points) - Deploy LightRAG Server as Docker Service
- ✅ **[Story 3.8](3.8.neo4j-browser-guide.md)** (1 point) - Configure Neo4j Browser Access and Documentation
- ✅ **[Story 3.9](3.9.graph-exploration-workflows.md)** (1 point) - Document Graph Exploration Workflows
- ✅ **[Story 3.10](3.10.graph-filtering.md)** (1 point) - Implement Graph Metadata and Entity Type Filtering
- ✅ **[Story 3.11](3.11.entity-type-evolution.md)** (3 points) - Implement Entity Type Schema Evolution and Re-Extraction

**Total: 48 story points**

---

## Readiness Checklist

### Dependencies ✅
- [x] Epic 1: Foundation & Core Infrastructure (Complete)
- [x] Epic 2: Multi-Format Document Ingestion Pipeline (Complete)
- [x] Neo4j operational with vector support
- [x] API service operational
- [x] Queue service with 5 documents ready for processing
- [x] Entity types configured ([config/entity-types.yaml](../../config/entity-types.yaml))
- [x] Metadata schema configured ([config/metadata-schema.yaml](../../config/metadata-schema.yaml))

### Story Files ✅
- [x] All 11 story files created with comprehensive details
- [x] Dev notes include architecture references
- [x] Testing guidance provided
- [x] Tasks broken down with AC references

### Infrastructure Ready ✅
- [x] Docker Compose configuration operational
- [x] Neo4j schema ready for graph extensions
- [x] 5 CV documents queued for processing
- [x] RAG-Anything service running

### No Blockers Identified ✅

---

## Stories in this Epic (Detailed)

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

## Recommended Sprint Plan

### Sprint 1 (Week 1): LightRAG Foundation
**Stories:** 3.1, 3.2 (16 points)
**Duration:** 5-7 days
**Goals:**
- Implement queue processing worker (Story 3.1)
- Process 5 queued CV documents from Epic 2
- Extract entities with custom types (Story 3.2)
- Verify entities in Neo4j graph

**Key Deliverables:**
- LightRAG service integrated with Neo4j
- Queue worker operational
- Document status transitions: "queued" → "indexed"
- Entity nodes created in Neo4j

**Critical Path:** Story 3.1 must complete before 3.2

---

### Sprint 2 (Week 2): Graph Construction & Core Retrieval
**Stories:** 3.3, 3.4 (16 points)
**Duration:** 5-7 days
**Goals:**
- Build relationship graph (Story 3.3)
- Implement hybrid retrieval pipeline (Story 3.4)
- Achieve NFR1 target: P95 query latency <2s

**Key Deliverables:**
- Entity relationships mapped
- Cross-document linking operational
- Query API endpoint functional
- All 4 retrieval modes working (naive, local, global, hybrid)

**Critical Path:** Story 3.3 must complete before 3.4

---

### Sprint 3 (Week 3): Retrieval Optimization
**Stories:** 3.5, 3.6 (8 points)
**Duration:** 3-4 days
**Goals:**
- Optimize query performance with metadata filtering (Story 3.5)
- Implement reranking for precision (Story 3.6)
- Achieve NFR9 target: 40%+ latency reduction

**Key Deliverables:**
- Metadata pre-filtering operational
- Reranking pipeline integrated
- Performance targets validated

**Parallelization:** Stories 3.5 and 3.6 can run in parallel if resources available

---

### Sprint 4 (Week 4): Visualization & Documentation
**Stories:** 3.7, 3.8, 3.9, 3.10, 3.11 (8 points)
**Duration:** 3-5 days
**Goals:**
- Deploy graph visualization UI (Story 3.7)
- Complete documentation (Stories 3.8, 3.9)
- Implement graph filtering (Story 3.10)
- Enable entity type evolution (Story 3.11)

**Key Deliverables:**
- LightRAG Server UI accessible
- Neo4j Browser guide complete
- Graph exploration workflows documented
- Entity type evolution API operational

**Parallelization:** Stories 3.7-3.10 can run in parallel; Story 3.11 depends on 3.1-3.3

---

## Epic Dependencies

**Depends On:**
- ✅ Epic 1: Foundation & Core Infrastructure (COMPLETE)
- ✅ Epic 2: Multi-Format Document Ingestion Pipeline (COMPLETE)

**Blocks:**
- Epic 4: REST API & Integration Layer (requires query functionality)
- Epic 5: Production Readiness (requires operational graph-based retrieval)

---

## Epic Acceptance Criteria

1. [ ] LightRAG integrated with Neo4j storage backend
2. [ ] 5 queued CV documents processed and indexed
3. [ ] Entity extraction operational with 10 configured entity types
4. [ ] Relationship mapping creates connected knowledge graph
5. [ ] Hybrid retrieval pipeline functional (naive, local, global, hybrid modes)
6. [ ] Metadata-based pre-filtering reduces query latency by 40%+
7. [ ] Reranking pipeline improves result precision
8. [ ] LightRAG Server UI accessible and displaying graph
9. [ ] Neo4j Browser documentation complete
10. [ ] Graph exploration workflows documented
11. [ ] Entity type evolution API operational
12. [ ] **NFR1 Validated:** P95 query latency <2s for 1000-document knowledge base
13. [ ] **NFR9 Validated:** Metadata filtering achieves 40%+ latency reduction

---

## Technical Notes

### Key Technologies
- **LightRAG**: 0.x (graph-based retrieval engine)
- **Neo4j**: 5.x (graph + vector storage)
- **sentence-transformers**: Latest (local embeddings)
- **BM25**: rank-bm25 library (keyword matching)
- **Cross-encoder**: Jina AI or MS Marco (reranking)
- **LiteLLM**: Latest (LLM proxy for entity extraction)

### Neo4j Schema Extensions

**New Nodes:**
- `:Entity {id, name, type, embedding, confidence_score, source_doc_id}`

**New Relationships:**
- `(:Document)-[:CONTAINS {text_span, confidence}]->(:Entity)`
- `(:Entity)-[:RELATIONSHIP {type, confidence, source_doc_id}]->(:Entity)`
- `(:Entity)-[:APPEARS_IN]->(:Document)` (cross-document links)

**New Indexes:**
- `CREATE INDEX entity_name_idx FOR (e:Entity) ON (e.name)`
- `CREATE INDEX entity_type_idx FOR (e:Entity) ON (e.type)`
- `CREATE VECTOR INDEX entity_embedding_idx FOR (e:Entity) ON (e.embedding)`

### API Endpoints Created
- `POST /api/v1/query` - Hybrid retrieval query
- `GET /api/v1/graph/stats` - Graph statistics
- `GET /api/v1/graph/query` - Programmatic graph queries
- `POST /api/v1/config/entity-types` - Add entity type
- `POST /api/v1/graph/re-extract` - Trigger re-extraction
- `GET /api/v1/graph/re-extract/{job_id}/status` - Re-extraction progress

---

## Epic Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| LightRAG library maturity (0.x version) | Medium | High | Consider 2-day spike to validate before starting; have fallback plan for custom implementation |
| Epic size (11 stories, 48 points) | Medium | Medium | Monitor progress weekly; consider splitting into Epic 3A/3B if timeline extends |
| Performance targets (NFR1, NFR2, NFR9) | Medium | High | Implement benchmarking from Story 3.1; optimize incrementally throughout epic |
| LLM API costs for entity extraction | Low | Medium | Use local models (Ollama); mock in tests; document cost estimates |
| Graph visualization performance (large graphs) | Low | Low | Limit visualization scope; implement pagination/filtering |
| Cross-document entity deduplication accuracy | Medium | Medium | Implement fuzzy matching (>90% threshold); manual review capabilities |

---

## Epic Definition of Done

- [ ] All 11 stories completed with acceptance criteria met
- [ ] Queue worker processing documents successfully
- [ ] Entity extraction working with all 10 configured types
- [ ] Relationship graph construction operational
- [ ] Hybrid retrieval functional with all 4 modes
- [ ] Performance targets validated (NFR1: <2s latency, NFR9: 40%+ reduction)
- [ ] LightRAG Server UI deployed and accessible
- [ ] Documentation complete (Neo4j Browser guide, exploration workflows)
- [ ] Entity type evolution API operational
- [ ] Integration tests pass for all stories
- [ ] Demo: Query knowledge base with 5 CV documents → retrieve relevant results via hybrid retrieval → visualize graph → verify performance metrics

---

## Performance Targets (NFRs)

**From PRD:**
- **NFR1:** P95 query latency <2 seconds for 1000-document knowledge base ✅ Validated in Story 3.4
- **NFR2:** MRR >0.80 on BEIR SciFact dataset (15+ percentage point improvement vs baseline) ✅ Validated in Epic 5 Story 5.7
- **NFR9:** Metadata filtering demonstrates 40%+ latency reduction on 20% subset ✅ Validated in Story 3.5

**Additional Performance Metrics:**
- Entity extraction: <30s per CV document (Story 3.1, 3.2)
- Relationship mapping: <5s per 100 entities (Story 3.3)
- Reranking latency: <500ms for 50 candidates (Story 3.6)
- Graph statistics query: <100ms (Story 3.3)

---

## Quality Standards to Maintain

**From Epic 2 (90/100 average QA score):**
- Type safety: `from __future__ import annotations` in all modules
- Structured logging with context (doc_id, entity_type, query_id)
- Comprehensive integration tests (80%+ coverage)
- Performance metrics logged in every story
- Documentation-first approach

**Epic 3 Additions:**
- Graph schema validation queries
- LLM prompt engineering documentation
- Cross-document entity deduplication testing
- Retrieval mode comparison benchmarks

---

## Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-10-15 | 1.0 | Epic created from PRD | Sarah (PO Agent) |
| 2025-10-17 | 2.0 | Status updated to Ready for Development; Added Story Files Index (11 stories, 48 points); Added Readiness Checklist (all dependencies met, no blockers); Added Recommended Sprint Plan (4 sprints); Added Epic Acceptance Criteria, Technical Notes, Risks, and Performance Targets; All story files created with comprehensive details | Sarah (PO Agent) |

---
