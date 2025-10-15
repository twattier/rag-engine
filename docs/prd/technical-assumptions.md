# Technical Assumptions

## Repository Structure: **Monorepo**

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

## Service Architecture: **Microservices within Docker Compose**

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

## Testing Requirements: **Unit + Integration Testing with Manual Testing Convenience**

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

## Additional Technical Assumptions and Requests

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
