# Epic 1: Foundation & Core Infrastructure

**Epic Goal:** Establish Docker-based project foundation with Neo4j integration, basic service orchestration, and health check endpoints. By the end of this epic, developers can run `docker-compose up`, verify all services are running correctly, and confirm Neo4j graph database connectivity. This epic delivers the minimal deployable infrastructure that subsequent epics will build upon.

## Story 1.1: Initialize Repository Structure and Docker Compose Configuration

**As a** developer,
**I want** a well-organized monorepo with Docker Compose orchestration,
**so that** I can clone the repository and understand the project structure immediately.

### Acceptance Criteria

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

## Story 1.2: Deploy Neo4j with Vector Support and Verify Connectivity

**As a** developer,
**I want** Neo4j running in Docker with vector plugin enabled and persistent storage,
**so that** I can store and query graph data with vector embeddings.

### Acceptance Criteria

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

## Story 1.3: Create API Service with FastAPI and Health Check Endpoint

**As a** developer,
**I want** a FastAPI-based API service with a health check endpoint,
**so that** I can verify the API service is running and responsive.

### Acceptance Criteria

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

## Story 1.4: Implement Service Health Monitoring and Neo4j Connection Verification

**As a** platform operator,
**I want** the API service to verify Neo4j connectivity and report all service health statuses,
**so that** I can quickly diagnose infrastructure issues.

### Acceptance Criteria

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

## Story 1.5: Configure Structured Logging and Docker Compose Logging

**As a** developer,
**I want** structured JSON logging from all services visible via Docker Compose,
**so that** I can debug issues during development and troubleshoot production deployments.

### Acceptance Criteria

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

## Story 1.6: Create End-to-End Deployment Test and Documentation

**As a** new user,
**I want** comprehensive deployment documentation with validation steps,
**so that** I can successfully deploy RAG Engine on my first attempt.

### Acceptance Criteria

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
