# Testing Guide

This guide covers all testing approaches for the RAG Engine project, including unit tests, integration tests, end-to-end tests, and service validation.

---

## Table of Contents

1. [Testing Philosophy](#testing-philosophy)
2. [Test Categories](#test-categories)
3. [Running Tests](#running-tests)
4. [End-to-End Integration Tests](#end-to-end-integration-tests)
5. [Service Health Validation](#service-health-validation)
6. [Test Data Management](#test-data-management)
7. [Performance Testing](#performance-testing)
8. [Troubleshooting](#troubleshooting)

---

## Testing Philosophy

### Persistent Data by Default

The RAG Engine testing framework uses a **persistent data** approach by default:

- **Tests leave data in Neo4j** after execution
- **Allows manual inspection** of results for debugging
- **Prevents accidental data loss** during development
- **Useful for exploring graph structure** and relationships

### Clean Mode (Optional)

Use the `--clean` flag when automatic cleanup is desired:

- **CI/CD pipelines** - Prevents data accumulation
- **Automated regression testing** - Ensures clean slate
- **Resource-constrained environments** - Manages disk usage

### Manual Cleanup

For granular control, use the dedicated cleanup script:

```bash
./scripts/clear-test-data.sh [--all|--db-only|--files-only] [--force]
```

---

## Test Categories

### 1. Unit Tests

**Location:** `services/api/tests/unit/`

**Purpose:** Test individual functions and classes in isolation

**Coverage Target:** 80%+

**Example:**
```bash
pytest services/api/tests/unit/ -v
```

### 2. Integration Tests

**Location:** `services/api/tests/integration/`

**Purpose:** Test API endpoints and service interactions

**Includes:**
- API route testing
- Document ingestion validation
- Metadata validation
- Entity configuration
- Batch processing

**Example:**
```bash
pytest services/api/tests/integration/ -v
```

### 3. End-to-End (E2E) Tests

**Location:** `services/api/tests/integration/test_e2e_cv_ingestion.py`

**Purpose:** Validate complete pipeline with real data

**Tests:**
- Document upload → Neo4j storage
- RAG-Anything PDF parsing
- Metadata retrieval
- Document listing and filtering
- Document deletion

---

## Running Tests

### Prerequisites

1. **Services running:**
   ```bash
   docker-compose up -d neo4j api
   ```

2. **Sample data downloaded:**
   ```bash
   python scripts/download-sample-data.py
   ```

3. **Dependencies installed:**
   ```bash
   pip install -r services/api/requirements.txt
   pip install pytest pytest-asyncio pytest-cov httpx
   ```

### Basic Test Execution

#### Run All Tests
```bash
pytest services/api/tests/ -v
```

#### Run Unit Tests Only
```bash
pytest services/api/tests/unit/ -v
```

#### Run Integration Tests Only
```bash
pytest services/api/tests/integration/ -v
```

#### Run E2E Tests Only
```bash
pytest services/api/tests/integration/test_e2e_cv_ingestion.py -v
```

### Test Output Verbosity

```bash
# Minimal output
pytest services/api/tests/

# Verbose output
pytest services/api/tests/ -v

# Very verbose (show print statements)
pytest services/api/tests/ -vv -s
```

### Code Coverage

```bash
# Run tests with coverage report
pytest services/api/tests/ --cov=app --cov-report=html

# View coverage report
open htmlcov/index.html
```

---

## End-to-End Integration Tests

### Overview

E2E tests validate the complete document ingestion pipeline using real CV PDF files from HuggingFace.

**Test File:** `services/api/tests/integration/test_e2e_cv_ingestion.py`

### Test Scenarios

1. **Single CV Ingestion** (`test_cv_ingestion_end_to_end`)
   - Upload CV via API
   - Verify Neo4j storage
   - Retrieve document metadata
   - List documents
   - Test deletion capability

2. **Batch Performance** (`test_cv_batch_ingestion_performance`)
   - Ingest multiple CVs
   - Measure throughput
   - Validate performance targets

3. **Entity Configuration** (`test_cv_entity_types_configuration`)
   - Verify CV-specific entity types
   - Validate entity type metadata

### Running E2E Tests

#### Persistent Mode (Default)

Test data remains in database for inspection:

```bash
pytest services/api/tests/integration/test_e2e_cv_ingestion.py -v
```

**Output includes:**
- Test results and assertions
- Performance metrics
- Instructions for viewing data
- Cleanup commands

**After tests:**
```bash
# View uploaded documents
curl -H "X-API-Key: test-key-12345" http://localhost:9000/api/v1/documents

# View specific document
curl -H "X-API-Key: test-key-12345" http://localhost:9000/api/v1/documents/{doc_id}

# Clean up when done
./scripts/clear-test-data.sh
```

#### Clean Mode

Automatically delete test data after execution:

```bash
pytest services/api/tests/integration/test_e2e_cv_ingestion.py --clean -v
```

**Use cases:**
- CI/CD pipelines
- Automated regression testing
- Quick validation without manual cleanup

### Performance Metrics

E2E tests measure and log:

| Metric | Target | Measured By |
|--------|--------|-------------|
| Document ingestion time | <10s per doc | Time from upload to API response |
| Ingestion throughput | >10 docs/min | Batch processing rate |
| Metadata query time | <100ms | GET /documents/{id} response time |
| Neo4j query time | <100ms | Cypher query execution |

**Example output:**
```
============================================================
PERFORMANCE METRICS
============================================================
Document ingestion time:  2.34s
Ingestion throughput:     25.6 documents/minute
Metadata query time:      45.23ms
============================================================
```

---

## Service Health Validation

### Overview

The health validation script tests all services and the complete ingestion pipeline without pytest.

**Script:** `scripts/test-ingestion-pipeline.sh`

### What It Tests

1. **Neo4j HTTP connectivity** (port 7474)
2. **Neo4j Bolt connectivity** (port 7687)
3. **API service health** endpoint
4. **Document ingestion** (upload real CV)
5. **Neo4j data verification**
6. **End-to-end round-trip** (ingest → retrieve)

### Running Health Validation

#### Persistent Mode (Default)
```bash
./scripts/test-ingestion-pipeline.sh
```

**Output:**
```
============================================================
RAG Engine Ingestion Pipeline Health Validation
============================================================

Configuration:
  API URL:          http://localhost:9000
  Neo4j HTTP Port:  7474
  Neo4j Bolt Port:  7687
  Clean Mode:       false

============================================================

➜ Test 1: Validating Neo4j HTTP connectivity...
✓ Neo4j HTTP endpoint responding

➜ Test 2: Validating Neo4j Bolt connectivity...
✓ Neo4j Bolt port 7687 is open

➜ Test 3: Validating API service health...
✓ API service health endpoint responding

...

✓ ALL VALIDATIONS PASSED
```

#### Clean Mode
```bash
./scripts/test-ingestion-pipeline.sh --clean
```

Automatically deletes test document after validation.

### Configuration

Override defaults with environment variables:

```bash
# Custom API URL
API_URL=http://localhost:9100 ./scripts/test-ingestion-pipeline.sh

# Custom Neo4j ports
NEO4J_HTTP_PORT=8474 NEO4J_BOLT_PORT=8687 ./scripts/test-ingestion-pipeline.sh

# Custom API key
API_KEY=my-secret-key ./scripts/test-ingestion-pipeline.sh --clean
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All validations passed |
| 1 | Validation failure |
| 2 | Configuration error |

**Example usage in CI/CD:**
```bash
#!/bin/bash
if ./scripts/test-ingestion-pipeline.sh --clean; then
  echo "Pipeline healthy ✓"
  exit 0
else
  echo "Pipeline validation failed ✗"
  exit 1
fi
```

---

## Test Data Management

### Downloading Sample Data

Download CV PDF files from HuggingFace:

```bash
# Download default (6 CVs)
python scripts/download-sample-data.py

# Download custom number
python scripts/download-sample-data.py --max-cvs 3

# Download to custom directory
python scripts/download-sample-data.py --output-dir ./my-cv-data
```

**See:** [sample-data.md](sample-data.md) for detailed documentation.

### Cleaning Test Data

The cleanup script provides granular control:

#### Quick Cleanup Commands

```bash
# Clear database only (default)
./scripts/clear-test-data.sh

# Clear both database and files
./scripts/clear-test-data.sh --all

# Clear files only
./scripts/clear-test-data.sh --files-only

# Force cleanup without confirmation
./scripts/clear-test-data.sh --all --force
```

#### What Gets Deleted

| Flag | Database Documents | PDF Files |
|------|-------------------|-----------|
| `--db-only` (default) | ✓ | ✗ |
| `--files-only` | ✗ | ✓ |
| `--all` | ✓ | ✓ |

#### Script Features

- **Confirmation prompt** before deletion (unless `--force`)
- **Resource counting** before deletion
- **Detailed logging** of cleanup operations
- **Summary output** showing deleted resources
- **Proper exit codes** for automation

**Example output:**
```bash
$ ./scripts/clear-test-data.sh --all

➜ Counting documents in database...
  Found: 12 documents

➜ Counting PDF files in filesystem...
  Found: 6 PDF files in tests/fixtures/sample-data/cv-pdfs

============================================================
CLEANUP CONFIRMATION
============================================================

About to delete:
  • 12 documents from Neo4j (via API)
  • 6 PDF files from tests/fixtures/sample-data/cv-pdfs

⚠ This action cannot be undone!

Continue? [y/N] y

============================================================
✓ CLEANUP COMPLETE
============================================================

  Database: Deleted 12 documents from Neo4j
  Filesystem: Deleted 6 PDF files
```

---

## Performance Testing

### Baseline Metrics

From Epic 2 implementation:

| Metric | Target | Typical |
|--------|--------|---------|
| Document parsing success rate | >95% | ~98% |
| Batch ingestion throughput | >10 docs/min | 15-25 docs/min |
| API ingestion acceptance | <500ms | 200-400ms |
| Single document retrieval | <100ms | 50-80ms |

### Running Performance Tests

```bash
# Run batch performance test
pytest services/api/tests/integration/test_e2e_cv_ingestion.py::test_cv_batch_ingestion_performance -v

# Run with performance profiling
pytest services/api/tests/integration/ --durations=10
```

### Interpreting Results

E2E tests log performance metrics:

```python
logger.info(
    "Performance metric",
    operation="document_ingestion",
    duration_seconds=elapsed,
    documents_per_minute=60 / elapsed
)
```

**Example output:**
```
Test 1: Uploading CV document via API...
✓ Document uploaded successfully
  Document ID: 550e8400-e29b-41d4-a716-446655440000
  Filename: cv_000.pdf
  Status: queued
  Ingestion time: 2.34s
  Throughput: 25.6 documents/minute
```

### Performance Regression Detection

Compare metrics across test runs:

```bash
# Run tests and save output
pytest services/api/tests/integration/test_e2e_cv_ingestion.py -v > test_results.log

# Extract performance metrics
grep "Throughput:" test_results.log
```

---

## Troubleshooting

### Common Issues

#### 1. No CV Files Found

**Error:**
```
SKIPPED [1] services/api/tests/integration/test_e2e_cv_ingestion.py:51:
No CV PDF files found in tests/fixtures/sample-data/cv-pdfs
Run: python scripts/download-sample-data.py
```

**Solution:**
```bash
python scripts/download-sample-data.py
```

---

#### 2. Neo4j Connection Failed

**Error:**
```
neo4j.exceptions.ServiceUnavailable: Unable to retrieve routing information
```

**Solutions:**
1. **Check Neo4j is running:**
   ```bash
   docker-compose ps neo4j
   ```

2. **Verify Neo4j ports:**
   ```bash
   nc -z localhost 7687
   nc -z localhost 7474
   ```

3. **Check Neo4j logs:**
   ```bash
   docker-compose logs neo4j
   ```

4. **Restart Neo4j:**
   ```bash
   docker-compose restart neo4j
   ```

---

#### 3. API Service Unavailable

**Error:**
```
httpx.ConnectError: [Errno 111] Connection refused
```

**Solutions:**
1. **Check API is running:**
   ```bash
   docker-compose ps api
   ```

2. **Verify API health:**
   ```bash
   curl http://localhost:9000/health
   ```

3. **Check API logs:**
   ```bash
   docker-compose logs api
   ```

4. **Restart API:**
   ```bash
   docker-compose restart api
   ```

---

#### 4. Test Data Cleanup Failed

**Error:**
```
Failed to delete document xxx (HTTP 404)
```

**Solution:**
Document may have already been deleted. This is usually safe to ignore, but you can verify:

```bash
# List all documents
curl -H "X-API-Key: test-key-12345" http://localhost:9000/api/v1/documents

# Force cleanup
./scripts/clear-test-data.sh --all --force
```

---

#### 5. Slow Test Execution

**Issue:** Tests taking longer than expected

**Solutions:**

1. **Check Docker resources:**
   ```bash
   docker stats
   ```

2. **Verify Neo4j memory settings:**
   ```bash
   docker-compose logs neo4j | grep -i memory
   ```

3. **Run fewer tests:**
   ```bash
   # Run single test
   pytest services/api/tests/integration/test_e2e_cv_ingestion.py::test_cv_ingestion_end_to_end -v

   # Skip performance tests
   pytest services/api/tests/integration/ -k "not performance" -v
   ```

4. **Use clean mode to reduce data:**
   ```bash
   pytest services/api/tests/integration/ --clean -v
   ```

---

#### 6. Import Errors

**Error:**
```
ModuleNotFoundError: No module named 'app'
```

**Solutions:**

1. **Install dependencies:**
   ```bash
   pip install -r services/api/requirements.txt
   ```

2. **Set PYTHONPATH:**
   ```bash
   export PYTHONPATH=/home/wsluser/dev/rag-engine/services/api:$PYTHONPATH
   pytest services/api/tests/ -v
   ```

3. **Run from correct directory:**
   ```bash
   cd /home/wsluser/dev/rag-engine
   pytest services/api/tests/ -v
   ```

---

## Best Practices

### For Development

1. **Run tests frequently** during development
2. **Use persistent mode** for debugging
3. **Clean up manually** when you're done inspecting
4. **Check performance metrics** for regression

```bash
# Typical development workflow
pytest services/api/tests/integration/test_e2e_cv_ingestion.py -v -s

# Inspect results in Neo4j Browser
open http://localhost:7474

# Clean up when satisfied
./scripts/clear-test-data.sh --all
```

### For CI/CD

1. **Use clean mode** to prevent data accumulation
2. **Run health validation** as smoke test
3. **Measure and track** performance metrics
4. **Fail fast** on validation errors

```bash
# CI/CD pipeline example
./scripts/test-ingestion-pipeline.sh --clean || exit 1
pytest services/api/tests/ --clean -v --cov=app --cov-report=xml
```

### For Performance Testing

1. **Use multiple CV files** for batch tests
2. **Measure consistently** across runs
3. **Compare against baselines** for regression
4. **Monitor resource usage** (CPU, memory, disk)

```bash
# Performance testing workflow
python scripts/download-sample-data.py --max-cvs 10
pytest services/api/tests/integration/test_e2e_cv_ingestion.py::test_cv_batch_ingestion_performance -v -s
```

---

## References

- **Sample Data Documentation:** [sample-data.md](sample-data.md)
- **Architecture Testing Strategy:** [architecture/testing-strategy.md](architecture/testing-strategy.md)
- **API Specification:** [architecture/api-specification.md](architecture/api-specification.md)
- **Entity Configuration:** [config/entity-types.yaml](../config/entity-types.yaml)

---

**Last Updated:** 2025-10-17
