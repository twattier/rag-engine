# Monitoring and Observability

## Monitoring Stack

- **Backend Monitoring:** Prometheus + Grafana (Phase 2)
  - FastAPI metrics exported via `prometheus-fastapi-instrumentator`
  - Custom metrics for query latency, document processing throughput
  - Neo4j metrics via official Prometheus exporter

- **Error Tracking:** Sentry (optional, Phase 2)
  - Automatic error capture from FastAPI exceptions
  - User context (API key, request path) attached to events
  - Release tracking for deployment correlation

- **Performance Monitoring:** Custom structlog + Grafana Loki
  - Structured JSON logs with request_id for distributed tracing
  - Query performance logs (latency per mode, top_k, etc.)
  - Neo4j slow query log integration

---

## Key Metrics

**Backend Metrics:**
- **Request Rate**: Total requests/second, by endpoint
- **Error Rate**: 4xx/5xx errors/second, by endpoint
- **Response Time**: P50, P95, P99 latency for all endpoints
  - Target: P95 < 2s for queries, P95 < 5s for document ingestion (initial response)
- **Database Query Performance**:
  - Cypher query latency (P50, P95, P99)
  - Vector search latency
  - Graph traversal latency
- **Document Processing**:
  - Documents ingested/hour
  - Average processing time per document
  - Success vs. failure rate
- **LLM API Usage**:
  - API calls/minute to LiteLLM
  - LLM response latency
  - Token consumption (input/output)
  - Cost per query (Phase 2)

**Infrastructure Metrics:**
- **Docker Containers**: CPU, memory, disk usage per service
- **Neo4j Database**:
  - Heap memory usage
  - Page cache hit ratio (target: >90%)
  - Transaction throughput
  - Store sizes (graph.db, vector indexes)
- **Volumes**: Disk usage for `neo4j_data`, `lightrag_storage`, `output`

**Business Metrics:**
- Total documents in knowledge base
- Total entities and relationships extracted
- Query volume by mode (local/global/hybrid/naive/mix)
- Average entities per document
- Average relationships per entity

---
