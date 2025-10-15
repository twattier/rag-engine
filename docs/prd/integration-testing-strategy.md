# Integration Testing Strategy

This section defines the testing approach across unit, service integration, cross-epic integration, and end-to-end levels to ensure RAG Engine components work together correctly.

## Testing Levels

### Level 1: Unit Tests (Per Service, Per Story)

**Scope:** Test individual functions, classes, and modules in isolation with mocked dependencies

**Framework:** pytest with fixtures and mocks (pytest-mock)

**Coverage Target:** 70%+ for core business logic

**Examples:**
- `shared/models/metadata.py`: Pydantic model validation tests
- `shared/utils/neo4j_client.py`: Connection pool logic with mocked Neo4j driver
- API routers: Endpoint logic with mocked service calls

**Execution:** Developers run locally during development, CI/CD runs on every commit

**Story Assignment:** Each story includes unit test acceptance criteria for new code

### Level 2: Service Integration Tests (Within Epic Stories)

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

### Level 3: Cross-Epic Integration Tests (Epic Boundary Validation)

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

### Level 4: End-to-End Tests (User Journey Validation)

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

## Test Data Management

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

## CI/CD Integration

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
