# Epic 4: REST API & Integration Layer

**Status:** Draft
**Epic Goal:** Develop unified FastAPI REST API with OpenAPI documentation, covering document ingestion, query/retrieval, knowledge base management, and metadata filtering endpoints. API provides developer-friendly integration surface abstracting LightRAG and RAG-Anything complexity.

---

## Stories in this Epic

### Story 4.1: Consolidate API Endpoints and Create Unified API Gateway
**As a** API consumer,
**I want** a single API gateway with consistent endpoint patterns,
**so that** I have a unified interface for all RAG Engine operations.

[Details in Story File: 4.1.api-gateway.md]

---

### Story 4.2: Implement API Authentication and Rate Limiting
**As a** platform operator,
**I want** API key-based authentication and rate limiting,
**so that** I can control access and prevent abuse.

[Details in Story File: 4.2.auth-rate-limiting.md]

---

### Story 4.3: Create Comprehensive OpenAPI Specification and Interactive Docs
**As a** developer integrating RAG Engine,
**I want** complete API documentation with examples and interactive testing,
**so that** I can understand and test endpoints without reading code.

[Details in Story File: 4.3.openapi-docs.md]

---

### Story 4.4: Implement Request Validation and Error Handling
**As a** API consumer,
**I want** clear validation errors and helpful error messages,
**so that** I can quickly fix invalid requests.

[Details in Story File: 4.4.validation-errors.md]

---

### Story 4.5: Create API Client Examples and Integration Guides
**As a** developer,
**I want** code examples in multiple languages,
**so that** I can quickly integrate RAG Engine into my application.

[Details in Story File: 4.5.client-examples.md]

---

## Epic Dependencies

**Depends On:**
- Epic 1: Foundation & Core Infrastructure (FastAPI service)
- Epic 2: Multi-Format Document Ingestion Pipeline (document endpoints)
- Epic 3: Graph-Based Retrieval & Knowledge Graph Construction (query/graph endpoints)

**Blocks:**
- Epic 5: Open-WebUI Integration & Production Readiness (requires complete API)

---

## Epic Acceptance Criteria

1. ✅ API Gateway consolidates all endpoints under `/api/v1` namespace
2. ✅ API key authentication implemented (optional for MVP, required for production)
3. ✅ Rate limiting configured (default: 100 requests/minute per API key)
4. ✅ OpenAPI 3.0 specification generated with all endpoints documented
5. ✅ Swagger UI at `/docs` and ReDoc at `/redoc` functional
6. ✅ Request validation returns 422 with detailed field-level errors
7. ✅ Error responses consistent with `ApiError` schema
8. ✅ Client examples created in Python, JavaScript/Node.js, and cURL
9. ✅ Integration guide published in `docs/integration-guide.md`
10. ✅ API changelog maintained in `docs/api-changelog.md`

---

## Technical Notes

### Key Technologies
- FastAPI 0.115+ for REST API
- Pydantic V2 for request/response validation and OpenAPI generation
- python-dotenv for API configuration
- Starlette middleware for CORS, logging, rate limiting
- httpx for inter-service communication (if services are split)

### API Versioning
- URL path versioning: `/api/v1/*`
- Future versions: `/api/v2/*` (backward compatible)

### Authentication (Phase 2 for MVP)
- API key via `Authorization: Bearer <api_key>` header
- Optional for MVP (local deployment)
- Required for production deployments

### Rate Limiting
- Default: 100 requests/minute per API key
- Configurable via `.env`: `RATE_LIMIT_PER_MINUTE`
- Rate limit headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`
- 429 status code when exceeded

### Error Response Format
```json
{
  "error": {
    "code": "validation_error",
    "message": "Request validation failed",
    "details": [
      {"field": "metadata.date", "error": "Invalid date format"}
    ],
    "timestamp": "2025-10-15T23:45:00Z",
    "requestId": "abc123"
  }
}
```

### HTTP Status Codes
- **200** OK - Successful request
- **201** Created - Resource created
- **202** Accepted - Async operation initiated
- **204** No Content - Successful deletion
- **400** Bad Request - Invalid request parameters
- **401** Unauthorized - Missing/invalid API key
- **404** Not Found - Resource not found
- **422** Unprocessable Entity - Validation error
- **429** Too Many Requests - Rate limit exceeded
- **500** Internal Server Error - Server error

### API Routers Organization
- `/api/v1/documents/*` - Document ingestion and management (Epic 2)
- `/api/v1/query` - RAG query endpoint (Epic 3)
- `/api/v1/graph/*` - Knowledge graph exploration (Epic 3)
- `/api/v1/config/*` - Configuration management (Epic 2)
- `/api/v1/health` - Health check (Epic 1)

### Critical Files Created
- `/services/api/routers/__init__.py` - Router consolidation
- `/services/api/middleware.py` - CORS, logging, error handling
- `/services/api/auth.py` - API key authentication (Phase 2)
- `/services/api/rate_limiter.py` - Rate limiting logic
- `/services/api/models/errors.py` - Error response models
- `/docs/api-examples/python-ingest-query.py` - Python example
- `/docs/api-examples/javascript-client.js` - JavaScript example
- `/docs/api-examples/curl-examples.sh` - cURL examples
- `/docs/integration-guide.md` - Integration guide
- `/docs/api-changelog.md` - API changelog

---

## Epic Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| API versioning breaking changes | Low | High | Strict backward compatibility policy, versioned endpoints |
| Rate limiting too restrictive | Medium | Medium | Configurable limits, clear documentation |
| Authentication complexity | Low | Medium | Defer to Phase 2 for MVP, document production setup |
| OpenAPI spec incomplete | Low | High | Automated generation from Pydantic models, validation tests |
| Client examples outdated | Medium | Low | Test examples in CI/CD, version control with API |

---

## Epic Definition of Done

- [ ] All 5 stories completed with acceptance criteria met
- [ ] API Gateway consolidates all endpoints with consistent patterns
- [ ] Authentication and rate limiting tested (even if optional for MVP)
- [ ] OpenAPI specification complete and accurate
- [ ] Swagger UI and ReDoc accessible and functional
- [ ] Request validation comprehensive with helpful error messages
- [ ] Client examples functional in Python, JavaScript, cURL
- [ ] Integration guide reviewed and complete
- [ ] API changelog initialized
- [ ] Demo: Test all endpoints via Swagger UI, run client examples

---

## Epic Metrics

- **Estimated Story Points:** 20 (based on 5 stories, ~4 points each)
- **Estimated Duration:** 1.5-2 weeks for solo developer
- **Key Performance Indicators:**
  - OpenAPI spec coverage: 100% of endpoints documented
  - Client example success rate: 100% (all examples run successfully)
  - API response time: <100ms for validation, <2s for retrieval
  - Error clarity score: >90% (manual review of error messages)

---

**Change Log:**

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-10-15 | 1.0 | Epic created from PRD | Sarah (PO Agent) |
