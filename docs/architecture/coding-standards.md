# Coding Standards

## Critical Fullstack Rules

- **Type Safety:** All API models defined with Pydantic V2; use strict type hints (`from __future__ import annotations`) in all modules
- **Error Handling:** All API routes must catch exceptions and return standardized `ApiError` response; never expose internal stack traces to clients
- **Environment Variables:** Access config only through `get_settings()` Pydantic Settings object; never use `os.getenv()` directly (except in `config.py`)
- **Async/Await Consistency:** All I/O operations (DB, HTTP, file) must use async; never block event loop with sync calls
- **Logging:** Use structlog with structured fields (JSON); never use `print()` statements; include `request_id` in all log entries
- **Neo4j Queries:** Always use parameterized Cypher queries via Neo4j driver; never string interpolation (prevents injection)
- **Docker Volumes:** Never store data in containers; use named volumes or bind mounts for persistence
- **API Versioning:** All routes prefixed with `/api/v1/` for future compatibility
- **Dependency Injection:** Use FastAPI `Depends()` for all shared resources (DB connections, services); never create global singletons
- **Testing:** Every API endpoint requires integration test; every service function requires unit test (target 80%+ coverage)

---

## Naming Conventions

| Element | Convention | Example |
|---------|-----------|---------|
| Modules | snake_case | `document_service.py` |
| Classes | PascalCase | `DocumentService` |
| Functions | snake_case | `async def ingest_document()` |
| Variables | snake_case | `doc_id`, `file_path` |
| Constants | SCREAMING_SNAKE_CASE | `MAX_FILE_SIZE`, `DEFAULT_TOP_K` |
| API Routes | kebab-case | `/documents/ingest`, `/graph/entities` |
| Database Tables (Neo4j Labels) | PascalCase | `:Document`, `:Entity`, `:TextChunk` |
| Environment Variables | SCREAMING_SNAKE_CASE | `NEO4J_URI`, `API_PORT` |
| Docker Services | kebab-case | `rag-engine-api`, `neo4j` |
| JSON Fields | camelCase | `{"docId": "...", "createdAt": "..."}` |

**Additional Conventions:**
- **Async Functions**: Prefix with `async def a<function_name>` for clarity (e.g., `async def aquery()` in LightRAG)
- **Private Methods**: Single leading underscore `_internal_method()`
- **Pydantic Models**: Suffix with type (e.g., `DocumentRequest`, `QueryResponse`, `ApiError`)
- **Test Functions**: Prefix with `test_` and use descriptive names (e.g., `test_ingest_document_success`)

---
