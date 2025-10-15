# Epic 1: Foundation & Core Infrastructure

**Status:** Ready for Development
**Epic Goal:** Establish Docker-based project foundation with Neo4j integration, basic service orchestration, and health check endpoints. By the end of this epic, developers can run `docker-compose up`, verify all services are running correctly, and confirm Neo4j graph database connectivity. This epic delivers the minimal deployable infrastructure that subsequent epics will build upon.

**PO Validation:** ✅ All story files created, `.env.example` template included, service naming standardized to `api`, `lightrag`, `rag-anything` (matching architecture document).

---

## Stories in this Epic

### Story 1.1: Initialize Repository Structure and Docker Compose Configuration
**As a** developer,
**I want** a well-organized monorepo with Docker Compose orchestration,
**so that** I can clone the repository and understand the project structure immediately.

[Details in Story File: 1.1.init-repository.md]

---

### Story 1.2: Deploy Neo4j with Vector Support and Verify Connectivity
**As a** developer,
**I want** Neo4j running in Docker with vector plugin enabled and persistent storage,
**so that** I can store and query graph data with vector embeddings.

[Details in Story File: 1.2.deploy-neo4j.md]

---

### Story 1.3: Create API Service with FastAPI and Health Check Endpoint
**As a** developer,
**I want** a FastAPI-based API service with a health check endpoint,
**so that** I can verify the API service is running and responsive.

[Details in Story File: 1.3.create-api-service.md]

---

### Story 1.4: Implement Service Health Monitoring and Neo4j Connection Verification
**As a** platform operator,
**I want** the API service to verify Neo4j connectivity and report all service health statuses,
**so that** I can quickly diagnose infrastructure issues.

[Details in Story File: 1.4.health-monitoring.md]

---

### Story 1.5: Configure Structured Logging and Docker Compose Logging
**As a** developer,
**I want** structured JSON logging from all services visible via Docker Compose,
**so that** I can debug issues during development and troubleshoot production deployments.

[Details in Story File: 1.5.structured-logging.md]

---

### Story 1.6: Create End-to-End Deployment Test and Documentation
**As a** new user,
**I want** comprehensive deployment documentation with validation steps,
**so that** I can successfully deploy RAG Engine on my first attempt.

[Details in Story File: 1.6.deployment-docs.md]

---

## Epic Dependencies

**Depends On:** None (Foundation epic)

**Blocks:**
- Epic 2: Multi-Format Document Ingestion Pipeline
- Epic 3: Graph-Based Retrieval & Knowledge Graph Construction
- Epic 4: REST API & Integration Layer
- Epic 5: Open-WebUI Integration & Production Readiness

---

## Epic Acceptance Criteria

1. ✅ Repository cloned and `docker-compose up` executes successfully
2. ✅ Neo4j accessible at `http://localhost:7474` (Browser) and `bolt://localhost:7687` (Driver)
3. ✅ FastAPI service accessible at `http://localhost:8000` with OpenAPI docs at `/docs`
4. ✅ `/health` endpoint returns healthy status for all services
5. ✅ Structured JSON logs visible via `docker-compose logs`
6. ✅ Deployment validation script (`scripts/validate-deployment.sh`) passes all checks
7. ✅ Documentation complete: README.md, deployment-guide.md, troubleshooting.md

---

## Technical Notes

### Key Technologies
- Docker Compose V2 for service orchestration
- Neo4j Community Edition 5.x with vector support
- FastAPI 0.115+ with Uvicorn ASGI server
- Python 3.11+ for all services
- structlog for structured logging
- python-dotenv for environment configuration

### Service Ports (Configurable in .env)
- Neo4j Bolt: 7687
- Neo4j HTTP: 7474
- FastAPI API: 8000

### Critical Files Created
- `/docker-compose.yml` - Service definitions
- `/.env.example` - Configuration template with ALL variables
- `/services/api/main.py` - FastAPI application
- `/shared/utils/neo4j_client.py` - Neo4j connection manager
- `/shared/utils/logging.py` - Logging configuration
- `/scripts/validate-deployment.sh` - Deployment validator

---

## Epic Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Neo4j vector plugin compatibility | Low | High | Test with Neo4j 5.x during Story 1.2 |
| Port conflicts on user systems | Medium | Medium | .env configuration, clear documentation |
| Docker memory limits | Medium | High | Document minimum requirements, validation script checks |
| Python dependency conflicts | Low | Medium | Use Poetry/pip-tools for dependency locking |

---

## Epic Definition of Done

- [ ] All 6 stories completed with acceptance criteria met
- [ ] Integration tests pass for Neo4j connectivity
- [ ] Health check endpoint functional
- [ ] Deployment validated on Linux, macOS, Windows WSL2
- [ ] Documentation reviewed and complete
- [ ] Code committed to main branch
- [ ] Demo: `docker-compose up` → health check → Neo4j Browser → API docs

---

## Epic Metrics

- **Estimated Story Points:** 21 (based on 6 stories, ~3-4 points each)
- **Estimated Duration:** 1.5-2 weeks for solo developer
- **Key Performance Indicators:**
  - Deployment time from clone to healthy: <5 minutes
  - Health check response time: <1 second
  - Zero critical bugs in foundation

---

**Change Log:**

| Date | Version | Description | Author |
|------|---------|-------------|--------|
| 2025-10-15 | 1.0 | Epic created from PRD | Sarah (PO Agent) |
