# Epic 3: Graph-Based Retrieval, Knowledge Graph Construction & Visualization

**Status:** Draft
**Epic Goal:** Integrate LightRAG for entity extraction, relationship mapping, hybrid retrieval (vector + graph + BM25), reranking pipeline, and expose graph visualization UI to deliver core RAG functionality with operational transparency. Users can query the knowledge base and receive relevant results leveraging graph-based retrieval superior to simple vector search.

---

## Stories in this Epic

### Story 3.1: Integrate LightRAG Core Library and Initialize Graph Storage
**As a** developer,
**I want** LightRAG integrated with Neo4j for graph-based knowledge representation,
**so that** documents are transformed into entity-relationship graphs.

[Details in Story File: 3.1.integrate-lightrag.md]

---

### Story 3.2: Implement Entity Extraction with Custom Entity Types
**As a** domain specialist,
**I want** LightRAG to extract domain-specific entities from my documents,
**so that** the knowledge graph reflects my specialized terminology.

[Details in Story File: 3.2.entity-extraction.md]

---

### Story 3.3: Implement Relationship Mapping and Graph Construction
**As a** knowledge seeker,
**I want** LightRAG to discover relationships between entities across documents,
**so that** I can explore connected knowledge through graph traversal.

[Details in Story File: 3.3.relationship-mapping.md]

---

### Story 3.4: Implement Hybrid Retrieval Pipeline (Vector + Graph + BM25)
**As a** RAG Engine user,
**I want** queries to leverage vector similarity, graph traversal, and keyword matching,
**so that** retrieval results are more accurate than single-method approaches.

[Details in Story File: 3.4.hybrid-retrieval.md]

---

### Story 3.5: Implement Metadata-Based Pre-Filtering for Retrieval
**As a** knowledge base user,
**I want** to filter retrieval by metadata fields before searching,
**so that** queries are faster and more precise by searching only relevant documents.

[Details in Story File: 3.5.metadata-filtering.md]

---

### Story 3.6: Integrate Reranking Pipeline for Result Refinement
**As a** knowledge seeker,
**I want** retrieval results reranked by relevance to my query,
**so that** the most useful results appear first.

[Details in Story File: 3.6.reranking.md]

---

### Story 3.7: Deploy LightRAG Server as Docker Service
**As a** knowledge base explorer,
**I want** LightRAG Server's graph visualization UI accessible through my browser,
**so that** I can visually explore the knowledge graph structure.

[Details in Story File: 3.7.lightrag-server.md]

---

### Story 3.8: Configure Neo4j Browser Access and Documentation
**As a** developer,
**I want** direct access to Neo4j Browser for database inspection,
**so that** I can debug graph structure and run custom Cypher queries.

[Details in Story File: 3.8.neo4j-browser.md]

---

### Story 3.9: Document Graph Exploration Workflows
**As a** knowledge base user,
**I want** clear guidance on exploring the knowledge graph visually,
**so that** I understand how documents are connected and validate retrieval quality.

[Details in Story File: 3.9.graph-workflows.md]

---

### Story 3.10: Implement Graph Metadata and Entity Type Filtering
**As a** knowledge graph explorer,
**I want** to filter the graph visualization by metadata fields and entity types,
**so that** I can focus on specific subsets of knowledge.

[Details in Story File: 3.10.graph-filtering.md]

---

### Story 3.11: Implement Entity Type Schema Evolution and Re-Extraction
**As a** domain specialist,
**I want** to add new entity types without losing existing graph data,
**so that** I can refine entity extraction as my understanding of the domain improves.

[Details in Story File: 3.11.entity-evolution.md]

---

## Epic Dependencies

**Depends On:**
- Epic 1: Foundation & Core Infrastructure (Neo4j, API service)
- Epic 2: Multi-Format Document Ingestion Pipeline (parsed documents)

**Blocks:**
- Epic 4: REST API & Integration Layer (retrieval endpoints)
- Epic 5: Open-WebUI Integration (query functionality)

---

## Epic Acceptance Criteria

1. ✅ LightRAG integrated with Neo4j for graph storage
2. ✅ Entity extraction working with custom entity types from `entity-types.yaml`
3. ✅ Relationship mapping creates connections between entities across documents
4. ✅ Hybrid retrieval pipeline functional (vector + graph + BM25)
5. ✅ Metadata-based pre-filtering reduces query latency by 40%+ on filtered subsets
6. ✅ Reranking pipeline improves top result relevance
7. ✅ LightRAG Server UI accessible at `http://localhost:9621`
8. ✅ Neo4j Browser guide with example Cypher queries
9. ✅ Graph exploration workflow documentation with screenshots
10. ✅ Graph filtering by metadata and entity types operational
11. ✅ Entity type re-extraction workflow tested without data loss

