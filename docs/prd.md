# RAG Engine Product Requirements Document (PRD)

## Goals and Background Context

### Goals

- Deliver a production-ready RAG deployment platform that achieves "ultimate" retrieval quality through graph-based knowledge representation
- Enable single-command Docker deployment (`docker-compose up -d`) that runs sophisticated RAG infrastructure without DevOps expertise
- Provide multi-format document ingestion (PDF, Markdown, HTML, Word, code) with intelligent graph entity extraction
- Support multiple integration patterns (Open-WebUI, MCP, n8n, Pydantic SDK, REST API) from a unified knowledge base
- Achieve 85%+ retrieval relevance vs. 60-70% baseline through hybrid retrieval, graph traversal, and reranking
- Empower users with graph visualization UI for knowledge exploration and retrieval validation
- Enable custom metadata fields and domain-specific entity types to improve graph quality and search precision
- Demonstrate deployment time-to-value under 30 minutes from setup to first successful query

### Background Context

Organizations and developers building AI applications face a critical dilemma: basic RAG implementations are easy to deploy but deliver poor retrieval quality, while sophisticated graph-based solutions like LightRAG offer superior results but require extensive infrastructure expertise. This gap forces teams to choose between quick deployment and performance, wasting developer time on infrastructure rather than improving retrieval quality.

RAG Engine solves this by integrating best-in-class open-source RAG technologies (LightRAG for graph-based retrieval, RAG-Anything for multi-format ingestion) into a production-grade Docker-based deployment platform. By standing on the shoulders of giants rather than reinventing algorithms, we deliver ultimate RAG performance with operational excellence—all running locally with zero vendor lock-in.

### Change Log

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-10-15 | v1.0 | Initial PRD creation from Project Brief | John (PM Agent) |

---

## Requirements

### Functional Requirements

**FR1:** The system shall support single-command Docker Compose deployment that initializes all required services (Neo4j, LightRAG, RAG-Anything, RAG Engine API, and optional LiteLLM proxy) with pre-configured default settings

**FR2:** The system shall ingest documents in multiple formats including PDF, Markdown, HTML, Microsoft Word (.doc/.docx), code files (Python, JavaScript, TypeScript, Java), and plain text through RAG-Anything integration

**FR3:** The system shall accept custom metadata fields during document ingestion (e.g., author, department, date, tags, project, category) configurable via API parameters or batch upload files (CSV/JSON)

**FR4:** The system shall accept user-defined expected entity types (e.g., person, organization, concept, product, location, technology) to guide LightRAG's entity extraction process via configuration files or API parameters

**FR5:** The system shall implement graph-based retrieval pipeline combining dense embeddings, sparse search (BM25), and graph traversal for multi-hop reasoning using LightRAG's hybrid retrieval modes

**FR6:** The system shall support metadata-based pre-filtering of search space before retrieval, allowing queries to specify metadata constraints (e.g., `department:engineering`, `date:2024`, `project:alpha`) with AND/OR logic, date ranges, and tag combinations

**FR7:** The system shall provide graph visualization UI through LightRAG Server for exploring knowledge graph structure, viewing entity relationships, visualizing document connections, and debugging retrieval paths

**FR8:** The system shall allow filtering graph visualization by custom metadata fields and entity types defined during ingestion

**FR9:** The system shall integrate open-source reranking using Jina AI reranker or MS Marco cross-encoder models to improve relevance of top-k retrieval results with configurable reranking strategies

**FR10:** The system shall provide an Open-WebUI Function Pipeline as a native Python function deployable directly to Open-WebUI, including configuration templates and setup documentation

**FR11:** The system shall expose a RESTful API with endpoints for document ingestion (with metadata), query/retrieval, knowledge base management, graph exploration, and entity/metadata filtering, documented via auto-generated OpenAPI 3.0 specification

**FR12:** The system shall support environment-based configuration for LLM endpoints (via LiteLLM), embedding models, retrieval parameters, custom entity type schemas, and system resources using `.env` files with optional YAML schema files for advanced customization

**FR13:** The system shall persist all knowledge graph data (entities, relationships, embeddings) to Neo4j with vector support for both graph traversal and vector similarity search

**FR14:** The system shall track document ingestion status and support incremental updates to the knowledge base without re-processing unchanged documents

**FR15:** The system shall extract entities and relationships from ingested documents automatically using LightRAG's entity extraction with LLM-powered natural language understanding

### Non-Functional Requirements

**NFR1:** The system shall achieve P95 query latency of less than 2 seconds for retrieval queries on a knowledge base containing 1,000 documents when running on the recommended hardware (16GB RAM, 8 CPU cores)

**NFR2:** The system shall demonstrate 85%+ retrieval relevance (measured via Mean Reciprocal Rank > 0.80 on BEIR benchmark dataset subset) compared to 60-70% baseline with ChromaDB simple vector search. Validation performed in Epic 5 Story 5.5 using BEIR SciFact dataset (1.1k scientific claims, 5k evidence documents) for domain-agnostic testing.

**Measurement Methodology:**
- **Baseline**: ChromaDB with naive vector search (no graph, no reranking) - expected MRR ~0.65-0.70
- **RAG Engine**: LightRAG hybrid retrieval with reranking - target MRR > 0.80
- **Dataset**: BEIR SciFact (scientific claim verification)
- **Metric**: Mean Reciprocal Rank (MRR) - measures how highly the first relevant document ranks
- **Success**: RAG Engine MRR ≥ baseline MRR × 1.15 (15+ percentage point improvement)

**NFR3:** The system shall complete the end-to-end deployment workflow (docker-compose up, ingest 100+ documents, define entity types, visualize graph, query knowledge base) within 30 minutes for new users

**NFR4:** The system shall achieve 99.9% uptime for the RAG Engine API service excluding external LLM dependencies

**NFR5:** The system shall run entirely on local infrastructure with zero external service dependencies except for optional LiteLLM for enterprise LLM access

**NFR6:** The system shall support knowledge bases up to 1,000 documents with acceptable performance (P95 < 2s) on MVP-recommended hardware as the baseline target

**NFR7:** The system shall provide clear error messages and troubleshooting guidance for common configuration issues across Linux, macOS, and Windows with WSL2 platforms

**NFR8:** The system shall implement automated Neo4j backup and restore functionality for knowledge base persistence

**NFR9:** The system shall demonstrate metadata-based filtering performance gains of 50%+ latency reduction when searching a filtered subset (e.g., 20% of knowledge base) compared to unfiltered search

**NFR10:** The system shall maintain API backward compatibility within major version releases to avoid breaking existing integrations

---

## User Interface Design Goals

### Overall UX Vision

**RAG Engine is a pure integration platform with zero custom UI development.** All user-facing interfaces are provided by the underlying services that RAG Engine orchestrates (LightRAG Server, Neo4j Browser, auto-generated API documentation). The product's UX strategy is "expose, don't create"—make the existing service UIs accessible through Docker networking and provide clear documentation for accessing them. Users experience RAG Engine primarily through programmatic integration (REST API, Open-WebUI Function Pipeline) with service-provided UIs serving operational/debugging purposes.

### Key Interaction Paradigms

- **Service-Native Interfaces**: Users access LightRAG Server's built-in web UI (graph visualization, document indexing, query interface) directly at its exposed port—RAG Engine simply ensures it's running and accessible
- **API-First Integration**: Primary interaction is through REST API consumed by external tools (Open-WebUI, n8n, custom scripts)—no custom RAG Engine web application
- **Configuration-as-Code**: System configuration through `.env` files, Docker Compose parameters, and YAML schemas—no GUI configuration panels to develop
- **Operational Transparency via Existing Tools**: Use LightRAG Server's UI for graph exploration, Neo4j Browser for database inspection, Docker logs for debugging—all provided by upstream services

### Core Screens and Views

**RAG Engine provides NO custom screens/views. Users access:**

- **LightRAG Server Web UI** (provided by LightRAG Server): Graph visualization, document upload interface, query testing interface—exposed on configured port (default: localhost:9621)
- **Neo4j Browser** (provided by Neo4j): Database exploration, Cypher query interface, graph schema inspection—exposed on Neo4j port (default: localhost:7474)
- **Swagger/ReDoc API Docs** (auto-generated by FastAPI): Interactive API documentation for RAG Engine's REST endpoints—exposed on API service port
- **Open-WebUI Chat Interface** (provided by Open-WebUI): Users interact with RAG Engine through Open-WebUI's existing chat UI after deploying the Function Pipeline

**RAG Engine Scope:**
- Configure and expose these services via Docker Compose
- Provide clear documentation on accessing each service UI (URLs, ports, default credentials)
- Ensure services are network-accessible within Docker environment

### Accessibility

**Not Applicable to RAG Engine MVP**

Accessibility is determined by the upstream services (LightRAG Server, Neo4j Browser, OpenAPI generators). RAG Engine does not develop custom UI components and therefore does not control accessibility implementation.

**Documentation Responsibility**: Provide links to each service's accessibility documentation where available.

### Branding

**No Custom Branding or Theming**

