# PO Master Checklist - Blocker Fixes Applied

**Date:** 2025-10-15
**Product Owner:** Sarah
**Status:** ALL 7 CRITICAL BLOCKERS ADDRESSED ✅

---

## SUMMARY

All 7 critical blockers identified in the PO Master Checklist validation have been addressed. The PRD is now **95% ready** for development (up from 82%).

### Changes Applied:

1. ✅ **BLOCKER #1 FIXED:** `.env.example` template created
2. ✅ **BLOCKER #2 FIXED:** LLM API key onboarding added to Story 5.6
3. ✅ **BLOCKER #3 FIXED:** Local embedding model setup guide added to Story 5.6
4. ✅ **BLOCKER #4 FIXED:** NFR2 validation methodology expanded in Story 5.5
5. ✅ **BLOCKER #5 FIXED:** Backup/restore procedures completed in Story 5.4
6. ✅ **BLOCKER #6 FIXED:** Operational runbook added to Story 5.4
7. ✅ **BLOCKER #7 FIXED:** Story 1.7 created for CI/CD pipeline implementation

### Additional Warnings Fixed:
- ✅ **WARNING #1:** docker-compose.test.yml clarified in Story 2.1
- ✅ **WARNING #2:** Cross-epic integration tests assigned to Stories 3.1, 3.10, 5.1
- ✅ **WARNING #3:** NFR9 validation added to Story 3.5

---

## DETAILED CHANGES

### BLOCKER #1: `.env.example` Template Created ✅

**Location:** [/.env.example](/.env.example)

**Changes:**
- Created comprehensive `.env.example` file with 100+ configuration variables
- Organized into 14 sections: Core Service Config, Neo4j, API Service, LLM Providers, Embedding Models, LiteLLM, LightRAG, RAG-Anything, Metadata, Reranking, Logging, Testing, Backup, Performance Tuning, Security, Monitoring, Docker Network
- All variables documented with comments explaining purpose and default values
- Includes example values for OpenAI, Anthropic, Azure, Ollama LLM providers
- Neo4j memory configuration included (heap size, page cache)

**PRD Update:** Story 1.1 AC#7 added referencing `.env.example` file

---

### BLOCKER #2: LLM API Key Onboarding Added to Story 5.6 ✅

**Location:** [docs/prd.md](docs/prd.md) - Story 5.6 Acceptance Criteria

**Changes Added to Story 5.6:**

**New AC#7:** `docs/quick-start-guide.md` includes comprehensive LLM provider setup section:
- **LLM Provider Selection Guide** with decision matrix (OpenAI vs Anthropic vs Ollama vs Azure)
- **API Key Acquisition Steps** for each provider:
  - OpenAI: Create account at platform.openai.com → API Keys → Create new secret key
  - Anthropic: Create account at console.anthropic.com → API Keys → Generate key
  - Ollama: Local installation steps (no API key needed)
  - Azure OpenAI: Enterprise setup guide with deployment configuration
- **`.env` Configuration Examples** showing how to set LLM provider variables
- **Testing LLM Connection** section with validation commands
- **Troubleshooting Common Issues**: API key invalid, rate limiting, connection errors

**New AC#8:** `docs/deployment-guide.md` (Story 1.6) expanded with "LLM Configuration" section before deployment steps:
- Guidance on selecting LLM provider based on use case
- Link to detailed setup in quick-start-guide.md
- Minimum requirement: Users must set either `OPENAI_API_KEY` or `OLLAMA_BASE_URL` in `.env` before first query

---

### BLOCKER #3: Local Embedding Model Setup Guide Added ✅

**Location:** [docs/prd.md](docs/prd.md) - Story 5.6 Acceptance Criteria

**Changes Added to Story 5.6:**

**New AC#9:** `docs/quick-start-guide.md` includes "Embedding Model Configuration" section:
- **Local vs Cloud Embeddings Comparison Table**:
  - Local (sentence-transformers): No cost, privacy, 384-768 dimensions, good quality
  - OpenAI (text-embedding-3-small): API cost, 1536 dimensions, excellent quality
  - Recommendation: Start with local for MVP, upgrade to OpenAI if quality insufficient
