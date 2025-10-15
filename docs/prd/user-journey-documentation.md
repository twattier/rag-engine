# User Journey Documentation

This section maps primary user workflows to epic sequences, ensuring all user touchpoints are covered and the epic structure delivers coherent end-to-end experiences.

## Journey 1: New User Onboarding (First-Time Deployment)

**User Goal:** Deploy RAG Engine and validate it's working correctly

**Epic Mapping:** Epic 1 (Foundation)

**Steps:**
1. **Prerequisites Check** → Verify Docker 24.0+ installed, 16GB RAM available, ports 7474, 7687, 8000, 9621 available
2. **Repository Setup** → Clone repository, copy `.env.example` to `.env`, review configuration variables
3. **Initial Deployment** → Run `docker-compose up -d`, observe service startup logs
4. **Health Verification** → Access health endpoint (`http://localhost:8000/health`), verify all services report "healthy"
5. **UI Access** → Open Neo4j Browser (`http://localhost:7474`), LightRAG Server (`http://localhost:9621`), API docs (`http://localhost:8000/docs`)
6. **Validation** → Run validation script (`scripts/validate-deployment.sh`), confirm all checks pass

**Success Criteria:** User can deploy RAG Engine and see all services running within 30 minutes

**Touchpoints:**
- Story 1.1: Repository structure and README
- Story 1.2: Neo4j deployment and browser access
- Story 1.3: API service and health endpoint
- Story 1.4: Health monitoring with dependency checks
- Story 1.6: Deployment validation script

**Common Issues & Resolution:**
- **Port conflicts** → Documentation guides user to change ports in `.env`
- **Neo4j authentication failure** → Troubleshooting doc explains credential reset
- **Service timeout** → Logs guide debugging (check Docker resources, network connectivity)

## Journey 2: Knowledge Base Population (Document Ingestion)

**User Goal:** Ingest documents with custom metadata and entity types for domain-specific knowledge base

**Epic Mapping:** Epic 2 (Ingestion) → Epic 3 (Graph Construction)

**Steps:**
1. **Define Metadata Schema** → Edit `config/metadata-schema.yaml` to add domain-specific fields (e.g., `department`, `project`)
2. **Configure Entity Types** → Edit `config/entity-types.yaml` to define expected entities (e.g., `API`, `Service`, `Database` for technical docs)
3. **Prepare Documents** → Organize documents in folders by type (PDFs, Markdown, code files)
4. **Single Document Test** → Use API endpoint `POST /api/v1/documents/ingest` to upload one document with metadata, verify success
5. **Batch Upload** → Prepare CSV mapping filenames to metadata, use `POST /api/v1/documents/ingest/batch` for bulk upload
6. **Monitor Progress** → Poll batch status endpoint, wait for completion
7. **Verify Ingestion** → Query `GET /api/v1/documents` to list ingested documents, check metadata
8. **Inspect Graph** → Open LightRAG Server UI, explore entities and relationships extracted from documents

**Success Criteria:** User can ingest 100+ documents across multiple formats with custom metadata and see entity graph in visualization

**Touchpoints:**
- Story 2.1: RAG-Anything parsing service for format support
- Story 2.2: Metadata schema definition and validation
- Story 2.3: Document ingestion API with metadata
- Story 2.4: Batch ingestion with progress tracking
- Story 2.5: Entity type configuration
- Story 2.6: Document listing and management
- Story 2.7: Metadata schema migration
- Story 3.1: LightRAG graph construction from ingested documents
- Story 3.2: Entity extraction with custom types
- Story 3.3: Relationship mapping across documents

**Common Issues & Resolution:**
- **Parsing failures** → Check supported formats, review error logs for specific file issues
- **Metadata validation errors** → Review schema definition, ensure CSV matches schema
- **Missing entities** → Verify entity types configured before ingestion, consider reindexing
- **Batch timeout** → Large batches split into smaller chunks, check system resources

## Journey 3: Query and Retrieval Optimization

**User Goal:** Query knowledge base with metadata filtering and optimize retrieval quality

**Epic Mapping:** Epic 3 (Retrieval & Visualization)

**Steps:**
1. **Basic Query** → Use API endpoint `POST /api/v1/query` with simple text query, review results
2. **Retrieval Mode Comparison** → Test different modes (`naive`, `local`, `global`, `hybrid`), compare result quality
3. **Apply Metadata Filters** → Add `metadata_filters` to query (e.g., `{"department": "engineering"}`), observe filtered results
4. **Enable Reranking** → Set `rerank: true` in query, compare top results before/after reranking
5. **Analyze Retrieval Path** → Use graph visualization to trace why specific documents were retrieved
6. **Performance Measurement** → Review `retrieval_latency_ms` in response, validate P95 < 2s target
7. **Iterate on Filters** → Refine metadata filters to narrow search space, measure latency improvement