RAG Engine does not implement custom visual identity. Users see:
- LightRAG Server's default UI styling
- Neo4j Browser's default styling
- FastAPI's default Swagger/ReDoc themes

**RAG Engine Branding Limited To:**
- README.md header/logo (documentation only)
- API response headers (e.g., `X-Powered-By: RAG-Engine/1.0`)
- Docker Compose project name

### Target Device and Platforms

**Inherited from Service UIs**

- **LightRAG Server**: Desktop web browsers (as designed by LightRAG Server team)
- **Neo4j Browser**: Desktop web browsers (as designed by Neo4j)
- **API Documentation**: Any device capable of viewing web pages
- **REST API Access**: Platform-agnostic (any HTTP client on any platform)

**RAG Engine's Platform Responsibility**: Ensure Docker deployment works on Linux, macOS, and Windows with WSL2

---

## Technical Assumptions

### Repository Structure: **Monorepo**

RAG Engine will use a **monorepo** structure to house all services, shared libraries, configuration, and documentation in a single Git repository. This decision optimizes for:

**Rationale:**
- **Simplified Development**: Single clone operation, unified CI/CD, atomic commits across service boundaries
- **Small Team Efficiency**: 1-2 developers benefit from reduced repository management overhead
- **Shared Code Reuse**: Common Pydantic models, utilities, and configuration shared across services without package publishing
- **Docker Compose Alignment**: Single repository naturally maps to docker-compose.yml service definitions

**Structure:**
```
rag-engine/
├── docker-compose.yml           # Single-command deployment
├── services/
│   ├── api/                     # FastAPI REST API
│   ├── lightrag-integration/    # LightRAG service wrapper
│   └── rag-anything-integration/# RAG-Anything service wrapper
├── shared/
│   ├── models/                  # Pydantic data models
│   ├── config/                  # Configuration schemas
│   └── utils/                   # Shared utilities
├── tests/                       # Unit and integration tests
├── docs/                        # Documentation
└── .env.example                 # Environment configuration template
```

### Service Architecture: **Microservices within Docker Compose**

RAG Engine implements a **microservices pattern** orchestrated by Docker Compose, accepting operational complexity in exchange for modularity and upstream integration flexibility.

**Service Components:**

1. **RAG Engine API Service** (FastAPI)
   - Orchestration layer providing unified REST API
   - Routes requests to LightRAG and RAG-Anything services
   - Handles authentication, validation, error handling

2. **LightRAG Integration Service** (Python wrapper around lightrag-hku)
   - Wraps LightRAG core functionality
   - Exposes LightRAG Server for graph visualization UI
   - Manages Neo4j connections and graph operations

3. **RAG-Anything Integration Service** (Python wrapper around raganything)
   - Handles multi-format document parsing
   - Extracts text, images, tables, equations
   - Provides parsed content to LightRAG service

4. **Neo4j Database** (Official Neo4j Docker image)
   - Graph + vector storage
   - Persists entities, relationships, embeddings
   - Provides Neo4j Browser UI

5. **LiteLLM Proxy** (Optional, official LiteLLM Docker image)
   - OpenAI-compatible API proxy for enterprise LLMs
   - Optional dependency—users can configure direct LLM endpoints

**Inter-Service Communication:**
- Docker internal networking (service name resolution)
- REST APIs between services (JSON over HTTP)
- Neo4j native protocol for database access

**Rationale:**
- **Upstream Integration**: Cleanly integrate LightRAG and RAG-Anything as separate concerns
- **Independent Scaling**: Services can be replicated independently in Phase 2 (Kubernetes)
- **Failure Isolation**: Document parsing failures don't crash graph retrieval service
- **Technology Flexibility**: Each service can use optimal technology stack (all Python for MVP simplicity)

**Trade-off:** Increased operational complexity vs. monolithic deployment, but necessary for clean integration of LightRAG and RAG-Anything as distinct upstream projects.

### Testing Requirements: **Unit + Integration Testing with Manual Testing Convenience**

**Testing Strategy:**

1. **Unit Tests** (pytest)
   - Test individual functions, Pydantic models, utility modules
   - Mock external dependencies (Neo4j, LLM APIs)
   - Target: 70%+ code coverage for core logic

2. **Integration Tests** (pytest with Docker Compose)
   - Test service-to-service communication
   - Test Neo4j data persistence and retrieval
   - Test end-to-end document ingestion → query workflows
   - Use pytest fixtures to manage test Docker environments

3. **Manual Testing Convenience Methods**
   - Provide CLI scripts for common testing scenarios (ingest test documents, run test queries)
   - Example: `./scripts/test-ingestion.sh` to populate knowledge base with sample documents
   - Docker Compose profiles for test data seeding

**Not in MVP Scope:**
- E2E browser testing (no custom UI to test)
- Performance/load testing infrastructure (manual benchmarking acceptable)
- Chaos engineering or fault injection testing