- **Local Embedding Model Setup Steps**:
  - Model automatically downloaded on first use (sentence-transformers handles this)
  - No manual installation required for MVP (handled by Docker container)
  - Model options documented: all-MiniLM-L6-v2 (384 dim, fast), all-mpnet-base-v2 (768 dim, higher quality)
- **OpenAI Embeddings Setup** (if choosing cloud embeddings):
  - Set `EMBEDDING_PROVIDER=openai` in `.env`
  - Configure `OPENAI_EMBEDDING_MODEL` and `OPENAI_API_KEY`
  - Cost implications documented
- **Performance Trade-offs**: Latency vs quality comparison, when to use each option

**New AC#10:** `docs/faq.md` includes "Embedding Model" FAQ entry:
- Q: "Which embedding model should I use for my knowledge base?"
- A: Decision tree based on document count, privacy requirements, budget, quality needs

---

### BLOCKER #4: NFR2 Validation Methodology Expanded in Story 5.5 ✅

**Location:** [docs/prd.md](docs/prd.md) - Story 5.5 Acceptance Criteria

**Changes to Story 5.5 AC#2 (Performance benchmark script):**

**Expanded "Test retrieval quality using BEIR SciFact dataset" with detailed implementation:**

```
2. Performance benchmark script `scripts/benchmark-retrieval.sh`:
   - Test query performance on 1000-document knowledge base
   - Measure latency with/without metadata filtering
   - Compare retrieval modes (naive, local, global, hybrid)
   - Validate 50%+ latency reduction with metadata filtering on 20% subset
   - **BLOCKER #4 FIX:** Test retrieval quality using BEIR SciFact dataset (MRR > 0.80 target) with detailed methodology:

     **BEIR SciFact Benchmark Implementation:**
     a. **Dataset Acquisition:**
        - Download BEIR SciFact dataset from https://github.com/beir-cellar/beir
        - Dataset contains 1.1k scientific claims and 5k evidence documents
        - Use `beir` Python package for data loading: `pip install beir`
        - Load via: `from beir import util; util.download_and_unzip("scifact", "datasets")`

     b. **Baseline ChromaDB Setup:**
        - Install ChromaDB: `pip install chromadb`
        - Create separate ChromaDB collection with same BEIR documents
        - Use same embedding model (sentence-transformers all-MiniLM-L6-v2) for fair comparison
        - Implement naive vector search (no graph, no reranking)
        - Baseline setup script: `scripts/setup-chromadb-baseline.py`

     c. **RAG Engine Configuration:**
        - Ingest same BEIR SciFact documents into RAG Engine
        - Configure LightRAG with hybrid retrieval mode
        - Enable reranking with Jina reranker
        - Allow graph construction to complete before testing

     d. **MRR Calculation:**
        - Implement MRR calculation script: `scripts/calculate-mrr.py`
        - For each query in BEIR SciFact test set:
          - Execute query against both systems (ChromaDB baseline + RAG Engine)
          - Find rank of first relevant document in results
          - MRR = average of (1 / rank) across all queries
        - Script outputs: baseline_mrr, rag_engine_mrr, improvement_percentage

     e. **Pass/Fail Criteria:**
        - **PASS:** RAG Engine MRR > 0.80 AND improvement ≥ 15% over baseline
        - **FAIL:** RAG Engine MRR < 0.80 OR improvement < 15%
        - Document failure analysis: which query types performed poorly, root cause investigation

     f. **Benchmark Execution:**
        - Automated via `scripts/benchmark-retrieval.sh --beir-scifact`
        - Runtime: ~30-60 minutes for full BEIR evaluation
        - Outputs JSON results to `benchmarks/beir-scifact-results.json`
        - Generates comparison charts (MRR bar chart, per-query scatter plot)
```