**Success Criteria:** User achieves relevant results with acceptable performance and understands how to optimize queries

**Touchpoints:**
- Story 3.4: Hybrid retrieval pipeline implementation
- Story 3.5: Metadata-based pre-filtering
- Story 3.6: Reranking pipeline integration
- Story 3.7: LightRAG Server UI deployment
- Story 3.9: Graph exploration workflow documentation
- Story 3.10: Metadata and entity type filtering in visualization

**Common Issues & Resolution:**
- **Irrelevant results** → Try different retrieval modes, enable reranking, refine query phrasing
- **Slow queries** → Apply metadata filters to reduce search space, check Neo4j query performance
- **Missing expected documents** → Verify documents ingested correctly, check entity extraction quality
- **Graph visualization confusion** → Follow workflow documentation, use filters to simplify view

## Journey 4: Open-WebUI Integration

**User Goal:** Use RAG Engine from Open-WebUI chat interface for conversational knowledge access

**Epic Mapping:** Epic 4 (REST API) → Epic 5 (Open-WebUI Integration)

**Steps:**
1. **Deploy Open-WebUI** → Install Open-WebUI separately (Docker or local), verify it's running
2. **Configure RAG Engine** → Ensure RAG Engine API accessible from Open-WebUI network (check Docker networking or host.docker.internal)
3. **Install Function Pipeline** → Copy `integrations/open-webui/rag_engine_pipeline.py` to Open-WebUI functions directory
4. **Configure Function** → Set RAG Engine API endpoint, API key, retrieval preferences (mode, reranking) in function settings
5. **Test in Chat** → Ask question in Open-WebUI chat, verify RAG Engine responds with cited sources
6. **Upload Document via Chat** → Use file upload in chat, verify document ingested to RAG Engine
7. **Query with Filters** → Use function parameters to apply metadata filters, observe filtered results
8. **Iterate** → Refine queries, adjust retrieval settings, explore different conversation patterns

**Success Criteria:** User can query RAG Engine knowledge base through natural conversation in Open-WebUI with cited sources

**Touchpoints:**
- Story 4.1: Unified API gateway for Open-WebUI integration
- Story 4.2: API authentication and rate limiting
- Story 4.3: OpenAPI documentation for integration reference
- Story 5.1: Open-WebUI Function Pipeline development
- Story 5.2: Production error handling for graceful degradation
- Story 5.6: User onboarding documentation with Open-WebUI setup

**Common Issues & Resolution:**
- **Connection failures** → Check network connectivity, API endpoint configuration, API key validity
- **Rate limiting** → Adjust rate limits in `.env`, consider per-user limits in Open-WebUI
- **Timeout errors** → Check retrieval performance, consider increasing timeout thresholds
- **No cited sources** → Verify function response formatting, check API response structure

## Journey 5: Troubleshooting and Knowledge Base Management

**User Goal:** Diagnose issues, manage knowledge base content, and maintain system health

**Epic Mapping:** All Epics (Cross-cutting)

**Steps:**
1. **Check System Health** → Access `/health` endpoint, review dependency statuses, check logs
2. **Inspect Neo4j** → Open Neo4j Browser, run diagnostic Cypher queries (entity counts, relationship stats)
3. **Review Logs** → Use `docker-compose logs -f [service]` to tail service logs, filter by error level
4. **Graph Statistics** → Query `/api/v1/graph/stats` API endpoint for knowledge base metrics
5. **List Documents** → Use `/api/v1/documents` with filters to find problematic documents
6. **Delete Documents** → Remove incorrect or outdated documents via API, verify graph updates
7. **Reindex Documents** → Use schema migration workflow to reindex after entity type or metadata changes
8. **Performance Benchmarking** → Run `scripts/benchmark-retrieval.sh` to validate performance targets
9. **Backup Knowledge Base** → Execute `scripts/backup-neo4j.sh` before major changes

**Success Criteria:** User can independently diagnose and resolve common issues without external support

**Touchpoints:**
- Story 1.4: Health monitoring with dependency checks
- Story 1.5: Structured logging for debugging
- Story 1.6: Troubleshooting documentation
- Story 2.6: Document management API (list, retrieve, delete)
- Story 2.7: Metadata schema migration
- Story 3.3: Graph statistics endpoint
- Story 3.11: Entity type schema evolution
- Story 5.3: Monitoring endpoints and metrics
- Story 5.4: Production deployment documentation with backup procedures

**Common Issues & Resolution:**
- **Service unhealthy** → Check Docker resources, restart services, review logs for errors
- **Neo4j out of memory** → Adjust heap size in `.env`, consider upgrading hardware
- **Graph quality issues** → Review entity extraction, adjust entity types, reindex documents
- **Performance degradation** → Check document count, analyze slow queries, optimize metadata filters

---