**Rationale:**
- Unit tests ensure correctness of integration logic (our code wrapping LightRAG/RAG-Anything)
- Integration tests validate Docker orchestration and service communication
- Manual testing tools essential for developer productivity during MVP phase
- E2E UI testing not needed (we're not building custom UIs)

### Additional Technical Assumptions and Requests

**Programming Language:**
- **Primary:** Python 3.11+ for all custom services (API, LightRAG integration, RAG-Anything integration)
- **Rationale:** LightRAG and RAG-Anything are Python libraries; maximize compatibility and simplify dependency management

**API Framework:**
- **FastAPI** for REST API service
- **Rationale:** Async support, automatic OpenAPI generation, production-ready, Python ecosystem standard for modern APIs

**Dependency Management:**
- **Poetry** or **pip-tools** for Python dependency locking
- **Rationale:** Reproducible builds, clear separation of direct vs. transitive dependencies

**Container Images:**
- **Base Images:** Official `python:3.11-slim` for custom services, official images for Neo4j and LiteLLM
- **Rationale:** Minimize image size, leverage official support and security updates

**Configuration Management:**
- **Environment Variables** via `.env` files for runtime configuration (LLM endpoints, API keys, ports)
- **YAML Schema Files** (optional) for complex configuration like custom entity types or metadata schemas
- **Rationale:** 12-factor app principles, Docker Compose native support for .env files

**LLM Integration:**
- **Primary Path:** LiteLLM proxy for OpenAI-compatible endpoints
- **Fallback:** Direct configuration of LLM endpoints in LightRAG configuration
- **Embedding Models:** sentence-transformers (local, e.g., `all-MiniLM-L6-v2`) for MVP; support OpenAI embeddings via LiteLLM
- **Rationale:** Flexibility for users with different LLM access patterns (cloud APIs, local Ollama, enterprise endpoints)

**Storage and Persistence:**
- **Neo4j Community Edition 5.x** with vector plugin for graph + vector storage
- **Docker Volumes** for Neo4j data persistence
- **Backup Strategy:** Document manual Neo4j dump/restore procedures for MVP; automated backups in Phase 2
- **Rationale:** Single database simplifies architecture; Neo4j Community Edition sufficient for 1k document scale

**Networking and Ports:**
- **API Service:** Port 8000 (configurable)
- **LightRAG Server UI:** Port 9621 (LightRAG Server default)
- **Neo4j Browser:** Port 7474 (Neo4j default HTTP)
- **Neo4j Bolt:** Port 7687 (Neo4j native protocol)
- **LiteLLM Proxy** (optional): Port 4000 (configurable)
- **Rationale:** Use upstream service defaults to minimize configuration; allow override via .env

**Security:**
- **Authentication:** API key-based authentication for RAG Engine API (simple Bearer token)
- **Secrets Management:** Environment variables for MVP; document integration with external secret managers for production
- **TLS/HTTPS:** Optional reverse proxy configuration documented for production deployments; HTTP acceptable for local MVP usage
- **Rationale:** Balance security with MVP simplicity; defer enterprise-grade security to Phase 2

**Logging and Observability:**
- **Logging:** Python `structlog` for structured JSON logging to stdout
- **Observability:** Docker Compose logs via `docker-compose logs`; Prometheus/Grafana deferred to Phase 2
- **Rationale:** Standard Docker logging sufficient for MVP troubleshooting

**CI/CD:**
- **GitHub Actions** for automated testing and Docker image builds
- **Docker Hub** or **GitHub Container Registry** for image distribution
- **Rationale:** Free for open-source projects, well-documented, community-standard

**Documentation:**
- **Markdown** documentation in `docs/` directory
- **OpenAPI Specification** auto-generated by FastAPI for API documentation
- **Rationale:** Simple, version-controlled, renders well on GitHub

**Open Source Licensing:**
- **MIT License** (preferred) or **Apache 2.0**
- **Rationale:** Permissive licensing aligns with community adoption goals; compatible with LightRAG (Apache 2.0) and RAG-Anything licensing

---

## User Journey Documentation

This section maps primary user workflows to epic sequences, ensuring all user touchpoints are covered and the epic structure delivers coherent end-to-end experiences.

### Journey 1: New User Onboarding (First-Time Deployment)

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

### Journey 2: Knowledge Base Population (Document Ingestion)

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

### Journey 3: Query and Retrieval Optimization

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

### Journey 4: Open-WebUI Integration

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

### Journey 5: Troubleshooting and Knowledge Base Management

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

## Integration Testing Strategy

This section defines the testing approach across unit, service integration, cross-epic integration, and end-to-end levels to ensure RAG Engine components work together correctly.

### Testing Levels

#### Level 1: Unit Tests (Per Service, Per Story)

**Scope:** Test individual functions, classes, and modules in isolation with mocked dependencies

**Framework:** pytest with fixtures and mocks (pytest-mock)

**Coverage Target:** 70%+ for core business logic

**Examples:**
- `shared/models/metadata.py`: Pydantic model validation tests
- `shared/utils/neo4j_client.py`: Connection pool logic with mocked Neo4j driver
- API routers: Endpoint logic with mocked service calls

**Execution:** Developers run locally during development, CI/CD runs on every commit

**Story Assignment:** Each story includes unit test acceptance criteria for new code

#### Level 2: Service Integration Tests (Within Epic Stories)

**Scope:** Test service-to-service communication and external dependency integration (Neo4j, LightRAG, RAG-Anything)

**Framework:** pytest with Docker Compose test environment (pytest-docker-compose)

**Test Environment:**
- Dedicated `docker-compose.test.yml` with test-specific configurations
- Ephemeral Neo4j database (cleared between test runs)
- Mock LLM endpoints (avoid external API calls in CI/CD)

**Examples:**
- **API → Neo4j** (Epic 1): Create test node via API, verify node exists in Neo4j, delete node
- **API → RAG-Anything** (Epic 2): Upload PDF via API, verify parsed content returned, check error handling for corrupt file
- **API → LightRAG** (Epic 3): Trigger graph construction via API, verify entities created in Neo4j, query graph traversal

**Execution:**
- Developers run locally via `pytest tests/integration/`
- CI/CD runs integration tests after unit tests pass
- Uses Docker Compose to spin up test environment

**Story Assignment:**
- Epic 1 Story 1.4: Neo4j connection integration test
- Epic 2 Story 2.1: RAG-Anything parsing integration test
- Epic 2 Story 2.3: Document ingestion API integration test (API → RAG-Anything → Storage)
- Epic 3 Story 3.1: LightRAG graph construction integration test (API → LightRAG → Neo4j)
- Epic 3 Story 3.4: Hybrid retrieval integration test (query → retrieval → results validation)

#### Level 3: Cross-Epic Integration Tests (Epic Boundary Validation)

**Scope:** Test data flow and functionality across multiple epics to ensure epic outputs become valid inputs for subsequent epics

**Framework:** pytest with full Docker Compose environment

**Test Scenarios:**

**Test: Epic 2 Output → Epic 3 Input**
- **Given:** Document ingested via Epic 2 ingestion API with metadata
- **When:** Epic 3 graph construction triggered
- **Then:**
  - Entities extracted from document content
  - Relationships created between entities
  - Document metadata preserved in Neo4j
  - Graph queryable via Epic 3 retrieval API

**Test: Epic 3 Output → Epic 3 Visualization**
- **Given:** Documents ingested and graph constructed (Epic 2 + 3)
- **When:** LightRAG Server UI accessed (Epic 3 Stories 3.7-3.10)
- **Then:**
  - Graph visualization displays entities and relationships
  - Metadata filters work in UI
  - Entity type filters reduce displayed nodes

**Test: Epic 4 API → Epic 5 Open-WebUI Integration**
- **Given:** RAG Engine API fully functional (Epics 1-4)
- **When:** Open-WebUI Function Pipeline queries API
- **Then:**
  - Query returns relevant results with metadata
  - Cited sources formatted correctly
  - Error handling graceful (API unavailable scenario)

**Execution:**
- Run manually during epic transitions (end of Epic 2, end of Epic 3, end of Epic 4)
- Automated in CI/CD for main branch merges
- Uses production-like Docker Compose configuration

**Story Assignment:**
- Epic 3 Story 3.1: Add cross-epic test validating Epic 2 → Epic 3 data flow
- Epic 3 Story 3.10: Add cross-epic test validating Epic 3 graph → visualization
- Epic 5 Story 5.1: Add cross-epic test validating Epic 4 → Epic 5 Open-WebUI integration

#### Level 4: End-to-End Tests (User Journey Validation)

**Scope:** Test complete user journeys from start to finish, simulating real user workflows

**Framework:** pytest with full production-like environment

**Test Scenarios (Map to User Journeys):**

**E2E Test 1: New User Onboarding**
1. Deploy RAG Engine with `docker-compose up`
2. Wait for all services healthy
3. Access health endpoint, Neo4j Browser, LightRAG Server, API docs
4. Verify all UIs load successfully

**E2E Test 2: Knowledge Base Population**
1. Define custom metadata schema (department, project)
2. Configure entity types (API, Service, Database)
3. Ingest 10 sample documents (mixed formats) with metadata via API
4. Wait for graph construction complete
5. Verify all documents listed in API
6. Open graph visualization, verify entities of custom types exist
7. Query graph stats, validate entity/relationship counts

**E2E Test 3: Query and Retrieval Optimization**
1. Ingest 100 documents (reuse test dataset)
2. Execute query without filters, measure latency
3. Execute query with metadata filter, measure latency, validate < 50% baseline
4. Compare retrieval modes (naive, local, global, hybrid)
5. Enable reranking, verify top result changes
6. Validate P95 latency < 2s across 100 queries

**E2E Test 4: Open-WebUI Integration**
1. Deploy RAG Engine and Open-WebUI
2. Install Function Pipeline
3. Configure API endpoint and key
4. Send query via Open-WebUI chat
5. Verify response with cited sources
6. Upload document via chat, verify ingestion
7. Query document content, verify retrieval

**Execution:**
- Story 5.5: MVP validation script implements E2E tests
- Run before release candidates
- Manual QA validation on target platforms (Linux, macOS, Windows WSL2)
- Performance benchmarking included in E2E Test 3

**Story Assignment:**
- Epic 5 Story 5.5: Implement all E2E tests as automated script `scripts/mvp-validation.sh`

### Test Data Management

**Sample Dataset:**
- Located in `tests/fixtures/sample-documents/`
- Includes: 5 PDFs, 5 Markdown files, 5 Python code files, 3 Word docs
- Sample metadata CSV for batch ingestion tests
- Domain-specific examples: technical documentation, research papers, business reports

**Test Environment Configuration:**
- `.env.test` file with test-specific settings (test database, mock LLM endpoints)
- `docker-compose.test.yml` with ephemeral volumes
- Test API keys for authentication tests

**Test Database Cleanup:**
- Before each integration/E2E test: Clear Neo4j database
- After test suite: Optional preserve mode for debugging (env var `PRESERVE_TEST_DB=true`)

### CI/CD Integration

**GitHub Actions Workflow:**

```yaml
name: Test Suite
on: [push, pull_request]
jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - Checkout code
      - Setup Python 3.11
      - Install dependencies
      - Run pytest tests/unit/ --cov
      - Upload coverage report

  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    steps:
      - Checkout code
      - Setup Docker Compose
      - Run docker-compose -f docker-compose.test.yml up -d
      - Run pytest tests/integration/
      - Teardown test environment

  e2e-tests:
    runs-on: ubuntu-latest
    needs: integration-tests
    if: github.ref == 'refs/heads/main'
    steps:
      - Checkout code
      - Run scripts/mvp-validation.sh
      - Upload benchmark results
```

---

## Epic List

**Epic 1: Foundation & Core Infrastructure**
Establish Docker-based project foundation with Neo4j integration, basic service orchestration, and health check endpoints. Deliver initial deployable system demonstrating service connectivity and graph database operations.

**Epic 2: Multi-Format Document Ingestion Pipeline**
Implement RAG-Anything integration for parsing multiple document formats (PDF, Markdown, HTML, Word, code files) with custom metadata support, batch ingestion capabilities, and schema migration.

**Epic 3: Graph-Based Retrieval, Knowledge Graph Construction & Visualization**
Integrate LightRAG for entity extraction, relationship mapping, hybrid retrieval (vector + graph + BM25), reranking pipeline, and expose graph visualization UI to deliver core RAG functionality with operational transparency.

**Epic 4: REST API & Integration Layer**
Develop unified FastAPI REST API with OpenAPI documentation, covering document ingestion, query/retrieval, knowledge base management, and metadata filtering endpoints.

**Epic 5: Open-WebUI Integration & Production Readiness**
Create Open-WebUI Function Pipeline for seamless integration, implement production-grade error handling, logging, and deployment documentation for end-to-end MVP validation.

---

## Epic 1: Foundation & Core Infrastructure

**Epic Goal:** Establish Docker-based project foundation with Neo4j integration, basic service orchestration, and health check endpoints. By the end of this epic, developers can run `docker-compose up`, verify all services are running correctly, and confirm Neo4j graph database connectivity. This epic delivers the minimal deployable infrastructure that subsequent epics will build upon.

### Story 1.1: Initialize Repository Structure and Docker Compose Configuration

**As a** developer,
**I want** a well-organized monorepo with Docker Compose orchestration,
**so that** I can clone the repository and understand the project structure immediately.

#### Acceptance Criteria

1. Repository contains the documented monorepo structure:
   - `docker-compose.yml` at root
   - `services/` directory with subdirectories for `api/`, `lightrag-integration/`, `rag-anything-integration/`
   - `shared/` directory with `models/`, `config/`, `utils/`
   - `tests/` directory for test code
   - `docs/` directory for documentation
   - `.env.example` with all required environment variables documented

2. `.gitignore` configured to exclude:
   - Python cache files (`__pycache__`, `*.pyc`)
   - Virtual environments (`venv/`, `.venv/`)
   - Docker volumes and local data directories
   - `.env` file (sensitive configuration)
   - IDE-specific files

3. `README.md` includes:
   - Project overview (1-2 paragraphs from brief)
   - Prerequisites (Docker 24.0+, Docker Compose V2)
   - Quick start instructions (`cp .env.example .env`, edit configuration, `docker-compose up`)
   - Link to full documentation in `docs/`

4. `LICENSE` file present (MIT or Apache 2.0)

5. `docker-compose.yml` skeleton defines service placeholders for: `api`, `lightrag-integration`, `rag-anything-integration`, `neo4j`, `litellm` (optional)

6. Each service directory contains:
   - `Dockerfile` (placeholder or initial implementation)
   - `requirements.txt` or `pyproject.toml` for Python dependencies
   - Basic directory structure (`app/`, `tests/`)

7. **BLOCKER #1 FIX:** `.env.example` file created at repository root with ALL configuration variables documented (see root `.env.example` file for complete template including Neo4j, LLM providers, embedding models, LiteLLM, LightRAG, RAG-Anything, metadata, reranking, logging, testing, backup, performance tuning, security, monitoring, and Docker network configuration)

8. Python dependency management tool selected: **Poetry** (recommended for monorepo) or **pip-tools** for reproducible builds and dependency locking

### Story 1.2: Deploy Neo4j with Vector Support and Verify Connectivity

**As a** developer,
**I want** Neo4j running in Docker with vector plugin enabled and persistent storage,
**so that** I can store and query graph data with vector embeddings.

#### Acceptance Criteria

1. `docker-compose.yml` includes Neo4j service configuration:
   - Uses official Neo4j 5.x Community Edition image
   - Exposes port 7474 (HTTP/Browser) and 7687 (Bolt protocol)
   - Configures Docker volume for data persistence (`neo4j-data` volume)
   - Sets required environment variables (NEO4J_AUTH for username/password)

2. Neo4j vector plugin is enabled and functional (verify via Cypher query)

3. Neo4j Browser UI is accessible at `http://localhost:7474` after `docker-compose up`

4. Connection test script (`scripts/test-neo4j-connection.py`) successfully:
   - Connects to Neo4j using Bolt protocol
   - Creates a test node with vector property
   - Queries the test node
   - Deletes test data
   - Returns success message

5. Documentation in `docs/neo4j-setup.md` covers:
   - Neo4j Browser access and default credentials
   - How to change NEO4J_AUTH credentials in `.env`
   - Volume backup and restore procedures
   - Troubleshooting common connection issues

6. `.env.example` includes Neo4j configuration variables:
   - `NEO4J_URI` (default: bolt://neo4j:7687)
   - `NEO4J_AUTH` (default: neo4j/password)
   - `NEO4J_DATABASE` (default: neo4j)
   - `NEO4J_dbms_memory_heap_initial__size` (default: 2g)
   - `NEO4J_dbms_memory_heap_max__size` (default: 4g, recommended 8g for larger knowledge bases)
   - `NEO4J_dbms_memory_pagecache_size` (default: 2g, recommended 4g for larger knowledge bases)

### Story 1.3: Create API Service with FastAPI and Health Check Endpoint

**As a** developer,
**I want** a FastAPI-based API service with a health check endpoint,
**so that** I can verify the API service is running and responsive.

#### Acceptance Criteria

1. `services/api/` contains working FastAPI application:
   - `app/main.py` with FastAPI app initialization
   - `app/routers/` directory for endpoint organization
   - `app/dependencies.py` for shared dependencies (database connections, etc.)
   - `app/config.py` for configuration management using Pydantic Settings

2. Health check endpoint `GET /health` returns:
   - Status code: 200
   - JSON response: `{"status": "healthy", "service": "rag-engine-api", "version": "0.1.0"}`

3. Root endpoint `GET /` returns:
   - Status code: 200
   - JSON response with API information and link to docs: `{"message": "RAG Engine API", "docs_url": "/docs", "version": "0.1.0"}`

4. OpenAPI documentation auto-generated by FastAPI accessible at:
   - Swagger UI: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`
   - OpenAPI JSON schema: `http://localhost:8000/openapi.json`

5. API service runs in Docker container defined in `services/api/Dockerfile`:
   - Based on `python:3.11-slim`
   - Installs dependencies from `requirements.txt`
   - Exposes port 8000
   - Runs with `uvicorn` ASGI server

6. `docker-compose.yml` includes API service configuration:
   - Builds from `services/api/Dockerfile`
   - Exposes port 8000 to host
   - Mounts source code as volume for development hot-reload
   - Sets environment variables from `.env`

7. `scripts/test-api-health.sh` successfully calls `/health` endpoint and validates response

### Story 1.4: Implement Service Health Monitoring and Neo4j Connection Verification

**As a** platform operator,
**I want** the API service to verify Neo4j connectivity and report all service health statuses,
**so that** I can quickly diagnose infrastructure issues.

#### Acceptance Criteria

1. Enhanced health check endpoint `GET /health` now returns:
   ```json
   {
     "status": "healthy",
     "service": "rag-engine-api",
     "version": "0.1.0",
     "dependencies": {
       "neo4j": {
         "status": "healthy",
         "response_time_ms": 45
       }
     },
     "timestamp": "2025-10-15T10:30:00Z"
   }
   ```

2. Health check performs active Neo4j connectivity test:
   - Attempts connection to Neo4j
   - Executes simple query (e.g., `RETURN 1`)
   - Measures response time
   - Returns "unhealthy" status if connection fails or timeout exceeds 5 seconds

3. If Neo4j is unreachable, health check returns:
   - Status code: 503 (Service Unavailable)
   - JSON response with `"status": "unhealthy"` and error details

4. `shared/utils/neo4j_client.py` implements reusable Neo4j connection manager:
   - Connection pooling
   - Connection retry logic (3 attempts with exponential backoff)
   - Graceful error handling with structured logging

5. API service logs health check failures with structured JSON logs including:
   - Timestamp
   - Log level (ERROR)
   - Service name
   - Error message and stack trace

6. Documentation updated in `docs/health-monitoring.md` explaining:
   - Health endpoint usage
   - Interpreting health check responses
   - Common failure modes and troubleshooting steps

### Story 1.5: Configure Structured Logging and Docker Compose Logging

**As a** developer,
**I want** structured JSON logging from all services visible via Docker Compose,
**so that** I can debug issues during development and troubleshoot production deployments.

#### Acceptance Criteria

1. API service implements structured logging using `structlog`:
   - All log messages output as JSON to stdout
   - Log entries include: timestamp, level, service_name, message, context (request_id, user_id when applicable)
   - Example log entry:
     ```json
     {"timestamp": "2025-10-15T10:30:00Z", "level": "info", "service": "api", "message": "Health check requested", "request_id": "abc123"}
     ```

2. `shared/utils/logging.py` provides centralized logging configuration:
   - Configures `structlog` with consistent formatting across services
   - Log level configurable via `LOG_LEVEL` environment variable (default: INFO)
   - Development mode adds pretty-printed logs (optional, via `LOG_FORMAT=console`)

3. Docker Compose configured for log management:
   - All services output logs to stdout/stderr
   - `docker-compose logs` displays logs from all services
   - `docker-compose logs -f api` follows logs for specific service

4. `.env.example` includes logging configuration:
   - `LOG_LEVEL` (default: INFO)
   - `LOG_FORMAT` (default: json, options: json|console)

5. Documentation in `docs/logging.md` covers:
   - Viewing logs with Docker Compose commands
   - Filtering logs by service or log level
   - Log message structure and common fields
   - Examples of typical log messages for debugging

6. API service logs key events:
   - Service startup and shutdown
   - Health check requests
   - Neo4j connection success/failure
   - Unhandled exceptions with stack traces

### Story 1.6: Create End-to-End Deployment Test and Documentation

**As a** new user,
**I want** comprehensive deployment documentation with validation steps,
**so that** I can successfully deploy RAG Engine on my first attempt.

#### Acceptance Criteria

1. `docs/deployment-guide.md` provides step-by-step deployment instructions:
   - Prerequisites verification (Docker version, available RAM/disk, ports)
   - Clone repository command
   - Configuration steps (copy `.env.example`, edit required variables)
   - Launch command (`docker-compose up -d`)
   - Verification steps (check service health, access Neo4j Browser, access API docs)
   - Shutdown and cleanup commands

2. `scripts/validate-deployment.sh` automated validation script:
   - Checks Docker and Docker Compose versions
   - Verifies required ports (7474, 7687, 8000) are available
   - Runs `docker-compose up -d`
   - Waits for all services to be healthy (polls `/health` endpoint)
   - Tests Neo4j Browser accessibility
   - Tests API documentation accessibility
   - Reports success or failure with detailed error messages

3. `docs/troubleshooting.md` covers common deployment issues:
   - Port already in use errors (how to change ports in `.env`)
   - Neo4j authentication failures (credential reset procedure)
   - Insufficient memory errors (Docker Desktop memory allocation)
   - Service startup timeout issues (network/firewall problems)
   - Platform-specific guidance (Linux, macOS, Windows WSL2)

4. README.md includes "Quick Validation" section:
   - Command to run validation script
   - Expected output showing all services healthy
   - Links to full deployment guide and troubleshooting docs

5. Deployment successfully tested on:
   - Ubuntu 22.04 (Linux)
   - macOS 14+ (Intel and Apple Silicon)
   - Windows 11 with WSL2 (Ubuntu 22.04)

6. All documentation uses consistent formatting:
   - Code blocks with syntax highlighting
   - Clear section headings
   - Inline links to related documentation
   - Warning/info callouts for critical information

---

## Epic 2: Multi-Format Document Ingestion Pipeline

**Epic Goal:** Integrate RAG-Anything for parsing multiple document formats (PDF, Markdown, HTML, Word, code files) with custom metadata support, batch ingestion capabilities, and schema migration. By the end of this epic, users can ingest documents through REST API endpoints, specify custom metadata fields, and verify successful ingestion through Neo4j.

### Story 2.1: Integrate RAG-Anything Library and Create Document Parsing Service

**As a** developer,
**I want** a containerized RAG-Anything parsing service that accepts documents and extracts structured content,
**so that** I can process multiple document formats consistently.

#### Acceptance Criteria

1. `services/rag-anything-integration/` contains RAG-Anything integration service with FastAPI endpoints
2. Service exposes endpoint `POST /parse` accepting document upload with multipart/form-data
3. Supported formats: PDF, Markdown (.md), HTML, Microsoft Word (.doc, .docx), Python (.py), JavaScript (.js), TypeScript (.ts), Java (.java), plain text (.txt)
4. Parse endpoint returns structured JSON with extracted content: text blocks, images (as base64 or references), tables, equations
5. Service runs in Docker container with RAG-Anything dependencies installed
6. `docker-compose.yml` includes `rag-anything-integration` service configuration
7. Integration tests verify parsing of sample documents for each supported format
8. Error handling for unsupported formats returns 400 with clear error message

### Story 2.2: Implement Metadata Schema Definition and Validation

**As a** knowledge base administrator,
**I want** to define custom metadata fields for my documents,
**so that** I can filter and organize documents by domain-specific attributes.

#### Acceptance Criteria

1. `shared/models/metadata.py` defines Pydantic models for metadata schema configuration
2. Schema supports field types: string, integer, date, boolean, tags (list of strings)
3. Schema definition file `config/metadata-schema.yaml` allows users to define custom fields with: field name, type, required/optional, default value, description
4. Example schema includes common fields: author, department, date_created, tags, project_name, category
5. API validates document metadata against schema on ingestion, returning 422 for invalid metadata
6. `.env.example` includes `METADATA_SCHEMA_PATH` configuration variable
7. Documentation in `docs/metadata-configuration.md` explains schema definition with examples

### Story 2.3: Create Document Ingestion API Endpoint with Metadata Support

**As a** RAG Engine user,
**I want** to upload documents via REST API with custom metadata,
**so that** I can populate my knowledge base programmatically.

#### Acceptance Criteria

1. API service exposes `POST /api/v1/documents/ingest` endpoint accepting:
   - Document file (multipart/form-data)
   - Metadata JSON object (validated against schema)
   - Optional: expected_entity_types (list of domain-specific entity types)
2. Endpoint orchestrates: RAG-Anything parsing → store raw parsed content → queue for LightRAG processing (Epic 3 dependency)
3. Response includes: document_id (UUID), ingestion_status ("parsing", "queued"), metadata confirmation
4. Parsed document content stored in Neo4j as temporary nodes pending graph construction
5. API handles file size limits (configurable, default 50MB) and returns 413 for oversized files
6. Rate limiting implemented (configurable, default 10 requests/minute per API key)
7. OpenAPI documentation updated with ingestion endpoint specification and examples
8. Integration test successfully ingests sample PDF with metadata

### Story 2.4: Implement Batch Document Ingestion and Progress Tracking

**As a** knowledge base administrator,
**I want** to upload multiple documents in a single batch operation,
**so that** I can efficiently populate large knowledge bases.

#### Acceptance Criteria

1. API endpoint `POST /api/v1/documents/ingest/batch` accepts:
   - Multiple document files (multipart/form-data, max 100 files per batch)
   - Optional: CSV/JSON file mapping filenames to metadata
2. Batch ingestion processes documents asynchronously, returning batch_id immediately
3. Endpoint `GET /api/v1/documents/ingest/batch/{batch_id}/status` returns:
   - total_documents, processed_count, failed_count, status ("in_progress", "completed", "partial_failure")
   - List of failed documents with error messages
4. Failed document ingestion doesn't block entire batch—partial success supported
5. Background task queue (using Python asyncio or simple queue) manages batch processing
6. Batch ingestion logs progress to structured logs for monitoring
7. Documentation in `docs/batch-ingestion.md` with CSV metadata format examples
8. Integration test verifies batch ingestion of 10 documents with mixed metadata

### Story 2.5: Create Entity Type Configuration and Pre-Ingestion Setup

**As a** domain specialist,
**I want** to specify expected entity types for my knowledge domain,
**so that** LightRAG extracts relevant entities during graph construction.

#### Acceptance Criteria

1. Configuration file `config/entity-types.yaml` allows defining custom entity types with: type_name, description, examples
2. Default entity types provided: person, organization, concept, product, location, technology, event, document
3. Entity types configuration loaded at service startup and accessible via API
4. API endpoint `GET /api/v1/config/entity-types` returns currently configured entity types
5. API endpoint `POST /api/v1/config/entity-types` allows adding new entity types (persisted to config file)
6. Entity types passed to LightRAG during graph construction (Epic 3 integration point)
7. `.env.example` includes `ENTITY_TYPES_CONFIG_PATH` variable
8. Documentation in `docs/entity-configuration.md` with domain-specific examples (legal, medical, technical documentation)

### Story 2.6: Implement Document Management API (List, Retrieve, Delete)

**As a** RAG Engine user,
**I want** to list, retrieve details, and delete ingested documents,
**so that** I can manage my knowledge base content.

#### Acceptance Criteria

1. API endpoint `GET /api/v1/documents` returns paginated list of documents with: document_id, filename, metadata, ingestion_date, status, size
2. Query parameters support filtering: metadata fields (e.g., `?department=engineering`), date ranges, status
3. API endpoint `GET /api/v1/documents/{document_id}` returns full document details including parsed content preview
4. API endpoint `DELETE /api/v1/documents/{document_id}` removes document and associated graph nodes/relationships from Neo4j
5. Delete operation is idempotent—deleting non-existent document returns 204 (no error)
6. Document listing supports pagination with `limit` and `offset` parameters (default limit: 50, max: 500)
7. Neo4j queries optimized with indexes on document_id and metadata fields
8. Integration tests verify list filtering, document retrieval, and deletion workflows

### Story 2.7: Implement Metadata Schema Migration and Reindexing

**As a** knowledge base administrator,
**I want** to update my metadata schema and reindex existing documents,
**so that** I can adapt the knowledge base to evolving organizational needs without redeployment.

#### Acceptance Criteria

1. API endpoint `PUT /api/v1/config/metadata-schema` accepts updated metadata schema YAML/JSON and persists to `config/metadata-schema.yaml`

2. Schema validation ensures backward compatibility:
   - New fields must be optional or have defaults
   - Existing required fields cannot be removed
   - Field type changes rejected (breaking change)

3. Schema update triggers reindexing workflow:
   - Option 1 (immediate): Automatically reindex all documents in background
   - Option 2 (deferred): Mark schema as "pending reindex," user triggers manually

4. API endpoint `POST /api/v1/documents/reindex` triggers reindexing:
   - Accepts optional filters (document IDs, date ranges, metadata criteria)
   - Returns reindex_job_id for progress tracking
   - Reindexing updates document metadata fields without re-parsing content

5. API endpoint `GET /api/v1/documents/reindex/{job_id}/status` returns:
   - total_documents, processed_count, failed_count, status ("in_progress", "completed", "failed")
   - Estimated time remaining

6. Existing documents with missing new optional fields use schema defaults

7. Schema changes logged with timestamp, user, and change description to audit log

8. Documentation in `docs/schema-migration.md` explains:
   - When to use metadata schema updates
   - Backward compatibility requirements
   - Reindexing workflow and performance considerations
   - Examples of common schema evolutions

---

## Epic 3: Graph-Based Retrieval, Knowledge Graph Construction & Visualization

**Epic Goal:** Integrate LightRAG for entity extraction, relationship mapping, hybrid retrieval (vector + graph + BM25), reranking pipeline, and expose graph visualization UI to deliver core RAG functionality with operational transparency. Users can query the knowledge base and receive relevant results leveraging graph-based retrieval superior to simple vector search.

### Story 3.1: Integrate LightRAG Core Library and Initialize Graph Storage

**As a** developer,
**I want** LightRAG integrated with Neo4j for graph-based knowledge representation,
**so that** documents are transformed into entity-relationship graphs.

#### Acceptance Criteria

1. `services/lightrag-integration/` contains LightRAG integration service
2. Service initializes LightRAG instance with Neo4j storage backend configuration
3. LightRAG configuration includes: Neo4j connection parameters, embedding model (sentence-transformers), LLM endpoint (via LiteLLM or direct)
4. Service exposes internal API endpoint `POST /build-graph` accepting parsed document content from RAG-Anything service
5. Graph construction extracts entities based on configured entity types (from Epic 2.5)
6. Extracted entities and relationships persisted to Neo4j with vector embeddings
7. `shared/utils/lightrag_client.py` provides reusable LightRAG client wrapper
8. Integration test verifies graph construction for sample document, validates entities exist in Neo4j

### Story 3.2: Implement Entity Extraction with Custom Entity Types

**As a** domain specialist,
**I want** LightRAG to extract domain-specific entities from my documents,
**so that** the knowledge graph reflects my specialized terminology.

#### Acceptance Criteria

1. LightRAG entity extraction uses configured entity types from `entity-types.yaml` (Epic 2.5)
2. LLM prompt engineering includes entity type descriptions and examples for improved extraction accuracy
3. Extracted entities include: entity_type, entity_name, confidence_score, source_document_id, text_span (where entity was found)
4. Neo4j graph schema: Entity nodes with properties (name, type, embedding), Document nodes, CONTAINS relationships
5. Duplicate entity resolution: entities with similar names (fuzzy matching >90% similarity) merged into single node
6. Entity extraction logs include: document_id, entities_extracted_count, extraction_duration
7. Validation query in Neo4j confirms entities of all configured types are being created
8. Integration test with technical documentation verifies custom entity types (API, Service, Database) are extracted

### Story 3.3: Implement Relationship Mapping and Graph Construction

**As a** knowledge seeker,
**I want** LightRAG to discover relationships between entities across documents,
**so that** I can explore connected knowledge through graph traversal.

#### Acceptance Criteria

1. LightRAG extracts relationships between entities with: relationship_type, source_entity, target_entity, confidence_score
2. Relationship types include: MENTIONS, RELATED_TO, PART_OF, IMPLEMENTS, DEPENDS_ON, LOCATED_IN, AUTHORED_BY (extensible)
3. Neo4j graph schema extended: Relationship edges between Entity nodes with properties (type, confidence, source_document_id)
4. Cross-document relationships: entities mentioned in multiple documents connected through graph
5. Graph construction preserves document hierarchy: Document → Section → Entity relationships
6. Performance optimization: batch entity/relationship creation in Neo4j (transactions of 100 entities)
7. Graph statistics endpoint `GET /api/v1/graph/stats` returns: total_entities, total_relationships, entity_type_distribution
8. Integration test verifies relationships exist between entities from same document and cross-document relationships

### Story 3.4: Implement Hybrid Retrieval Pipeline (Vector + Graph + BM25)

**As a** RAG Engine user,
**I want** queries to leverage vector similarity, graph traversal, and keyword matching,
**so that** retrieval results are more accurate than single-method approaches.

#### Acceptance Criteria

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

### Story 3.5: Implement Metadata-Based Pre-Filtering for Retrieval

**As a** knowledge base user,
**I want** to filter retrieval by metadata fields before searching,
**so that** queries are faster and more precise by searching only relevant documents.

#### Acceptance Criteria

1. Query endpoint accepts `metadata_filters` parameter with JSON object: `{"department": "engineering", "date": {"gte": "2024-01-01"}}`
2. Filter operators supported: equality, inequality, date ranges (`gte`, `lte`), tag inclusion (`in`), boolean logic (`AND`, `OR`)
3. Pre-filtering applies Neo4j Cypher query constraints before retrieval, narrowing search space
4. Filtered retrieval returns only results from documents matching metadata criteria
5. Query response includes `filtered_document_count` showing how many documents matched metadata filters
6. Performance improvement: metadata filtering on 20% of knowledge base demonstrates 40%+ latency reduction vs. unfiltered
7. Neo4j indexes created on common metadata fields (department, date_created, project_name) for performance
8. Integration test verifies metadata filtering with complex queries (AND/OR logic, date ranges)

### Story 3.6: Integrate Reranking Pipeline for Result Refinement

**As a** knowledge seeker,
**I want** retrieval results reranked by relevance to my query,
**so that** the most useful results appear first.

#### Acceptance Criteria

1. Reranking service integrated using open-source cross-encoder: Jina AI reranker (`jina-reranker-v2-base-multilingual`) or MS Marco (`ms-marco-MiniLM-L-12-v2`)
2. Query endpoint accepts `rerank` parameter (boolean, default: false for MVP)
3. Reranking applied to top-k retrieval results (configurable, default: rerank top 50, return top 10)
4. Reranked results include: original_score (from retrieval), rerank_score, final_rank
5. Reranking model runs locally (no external API calls) for privacy
6. Reranking adds <500ms latency to query pipeline (measured on 50 candidates)
7. Configuration in `.env`: `RERANKER_MODEL`, `RERANKER_ENABLED` (default: false for performance)
8. Integration test validates reranking changes result order, top result after reranking has higher relevance than before

### Story 3.7: Deploy LightRAG Server as Docker Service

**As a** knowledge base explorer,
**I want** LightRAG Server's graph visualization UI accessible through my browser,
**so that** I can visually explore the knowledge graph structure.

#### Acceptance Criteria

1. `docker-compose.yml` includes `lightrag-server` service configuration using LightRAG Server
2. LightRAG Server exposed on port 9621 (configurable via `.env`: `LIGHTRAG_SERVER_PORT`)
3. LightRAG Server configured to connect to shared Neo4j instance
4. Web UI accessible at `http://localhost:9621` after `docker-compose up`
5. UI displays: graph visualization canvas, document list, query interface, settings panel
6. Service health check verifies LightRAG Server is responding
7. Documentation in `docs/graph-visualization.md` with screenshots and usage guide
8. Manual test verifies UI loads and displays graph after documents are ingested (Epic 2 + Epic 3)

### Story 3.8: Configure Neo4j Browser Access and Documentation

**As a** developer,
**I want** direct access to Neo4j Browser for database inspection,
**so that** I can debug graph structure and run custom Cypher queries.

#### Acceptance Criteria

1. Neo4j Browser accessible at `http://localhost:7474` (configured in Epic 1.2)
2. Documentation in `docs/neo4j-browser-guide.md` covering:
   - Accessing Neo4j Browser and authentication
   - Common Cypher queries for inspecting documents, entities, relationships
   - Example queries: "Show all entities of type X", "Find relationships between entities", "Count documents by metadata field"
3. Example Cypher query collection in `docs/example-queries.cypher`
4. Screenshots showing graph schema visualization in Neo4j Browser
5. Troubleshooting section for authentication issues and connection failures
6. Query performance tips: using indexes, limiting result sizes

### Story 3.9: Document Graph Exploration Workflows

**As a** knowledge base user,
**I want** clear guidance on exploring the knowledge graph visually,
**so that** I understand how documents are connected and validate retrieval quality.

#### Acceptance Criteria

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

### Story 3.10: Implement Graph Metadata and Entity Type Filtering

**As a** knowledge graph explorer,
**I want** to filter the graph visualization by metadata fields and entity types,
**so that** I can focus on specific subsets of knowledge.

#### Acceptance Criteria

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

### Story 3.11: Implement Entity Type Schema Evolution and Re-Extraction

**As a** domain specialist,
**I want** to add new entity types without losing existing graph data,
**so that** I can refine entity extraction as my understanding of the domain improves.

#### Acceptance Criteria

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

## Epic 4: REST API & Integration Layer

**Epic Goal:** Develop unified FastAPI REST API with OpenAPI documentation, covering document ingestion, query/retrieval, knowledge base management, and metadata filtering endpoints. API provides developer-friendly integration surface abstracting LightRAG and RAG-Anything complexity.

### Story 4.1: Consolidate API Endpoints and Create Unified API Gateway

**As a** API consumer,
**I want** a single API gateway with consistent endpoint patterns,
**so that** I have a unified interface for all RAG Engine operations.

#### Acceptance Criteria

1. API service orchestrates calls to `lightrag-integration` and `rag-anything-integration` services
2. All API endpoints follow RESTful conventions: `/api/v1/{resource}` pattern
3. Endpoints organized by routers: `documents.py`, `query.py`, `graph.py`, `config.py`
4. Consistent error response format: `{"error": "error_code", "message": "human-readable message", "details": {...}}`
5. HTTP status codes used correctly: 200 (success), 201 (created), 400 (bad request), 401 (unauthorized), 404 (not found), 422 (validation error), 500 (internal error)
6. All endpoints require API key authentication via `Authorization: Bearer <api_key>` header
7. API versioning via URL path (`/api/v1/`) for future compatibility
8. OpenAPI spec updated with all endpoints, request/response schemas, authentication requirements

### Story 4.2: Implement API Authentication and Rate Limiting

**As a** platform operator,
**I want** API key-based authentication and rate limiting,
**so that** I can control access and prevent abuse.

#### Acceptance Criteria

1. API keys generated via admin script: `scripts/generate-api-key.sh` (stores in `.env` or database)
2. Authentication middleware validates API key on all endpoints (except `/health` and `/docs`)
3. Invalid or missing API key returns 401 with `{"error": "unauthorized", "message": "Invalid or missing API key"}`
4. Rate limiting implemented: default 100 requests/minute per API key (configurable via `.env`: `RATE_LIMIT_PER_MINUTE`)
5. Rate limit exceeded returns 429 with `{"error": "rate_limit_exceeded", "message": "Rate limit of 100 requests/minute exceeded", "retry_after": 30}`
6. Rate limit headers included in responses: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`
7. Documentation in `docs/authentication.md` explains API key generation, usage, and rate limiting
8. Integration test verifies authentication enforcement and rate limiting behavior

### Story 4.3: Create Comprehensive OpenAPI Specification and Interactive Docs

**As a** developer integrating RAG Engine,
**I want** complete API documentation with examples and interactive testing,
**so that** I can understand and test endpoints without reading code.

#### Acceptance Criteria

1. OpenAPI 3.0 specification generated by FastAPI includes:
   - All endpoints with descriptions
   - Request/response schemas with examples
   - Authentication requirements
   - Error response schemas
2. Example requests/responses for each endpoint showing realistic data
3. Swagger UI (`/docs`) allows testing endpoints with API key authentication
4. ReDoc UI (`/redoc`) provides alternative documentation view
5. OpenAPI JSON downloadable at `/openapi.json` for code generation tools
6. Custom OpenAPI metadata: title ("RAG Engine API"), description, version, contact information
7. Documentation includes common workflow examples: "Ingest and query a document", "Batch upload with metadata"
8. API changelog maintained in `docs/api-changelog.md` for version tracking

### Story 4.4: Implement Request Validation and Error Handling

**As a** API consumer,
**I want** clear validation errors and helpful error messages,
**so that** I can quickly fix invalid requests.

#### Acceptance Criteria

1. Pydantic models used for all request/response validation with field descriptions and examples
2. Validation errors return 422 with detailed field-level errors:
   ```json
   {"error": "validation_error", "message": "Request validation failed", "details": [{"field": "metadata.date", "error": "Invalid date format, expected YYYY-MM-DD"}]}
   ```
3. Business logic errors return appropriate status codes with clear messages (e.g., 404 for document not found, 409 for duplicate entity)
4. Internal errors (500) logged with stack traces but return generic error message to client for security
5. Custom exception handlers for common error scenarios: Neo4j connection failures, LLM timeout, parsing errors
6. Error responses include `request_id` for tracing in logs
7. Documentation in `docs/error-handling.md` lists common errors with resolution steps
8. Integration tests verify error handling for invalid requests, missing documents, service failures

### Story 4.5: Create API Client Examples and Integration Guides

**As a** developer,
**I want** code examples in multiple languages,
**so that** I can quickly integrate RAG Engine into my application.

#### Acceptance Criteria

1. `docs/api-examples/` contains working code examples in:
   - Python (using `requests` library)
   - JavaScript/Node.js (using `fetch` or `axios`)
   - cURL commands for command-line testing
2. Examples cover common scenarios:
   - Authenticate and ingest a document
   - Query knowledge base with metadata filtering
   - Batch upload documents with CSV metadata
   - Retrieve and delete documents
3. Each example includes: setup instructions, complete working code, expected output
4. Python example can be run as standalone script: `python docs/api-examples/python-ingest-query.py`
5. Examples use realistic sample documents and metadata
6. Documentation in `docs/integration-guide.md` provides architecture overview for integration planning
7. Examples hosted in repository and tested in CI/CD to ensure they remain functional

---

## Epic 5: Open-WebUI Integration & Production Readiness

**Epic Goal:** Create Open-WebUI Function Pipeline for seamless integration, implement production-grade error handling, logging, and deployment documentation for end-to-end MVP validation. Delivers primary user integration and production deployment readiness.

### Story 5.1: Develop Open-WebUI Function Pipeline

**As a** Open-WebUI user,
**I want** to deploy RAG Engine as a function pipeline in Open-WebUI,
**so that** I can query my knowledge base through Open-WebUI's chat interface.

#### Acceptance Criteria

1. Python function file `integrations/open-webui/rag_engine_pipeline.py` implements Open-WebUI Function interface
2. Function provides: document ingestion (via file upload in chat), knowledge base query (via chat messages), metadata filtering (via function parameters)
3. Function configuration includes: RAG Engine API endpoint, API key, retrieval mode selection, reranking toggle
4. Function returns formatted responses: cited sources with document names, relevance scores, metadata tags
5. Error handling: graceful degradation if RAG Engine unavailable, user-friendly error messages in chat
6. Installation instructions in `integrations/open-webui/README.md`:
   - Deploy RAG Engine via Docker Compose
   - Copy function file to Open-WebUI functions directory
   - Configure API endpoint and key in function settings
7. Screenshots showing Open-WebUI integration in action
8. Manual test verifies end-to-end workflow: upload document in Open-WebUI → query → receive cited results

### Story 5.2: Implement Production-Grade Error Handling and Retry Logic

**As a** platform operator,
**I want** automatic retry logic and graceful error recovery,
**so that** transient failures don't break user workflows.

#### Acceptance Criteria

1. All external service calls (Neo4j, LightRAG, RAG-Anything, LLM) wrapped with retry logic:
   - Exponential backoff: 1s, 2s, 4s delays
   - Max 3 retry attempts
   - Retry only on transient errors (connection timeout, 503 service unavailable)
2. Circuit breaker pattern for LLM calls: after 5 consecutive failures, stop calling LLM for 60 seconds (fail fast)
3. Graceful degradation: if reranking service fails, return non-reranked results with warning
4. Error logging includes: error type, retry attempts, service name, request context
5. Health check detects degraded service states and reports in `/health` endpoint
6. Configuration in `.env`: `RETRY_MAX_ATTEMPTS`, `CIRCUIT_BREAKER_THRESHOLD`, `CIRCUIT_BREAKER_TIMEOUT`
7. Integration tests simulate service failures and verify retry/fallback behavior

### Story 5.3: Implement Monitoring Endpoints and Operational Metrics

**As a** platform operator,
**I want** monitoring endpoints exposing operational metrics,
**so that** I can track system health and performance.

#### Acceptance Criteria

1. Metrics endpoint `GET /api/v1/metrics` returns JSON with:
   - Request counts by endpoint (last hour, last day)
   - Average response times per endpoint
   - Error rates by error type
   - Knowledge base statistics (documents, entities, relationships)
   - Neo4j database size and query performance metrics
2. Prometheus-compatible metrics endpoint `GET /metrics` (using `prometheus-client` library) for future integration
3. Metrics include labels: endpoint, status_code, error_type
4. Performance counters: total_queries, successful_retrievals, failed_retrievals, avg_retrieval_latency_ms
5. System resource metrics: memory usage, CPU usage (via psutil)
6. Documentation in `docs/monitoring.md` explains metrics and alerting recommendations
7. Metrics endpoint requires authentication (same API key mechanism)

### Story 5.4: Create Production Deployment Documentation

**As a** production operator,
**I want** comprehensive deployment documentation for production environments,
**so that** I can deploy RAG Engine securely and reliably.

#### Acceptance Criteria

1. `docs/production-deployment.md` covers:
   - Hardware requirements (CPU, RAM, storage) for different knowledge base sizes
   - Security hardening: API key rotation, TLS setup with reverse proxy (nginx example), network isolation
   - Backup and disaster recovery: Neo4j backup procedures, automated backup scripts
   - Scaling recommendations: when to upgrade hardware, multi-node deployment considerations (preview for Phase 2)
2. Example production `docker-compose.prod.yml` with:
   - Resource limits (memory, CPU) for each service
   - Health check configurations
   - Restart policies (always restart on failure)
   - Volume mount configurations for persistent storage
3. `scripts/backup-neo4j.sh` and `scripts/restore-neo4j.sh` for database backup/restore
4. Environment variable security: document using Docker secrets or external secret managers
5. Monitoring integration guidance: connecting Prometheus, log aggregation (ELK stack preview)
6. Troubleshooting section for production issues: OOM errors, disk space, network latency
7. Production checklist: security, backups, monitoring, documentation review

### Story 5.5: Conduct End-to-End MVP Validation and Performance Testing

**As a** product manager,
**I want** validation that all MVP success criteria are met,
**so that** I can confidently launch RAG Engine to users.

#### Acceptance Criteria

1. End-to-end validation script `scripts/mvp-validation.sh` tests complete user journey:
   - Deploy RAG Engine with `docker-compose up`
   - Ingest 100+ documents across multiple formats with custom metadata
   - Define custom entity types
   - Query knowledge base with metadata filtering
   - Verify retrieval results include relevant documents
   - Access graph visualization UI and explore knowledge graph
   - Measure query latency (P95 < 2s target)
2. Performance benchmark script `scripts/benchmark-retrieval.sh`:
   - Test query performance on 1000-document knowledge base
   - Measure latency with/without metadata filtering
   - Compare retrieval modes (naive, local, global, hybrid)
   - Validate 50%+ latency reduction with metadata filtering on 20% subset
   - Test retrieval quality using BEIR SciFact dataset (MRR > 0.80 target)
3. Benchmark results documented in `docs/performance-benchmarks.md`
4. MVP success criteria validation report:
   - ✅ Single-command deployment completes in <5 minutes
   - ✅ End-to-end workflow (ingest, query, visualize) completes in <30 minutes
   - ✅ P95 query latency <2s on 1k document knowledge base
   - ✅ Retrieval quality improvement measured (comparison with baseline vector search, MRR > 0.80)
   - ✅ Open-WebUI integration functional
   - ✅ All documentation complete and tested
5. Known issues and limitations documented in `docs/known-issues.md`
6. Launch readiness checklist completed

### Story 5.6: Create User Onboarding Documentation and Quick Start Guide

**As a** new RAG Engine user,
**I want** a comprehensive quick start guide,
**so that** I can successfully deploy and use RAG Engine without prior knowledge.

#### Acceptance Criteria

1. `docs/quick-start-guide.md` provides:
   - 5-minute overview of RAG Engine capabilities
   - Prerequisites checklist (Docker, hardware, ports)
   - Step-by-step deployment instructions with screenshots
   - First-time usage tutorial: ingest sample documents, run example queries
   - Common customization: changing metadata schema, adding entity types
2. Sample dataset provided in `examples/sample-documents/`:
   - 10-20 documents across different formats (PDF, Markdown, code)
   - Sample metadata CSV for batch ingestion
   - Example query prompts with expected results
3. Video tutorial (screencast, 10-15 minutes) demonstrating:
   - Deployment process
   - Document ingestion via API
   - Querying via Open-WebUI
   - Graph visualization exploration
4. FAQ section in `docs/faq.md` addressing:
   - Choosing LLM providers (OpenAI, Ollama, local models)
   - Metadata schema design best practices
   - When to use different retrieval modes
   - Troubleshooting common errors
5. Community resources: link to Discord, GitHub Discussions, contribution guidelines
6. Feedback mechanism: issue templates for bugs, feature requests, documentation improvements

---

## Checklist Results Report

### Executive Summary

**Overall PRD Completeness:** 97% (after addressing High Priority recommendations)
**MVP Scope Appropriateness:** Just Right
**Readiness for Architecture Phase:** ✅ **READY**

**Improvements Made:**
- Added comprehensive User Journey Documentation (5 primary workflows)
- Added Integration Testing Strategy section (4 testing levels with CI/CD integration)
- Added schema migration stories (Story 2.7 for metadata, Story 3.11 for entity types)
- Clarified NFR2 measurement methodology (BEIR SciFact, MRR > 0.80)
- Merged Epic 4 (Visualization) into Epic 3 for better cohesion, reducing total epics from 6 to 5

**Key Strengths:**
- Complete end-to-end user journey coverage from deployment to production
- Comprehensive requirements grounded in actual LightRAG/RAG-Anything capabilities
- Well-structured epic breakdown with clear sequencing and dependencies
- Detailed acceptance criteria for all 36 user stories across 5 epics
- Strong technical foundation with clear architectural direction
- Realistic MVP scope focused on integration rather than building from scratch
- Holistic testing strategy covering unit, integration, cross-epic, and E2E tests

**Remaining Considerations:**
- Timeline: 4-6 months realistic for solo developer (not 3 months)
- Story 0.1 technical validation spike recommended before Epic 1 to validate LightRAG Server and RAG-Anything deployment approaches
- Epic 3 is largest/most complex—monitor progress closely for potential scope adjustments

### Category Analysis

| Category                         | Status     | Notes                                                                 |
| -------------------------------- | ---------- | --------------------------------------------------------------------- |
| 1. Problem Definition & Context  | **PASS**   | Well-articulated from brief, clear target users                       |
| 2. MVP Scope Definition          | **PASS**   | Appropriate scope with 5 epics, schema evolution added                |
| 3. User Experience Requirements  | **PASS**   | Comprehensive user journey documentation added                        |
| 4. Functional Requirements       | **PASS**   | Complete FR1-FR15 with clear traceability to stories                  |
| 5. Non-Functional Requirements   | **PASS**   | NFR2 measurement methodology clarified (BEIR, MRR)                    |
| 6. Epic & Story Structure        | **PASS**   | 5 epics, 36 stories, well-organized with schema migration            |
| 7. Technical Guidance            | **PASS**   | Comprehensive technical assumptions, recommend Story 0.1 spike        |
| 8. Cross-Functional Requirements | **PASS**   | Integration testing strategy added, schema evolution covered          |
| 9. Clarity & Communication       | **PASS**   | Clear, well-structured, handoff prompts ready for UX/Architect        |

### Final Decision

### ✅ **READY FOR ARCHITECT**

The PRD is **97% complete**, properly structured, and ready for architectural design. All high-priority recommendations have been addressed:

**Completed Improvements:**
1. ✅ User Journey Documentation - 5 comprehensive workflows mapping to epic sequences
2. ✅ Integration Testing Strategy - 4-level testing approach with CI/CD integration
3. ✅ Schema Migration Stories - Story 2.7 (metadata) and Story 3.11 (entity types)
4. ✅ NFR2 Clarification - BEIR SciFact benchmark, MRR > 0.80 measurement
5. ✅ Epic Consolidation - Merged Epic 4 into Epic 3, now 5 epics total

**Architect Can Proceed With:**
- Service architecture and API contract design
- Neo4j schema design (documents, entities, relationships, metadata)
- Docker Compose configuration and networking
- Configuration management (.env and YAML schema formats)
- Error handling patterns across service boundaries

**Recommended Next Steps:**
1. Handoff to Architect using provided prompt in Next Steps section
2. Consider Story 0.1 technical validation spike (4 hours) to prototype LightRAG Server and RAG-Anything deployment before Epic 1
3. Adjust project timeline to 4-6 months for realistic delivery

---

## Next Steps

### UX Expert Prompt

**Prompt for UX Expert:**

> Review the RAG Engine PRD (docs/prd.md) and Project Brief (docs/brief.md). Note that RAG Engine uses service-native UIs (LightRAG Server, Neo4j Browser) rather than custom UI development. Your focus should be on:
>
> 1. Evaluating the usability of exposing existing service UIs vs. building custom interfaces
> 2. Reviewing the User Journey Documentation section and identifying gaps or friction points
> 3. Creating user flow diagrams for the 5 primary user journeys documented in the PRD
> 4. Identifying UX gaps or friction points in the API-first + service-native UI approach
> 5. Recommending documentation improvements to compensate for lack of unified custom UI
>
> Begin UX analysis when ready.

### Architect Prompt

**Prompt for Architect:**

> Review the RAG Engine PRD (docs/prd.md), Project Brief (docs/brief.md), and source documentation for LightRAG and RAG-Anything (docs/sources/). Create the technical architecture document covering:
>
> 1. **Service Architecture**: Detailed service communication patterns, data flow diagrams, API contracts between RAG Engine API ↔ LightRAG Integration ↔ RAG-Anything Integration
> 2. **Neo4j Schema Design**: Complete graph schema with nodes (Document, Entity, Metadata), relationships, properties, indexes, constraints; support for both graph traversal and metadata filtering
> 3. **Docker Compose Service Definitions**: Container specifications, networking (internal Docker network), volumes (Neo4j persistence), environment variables, port exposure strategy
> 4. **Integration Patterns**: RAG-Anything parsed output → LightRAG graph input data contracts, API orchestration layer design, error propagation patterns
> 5. **Configuration Management**: .env file structure (all variables documented), YAML schema formats for metadata-schema.yaml and entity-types.yaml with validation rules
> 6. **Security Architecture**: API key authentication implementation, secret management approach, TLS termination strategies for production reverse proxy
> 7. **Monitoring and Observability**: Structured logging format (structlog JSON schema), metrics collection points, health check implementation details, integration with Prometheus (optional)
> 8. **Testing Infrastructure**: Docker Compose test environment setup (docker-compose.test.yml), test database lifecycle management, mock LLM endpoint configuration
>
> **Critical Questions to Address:**
> - Can LightRAG Server run as separate Docker service, or must it be embedded in lightrag-integration service?
> - Does RAG-Anything provide service/API mode, or must we wrap its Python library?
> - What are Neo4j memory configuration requirements for 1k document scale? (Recommend heap size, page cache)
>
> **Consider Story 0.1 Technical Spike:** Before finalizing architecture, recommend prototyping LightRAG Server + RAG-Anything deployment approaches to validate assumptions.
>
> Begin architecture design in create-architecture mode using this PRD as input.

---

**PRD Complete - Version 1.0**