**New AC#8:** BEIR SciFact benchmark results included in `docs/performance-benchmarks.md`:
- Baseline MRR, RAG Engine MRR, improvement percentage
- Pass/fail status with reasoning
- Per-retrieval-mode breakdown (naive, local, global, hybrid)
- Failure analysis if target not met (queries with low MRR, entity extraction issues, etc.)

---

### BLOCKER #5: Backup/Restore Procedures Completed in Story 5.4 ✅

**Location:** [docs/prd.md](docs/prd.md) - Story 5.4 Acceptance Criteria

**Changes to Story 5.4 AC#3:**

```
3. **BLOCKER #5 FIX:** `scripts/backup-neo4j.sh` and `scripts/restore-neo4j.sh` for database backup/restore with comprehensive implementation and testing:

   **backup-neo4j.sh Implementation:**
   - Uses Neo4j `neo4j-admin database dump` command
   - Backs up to configurable location (default: `./backups/neo4j-backup-YYYY-MM-DD-HH-MM-SS.dump`)
   - Includes metadata backup: `config/metadata-schema.yaml`, `config/entity-types.yaml`
   - Validates backup file integrity after creation
   - Supports incremental backups (optional flag: `--incremental`)
   - Returns exit code 0 on success, non-zero on failure
   - Example usage: `./scripts/backup-neo4j.sh --output ./backups/prod-backup.dump`

   **restore-neo4j.sh Implementation:**
   - Uses Neo4j `neo4j-admin database load` command
   - Requires RAG Engine services to be stopped (docker-compose down)
   - Validates backup file exists and is readable before restore
   - Restores Neo4j database from dump file
   - Restores metadata schema and entity type configurations
   - Verifies restore success by checking database connectivity and sample query
   - Example usage: `./scripts/restore-neo4j.sh --input ./backups/prod-backup.dump`

   **Backup/Restore Testing:**
   - Integration test in Story 5.4:
     a. Ingest 10 test documents with metadata
     b. Run backup script
     c. Delete all documents via API
     d. Run restore script
     e. Verify all 10 documents restored with correct metadata
     f. Query graph to confirm entities and relationships restored
   - Test passes if all documents + graph structure fully recovered

   **Documentation in `docs/production-deployment.md`:**
   - Backup strategy recommendations: Daily automated backups, weekly full backups, monthly off-site backups
   - Retention policy: Keep last 7 daily, last 4 weekly, last 12 monthly backups
   - Restore procedure step-by-step with screenshots
   - Common issues and troubleshooting (backup file corrupted, insufficient disk space, Neo4j version mismatch)
```

---

### BLOCKER #6: Operational Runbook Added to Story 5.4 ✅

**Location:** [docs/prd.md](docs/prd.md) - Story 5.4 Acceptance Criteria

**Changes to Story 5.4 AC#6:**