---

## Technical Notes

### Key Technologies
- LightRAG Python library (latest from HKUDS/LightRAG)
- Neo4j Python Driver for graph operations
- sentence-transformers for local embeddings (all-MiniLM-L6-v2)
- Jina AI reranker or MS Marco cross-encoder
- LightRAG Server for graph visualization
- LiteLLM Proxy for LLM access (optional)

### API Endpoints Created
- `POST /api/v1/query` - RAG query endpoint
- `GET /api/v1/graph/stats` - Knowledge graph statistics
- `GET /api/v1/graph/entities` - List entities with filters
- `GET /api/v1/graph/relationships` - List relationships
- `GET /api/v1/graph/query` - Filtered graph queries (JSON)
- `POST /api/v1/graph/re-extract` - Entity re-extraction job
- `GET /api/v1/graph/re-extract/{job_id}/status` - Re-extraction progress

### Retrieval Modes
- **Naive**: Simple vector similarity search
- **Local**: Entity-centric retrieval with 1-hop graph traversal
- **Global**: Community detection and high-level concept retrieval
- **Hybrid**: Combines local + global strategies (recommended)
- **Mix**: Adaptive mode selection based on query

### Neo4j Schema
- **Nodes**: Document, TextChunk, Entity
- **Relationships**: HAS_CHUNK, MENTIONED_IN, RELATED_TO, CONTAINS, NEXT_CHUNK
- **Vector Indexes**: entity_embeddings, relationship_embeddings, chunk_embeddings (384 dimensions for all-MiniLM-L6-v2)
- **Performance Indexes**: doc_id_unique, entity_name_unique, chunk_doc_id, entity_type, document_metadata

### Critical Files Created
- `/services/lightrag-integration/service.py` - LightRAG wrapper
- `/services/api/routers/queries.py` - Query API routes
- `/services/api/routers/graph.py` - Graph exploration routes
- `/shared/utils/lightrag_client.py` - LightRAG client wrapper
- `/docs/graph-exploration-workflows.md` - Graph UI guide
- `/docs/neo4j-browser-guide.md` - Neo4j Browser documentation
- `/docs/example-queries.cypher` - Example Cypher queries

---

## Epic Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| LightRAG entity extraction quality | Medium | High | Custom entity types, prompt engineering, validation testing |
| Query latency exceeds 2s target | Medium | High | Metadata filtering, Neo4j indexing, performance testing |
| Graph visualization performance | Low | Medium | Filtering capabilities, documentation on large graphs |
| Embedding model compatibility | Low | High | Document vector dimensions in architecture, migration guide |
| LLM API costs during development | Medium | Medium | Use local models (Ollama), mock LLM endpoints in tests |

---

## Epic Definition of Done

- [ ] All 11 stories completed with acceptance criteria met
- [ ] Integration tests verify entity extraction, relationship mapping, retrieval pipeline
- [ ] Cross-epic test: Epic 2 ingested documents → Epic 3 graph construction → retrieval
- [ ] Performance tests validate P95 latency <2s on 1000-document knowledge base
- [ ] Metadata filtering demonstrates 40%+ latency reduction on 20% subset
- [ ] LightRAG Server UI accessible and functional
- [ ] Neo4j Browser guide tested with example queries
- [ ] Graph exploration workflows documented with screenshots
- [ ] Demo: Ingest documents → visualize graph → query with filters → compare retrieval modes

---

## Epic Metrics

- **Estimated Story Points:** 44 (based on 11 stories, ~4 points each) - **LARGEST EPIC**
- **Estimated Duration:** 3-4 weeks for solo developer
- **Key Performance Indicators:**
  - Query P95 latency: <2 seconds (1000 documents)
  - Metadata filtering latency reduction: >40% on 20% subset
  - Entity extraction coverage: >80% of expected entities found
  - Retrieval quality: Hybrid mode outperforms naive mode
  - Reranking improves top-1 result in >50% of queries

---

**Change Log:**

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-10-15 | 1.0 | Epic created from PRD | Sarah (PO Agent) |
