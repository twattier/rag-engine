# Security and Performance

## Security Requirements

**Backend Security:**
- **Input Validation**: All API requests validated via Pydantic schemas with strict type checking and format validation
- **Rate Limiting**: FastAPI Slowapi middleware with per-IP and per-API-key limits (100 req/min for MVP, configurable)
- **CORS Policy**:
  ```python
  # Restrictive CORS (production)
  CORS(
      app,
      allow_origins=["https://your-domain.com"],
      allow_methods=["GET", "POST", "DELETE"],
      allow_headers=["X-API-Key", "Content-Type"],
      allow_credentials=False
  )

  # Permissive CORS (development only)
  CORS(app, allow_origins=["*"])  # Development only!
  ```
- **SQL Injection Prevention**: N/A (using Neo4j with parameterized Cypher queries via driver)
- **Dependency Scanning**: Automated via Dependabot and `safety` CLI in CI/CD
- **Container Security**: Non-root users in Dockerfiles, minimal base images (python:3.11-slim), no secrets in images

**Authentication Security:**
- **Token Storage**: N/A for backend-only (clients manage API keys securely)
- **Session Management**: Stateless API (no sessions), API keys validated per-request
- **Password Policy**: N/A for MVP (API key auth only), Phase 2 OAuth2 will enforce:
  - Minimum 12 characters
  - Complexity requirements (upper, lower, digit, special)
  - Bcrypt hashing with cost factor 12

**Neo4j Security:**
- **Network Isolation**: Neo4j accessible only via Docker internal network (not exposed to host by default)
- **Authentication**: Strong password enforced (min 12 chars, complexity checked in setup script)
- **Encryption at Rest**: Optional via filesystem encryption (user's responsibility)
- **Encryption in Transit**: Bolt protocol over TLS (optional configuration, recommended for production)

**Secrets Management:**
- **Environment Variables**: Secrets loaded from `.env` (not committed to git)
- **Docker Secrets**: Recommended for production (docker-compose.prod.yml uses `secrets:` directive)
- **API Key Rotation**: Manual process (Phase 2: API for key management)

---

## Performance Optimization

**Backend Performance:**
- **Response Time Target**: P95 < 2 seconds for hybrid queries on 1k document knowledge base
- **Database Optimization**:
  - Neo4j indexes on `doc_id`, `entity_name`, `entity_type`, `metadata` fields
  - Vector indexes with cosine similarity for embedding search
  - Connection pooling with max 100 connections (configurable)
  - Query result caching in LightRAG LLM cache (enabled by default)
- **Caching Strategy**:
  - **LLM Cache**: LightRAG caches identical LLM prompts in `kv_store_llm_response_cache.json`
  - **Embedding Cache**: sentence-transformers caches embeddings in memory
  - **Query Result Cache (Phase 2)**: Redis for caching identical queries
  - **Document Cache**: Parsed documents stored in `output/` directory (reusable)
- **Async Operations**:
  - All API routes use `async def` for non-blocking I/O
  - Concurrent processing of entity/relationship/chunk retrieval
  - Background tasks for document ingestion (returns 202 immediately)
- **Resource Limits**: Docker Compose resource limits prevent memory leaks:
  ```yaml
  deploy:
    resources:
      limits:
        cpus: '4.0'
        memory: 8G
  ```

**Scaling Strategies (Phase 2):**
- **Horizontal Scaling**: Kubernetes with multiple API replicas behind load balancer
- **Read Replicas**: Neo4j clustering for read-heavy workloads
- **Sharding**: Partition knowledge base by metadata (e.g., by department, project)
- **GPU Acceleration**: Enable GPU for MinerU document parsing (10x speedup)

**Performance Monitoring:**
- **Metrics**: Prometheus scraping `/metrics` endpoint (FastAPI middleware)
- **Dashboards**: Grafana dashboards for:
  - API latency (P50, P95, P99)
  - Query throughput (requests/second)
  - Neo4j query performance (slow query log)
  - Memory/CPU usage per service
- **Alerts**: Alert on P95 latency > 5s, error rate > 5%, Neo4j down

---