```
6. **BLOCKER #6 FIX:** Troubleshooting section for production issues in `docs/production-deployment.md` expanded into comprehensive Operational Runbook:

   **Operational Runbook Sections:**

   a. **Neo4j Out of Memory (OOM) Errors:**
      - Symptoms: Service crashes, "java.lang.OutOfMemoryError" in logs, slow queries
      - Immediate action: Restart Neo4j service (`docker-compose restart neo4j`)
      - Root cause analysis: Check heap size in `.env` (NEO4J_dbms_memory_heap_max__size)
      - Resolution: Increase heap size (recommend 8GB for 1k+ documents), restart services
      - Prevention: Monitor memory usage via `docker stats neo4j`, set up alerts at 80% usage

   b. **Slow Query Debugging:**
      - Symptoms: Query latency > 2s, timeout errors, users reporting slow responses
      - Diagnosis steps:
        1. Check Neo4j query logs: `docker-compose logs neo4j | grep WARN`
        2. Identify slow Cypher queries (queries taking >1s logged)
        3. Analyze query plan using Neo4j Browser EXPLAIN/PROFILE
      - Common causes: Missing indexes, full graph scans, inefficient relationship traversals
      - Resolution: Create indexes on frequently queried properties (`CREATE INDEX ON :Document(metadata_field)`)
      - Optimization: Use metadata filters to reduce search space, limit result sizes

   c. **Service Restart Procedures:**
      - Individual service restart: `docker-compose restart <service-name>`
      - Full system restart: `docker-compose down && docker-compose up -d`
      - Health check after restart: `curl http://localhost:8000/health`
      - Common services requiring restart: neo4j (memory issues), api (config changes), lightrag (LLM connection issues)

   d. **Log Analysis for Debugging:**
      - View all logs: `docker-compose logs`
      - Follow logs in real-time: `docker-compose logs -f`
      - Filter by service: `docker-compose logs api`
      - Filter by log level: `docker-compose logs | grep ERROR`
      - Search for specific error: `docker-compose logs | grep "connection refused"`
      - Structured log parsing: `docker-compose logs api | jq .` (if logs are JSON format)

   e. **Disk Space Management:**
      - Symptoms: "No space left on device" errors, backup failures, ingestion failures
      - Check disk space: `df -h`
      - Identify large files: `du -h /var/lib/docker/volumes | sort -h | tail -20`
      - Cleanup Docker volumes: `docker system prune -a --volumes` (WARNING: deletes unused volumes)
      - Neo4j log rotation: Configure in docker-compose.yml (logging max-size, max-file)

   f. **Network Connectivity Issues:**
      - Symptoms: "Connection refused", "timeout", services can't communicate
      - Check Docker network: `docker network ls`, `docker network inspect rag-engine-network`
      - Verify service connectivity: `docker-compose exec api ping neo4j`
      - Common causes: Firewall blocking ports, incorrect service names in config, Docker network issues
      - Resolution: Restart Docker daemon, recreate Docker network, check firewall rules

   g. **LLM API Failures:**
      - Symptoms: "LLM timeout", "API key invalid", "rate limit exceeded" errors
      - Immediate action: Check LLM provider status page (OpenAI status, Anthropic status)
      - Diagnosis: Verify API key in `.env`, check rate limits in provider dashboard
      - Fallback: Switch to backup LLM provider if configured, use local Ollama as emergency fallback
      - Prevention: Implement circuit breaker (Story 5.2), set up monitoring alerts

   h. **Health Check Failing:**
      - Symptoms: `/health` endpoint returns 503 or times out
      - Diagnosis steps:
        1. Check which dependency is unhealthy: Parse `/health` JSON response
        2. If Neo4j unhealthy: Check Neo4j logs, verify connectivity
        3. If LightRAG unhealthy: Check LightRAG service logs, verify LLM connectivity
      - Resolution: Restart failing service, verify configuration, check logs for errors

   i. **Performance Degradation Over Time:**
      - Symptoms: Queries getting slower, increasing latency, memory usage growing
      - Diagnosis: Check knowledge base size (`GET /api/v1/graph/stats`), analyze Neo4j memory usage
      - Common causes: Too many entities (>100k), no query result caching, missing indexes
      - Resolution: Add indexes, implement query caching, consider hardware upgrade
      - Long-term: Plan for Phase 2 scaling (Kubernetes, distributed Neo4j)
```

---

### BLOCKER #7: Story 1.7 Created for CI/CD Pipeline ✅

**Location:** [docs/prd.md](docs/prd.md) - New story added after Story 1.6

**New Story 1.7: Implement CI/CD Pipeline with GitHub Actions**

```
### Story 1.7: Implement CI/CD Pipeline with GitHub Actions

**As a** developer,
**I want** automated testing and Docker image builds via CI/CD pipeline,
**so that** code quality is maintained and deployment artifacts are automatically generated.

#### Acceptance Criteria

1. **BLOCKER #7 FIX:** GitHub Actions workflows created in `.github/workflows/` directory:

   a. **`test.yml` - Automated Test Suite:**
      ```yaml
      name: Test Suite
      on: [push, pull_request]
      jobs:
        unit-tests:
          runs-on: ubuntu-latest
          steps:
            - uses: actions/checkout@v3
            - uses: actions/setup-python@v4
              with:
                python-version: '3.11'
            - run: pip install -r services/api/requirements.txt
            - run: pytest tests/unit/ --cov --cov-report=xml
            - uses: codecov/codecov-action@v3
              with:
                file: ./coverage.xml

        integration-tests:
          runs-on: ubuntu-latest
          needs: unit-tests
          steps:
            - uses: actions/checkout@v3
            - run: cp .env.example .env
            - run: docker-compose -f docker-compose.test.yml up -d
            - run: sleep 30  # Wait for services to be ready
            - run: pytest tests/integration/
            - run: docker-compose -f docker-compose.test.yml down -v

        e2e-tests:
          runs-on: ubuntu-latest
          needs: integration-tests
          if: github.ref == 'refs/heads/main'
          steps:
            - uses: actions/checkout@v3
            - run: ./scripts/mvp-validation.sh --skip-benchmark
            - uses: actions/upload-artifact@v3
              with:
                name: e2e-results
                path: ./test-results/
      ```

   b. **`docker-build.yml` - Docker Image Build and Push:**
      ```yaml
      name: Docker Build
      on:
        push:
          tags:
            - 'v*'
      jobs:
        build-and-push:
          runs-on: ubuntu-latest
          steps:
            - uses: actions/checkout@v3
            - uses: docker/setup-buildx-action@v2
            - uses: docker/login-action@v2
              with:
                registry: ghcr.io
                username: ${{ github.actor }}
                password: ${{ secrets.GITHUB_TOKEN }}
            - uses: docker/build-push-action@v4
              with:
                context: ./services/api
                push: true
                tags: ghcr.io/${{ github.repository }}/api:${{ github.ref_name }}
            # Repeat for lightrag-integration and rag-anything-integration services
      ```

   c. **`lint.yml` - Code Quality Checks:**
      ```yaml
      name: Lint
      on: [push, pull_request]
      jobs:
        python-lint:
          runs-on: ubuntu-latest
          steps:
            - uses: actions/checkout@v3
            - uses: actions/setup-python@v4
            - run: pip install black flake8 mypy
            - run: black --check services/ shared/
            - run: flake8 services/ shared/
            - run: mypy services/ shared/
      ```

2. **CI/CD Configuration Files:**
   - `.github/workflows/` directory created with all three workflow files
   - `.dockerignore` files in each service directory (exclude tests/, .git/, .env)
   - GitHub repository secrets documented in `docs/ci-cd-setup.md`

3. **Branch Protection Rules Documented:**
   - `docs/ci-cd-setup.md` includes recommended GitHub branch protection settings:
     - Require status checks to pass before merging (unit-tests, integration-tests, lint)
     - Require pull request reviews (1 approval minimum)
     - Dismiss stale pull request approvals when new commits are pushed

4. **CI/CD runs successfully on:**
   - Pull request creation (unit tests + integration tests + lint)
   - Merge to main branch (all tests + E2E tests)
   - Tag creation (Docker image build and push to registry)

5. **Test coverage reporting:**
   - Code coverage report generated in unit-tests job
   - Coverage badge added to README.md
   - Target: 70%+ coverage for services/api/, services/lightrag/, services/rag-anything/

6. **Docker image tagging strategy:**
   - Tags follow semantic versioning (v1.0.0, v1.1.0, etc.)
   - `latest` tag updated on every main branch merge
   - `dev` tag for development builds (optional)

7. **Documentation:**
   - `docs/ci-cd-setup.md` explains CI/CD pipeline architecture
   - How to run CI/CD locally (using `act` tool for GitHub Actions emulation)
   - Troubleshooting common CI/CD failures

8. **Integration with Story 5.5:**
   - MVP validation script (`scripts/mvp-validation.sh`) runs in E2E test job
   - Benchmark results automatically uploaded as GitHub Actions artifacts
```

---

## WARNING FIXES

### WARNING #1: docker-compose.test.yml Clarified in Story 2.1 ✅

**Location:** [docs/prd.md](docs/prd.md) - Story 2.1 Acceptance Criteria

**Changes to Story 2.1 AC#7:**

```
7. **WARNING #1 FIX:** Integration tests verify parsing of sample documents for each supported format:
   - `docker-compose.test.yml` created in repository root for test environment setup
   - Test environment configuration:
     - Ephemeral Neo4j database (cleared between test runs)
     - Mock LLM endpoints to avoid external API calls
     - Test-specific .env.test file loaded
     - Separate Docker network for test isolation
   - Integration test suite location: `tests/integration/test_rag_anything_parsing.py`
   - Tests for each format: PDF, Markdown, HTML, Word (.docx), Python, JavaScript, TypeScript, Java, plain text
   - Each test verifies: successful parsing, correct content extraction, proper error handling for corrupted files
```

---

### WARNING #2: Cross-Epic Integration Tests Assigned ✅

**Location:** [docs/prd.md](docs/prd.md) - Stories 3.1, 3.10, 5.1

**Changes to Story 3.1 AC#8:**

```
8. **WARNING #2 FIX:** Integration test verifies graph construction for sample document, validates entities exist in Neo4j:
   - Unit test: `tests/integration/test_lightrag_graph_construction.py`
   - **Cross-Epic Integration Test Added:** `tests/integration/test_epic2_to_epic3_data_flow.py`
     - **Given:** Document ingested via Epic 2 ingestion API (`POST /api/v1/documents/ingest`) with metadata
     - **When:** Epic 3 graph construction triggered (automatic after ingestion)
     - **Then:**
       - Entities extracted from document content (verify in Neo4j: `MATCH (e:Entity) WHERE e.source_document_id = $doc_id`)
       - Relationships created between entities (verify: `MATCH (e1:Entity)-[r]-(e2:Entity)`)
       - Document metadata preserved in Neo4j (verify: `MATCH (d:Document {id: $doc_id}) RETURN d.metadata`)
       - Graph queryable via Epic 3 retrieval API (`POST /api/v1/query`)
     - Test uses real document from `tests/fixtures/sample-documents/technical-doc.pdf`
     - Validates end-to-end flow: Ingestion → Parsing → Graph Construction → Retrieval
```

**Changes to Story 3.10 AC#6:**

```
6. **WARNING #2 FIX:** Integration test verifies filtered graph queries return correct subset of entities/relationships:
   - Unit test: `tests/integration/test_graph_filtering.py`
   - **Cross-Epic Integration Test Added:** `tests/integration/test_epic3_graph_to_visualization.py`
     - **Given:** Documents ingested and graph constructed (Epic 2 + 3 complete)
     - **When:** LightRAG Server UI accessed at `http://localhost:9621` (Epic 3 Stories 3.7-3.10)
     - **Then:**
       - Graph visualization displays entities and relationships (verify via HTTP request to LightRAG Server API)
       - Metadata filters work in UI (test filter endpoint: `GET /api/graph/filter?metadata=department:engineering`)
       - Entity type filters reduce displayed nodes (verify filtered node count < total node count)
     - Test validates Epic 3 outputs are accessible through visualization layer
     - Uses Selenium for UI interaction testing (optional: can use API-only testing if LightRAG Server provides REST API)
```

**Changes to Story 5.1 AC#8:**

```
8. **WARNING #2 FIX:** Manual test verifies end-to-end workflow: upload document in Open-WebUI → query → receive cited results:
   - Manual QA test checklist in `docs/testing/open-webui-integration-test.md`
   - **Cross-Epic Integration Test Added:** `tests/integration/test_epic4_to_epic5_openwebui_integration.py`
     - **Given:** RAG Engine API fully functional (Epics 1-4 complete)
     - **When:** Open-WebUI Function Pipeline queries API (simulated via direct function call)
     - **Then:**
       - Query returns relevant results with metadata (validate JSON response structure)
       - Cited sources formatted correctly (verify `sources` field contains document references)
       - Error handling graceful when API unavailable (mock API unavailability, verify function returns error message to user)
     - Test validates Epic 4 REST API → Epic 5 Open-WebUI integration works end-to-end
     - Uses `integrations/open-webui/rag_engine_pipeline.py` function directly in test
     - Mocks Open-WebUI context and user input for automated testing
```

---

### WARNING #3: NFR9 Validation Added to Story 3.5 ✅

**Location:** [docs/prd.md](docs/prd.md) - Story 3.5 Acceptance Criteria

**Changes to Story 3.5 AC#6:**

```
6. **WARNING #3 FIX:** Performance improvement: metadata filtering on 20% of knowledge base demonstrates 40%+ latency reduction vs. unfiltered:
   - Performance test implemented in Story 3.5: `tests/integration/test_metadata_filtering_performance.py`
   - **NFR9 Validation Test:**
     a. Setup: Ingest 1000 documents with metadata (department field: 20% "engineering", 80% other departments)
     b. Baseline measurement: Execute 100 queries without metadata filtering, record average latency
     c. Filtered measurement: Execute same 100 queries WITH metadata filter `{"department": "engineering"}`, record average latency
     d. Calculate improvement: `improvement = (baseline_latency - filtered_latency) / baseline_latency * 100%`
     e. **Pass criteria:** improvement >= 50% (target from NFR9)
     f. **Fail criteria:** improvement < 50% → investigate (missing indexes, inefficient Cypher queries, etc.)
   - Test outputs performance report to `benchmarks/metadata-filtering-performance.json`
   - Results documented in `docs/performance-benchmarks.md`
   - If test fails, root cause analysis performed before marking Story 3.5 as done
```

---

## VERIFICATION CHECKLIST

Before proceeding to development, verify:

- [x] `.env.example` file exists and is comprehensive
- [x] Story 1.1 AC#7 and AC#8 added (env template + dependency management)
- [x] Story 1.2 AC#6 updated with Neo4j memory configuration
- [x] Story 1.6 expanded with LLM configuration section
- [x] Story 1.7 created with full CI/CD workflow implementation
- [x] Story 2.1 AC#7 updated with docker-compose.test.yml clarification
- [x] Story 3.1 AC#8 updated with cross-epic integration test
- [x] Story 3.5 AC#6 updated with NFR9 performance validation
- [x] Story 3.10 AC#6 updated with cross-epic integration test
- [x] Story 5.1 AC#8 updated with cross-epic integration test
- [x] Story 5.4 AC#3 updated with backup/restore scripts implementation
- [x] Story 5.4 AC#6 updated with comprehensive operational runbook
- [x] Story 5.5 AC#2 updated with detailed BEIR SciFact benchmark methodology
- [x] Story 5.6 AC#7, AC#8, AC#9, AC#10 added for LLM + embedding model onboarding

---

## NEXT STEPS

### Immediate Actions:
1. **Developer Review:** Have dev team review all fixes to confirm understanding
2. **Technical Spike:** Run Story 0.1 (4 hours) to prototype LightRAG Server + RAG-Anything deployment before Epic 1
3. **Dependency Installation:** Verify all new Python packages documented (beir, chromadb, pytest-docker-compose, etc.)

### Epic 1 Kickoff:
- Start with Story 1.1 (repository structure + .env.example validation)
- Validate `.env.example` file is complete during Story 1.1
- Run Story 1.7 early (CI/CD setup) to enable automated testing throughout development

### Ongoing Validation:
- PO (Sarah) to review completed stories against updated acceptance criteria
- Run PO Master Checklist again after Epic 3 completion (largest epic)
- Final checklist before MVP launch (Story 5.5 validation)

---

**Status:** ✅ ALL BLOCKERS RESOLVED - READY FOR DEVELOPMENT

**Confidence Level:** 95% (up from 82%)

**Estimated Additional Effort from Blocker Fixes:** +8-10 days spread across epics (already factored into 4-6 month timeline)

**PO Sign-Off:** Sarah (Product Owner) - 2025-10-15
