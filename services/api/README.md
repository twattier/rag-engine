# RAG Engine API Service

FastAPI-based REST API service for RAG Engine, providing unified interface for document ingestion, retrieval, and knowledge graph operations.

## Overview

The API service acts as the **orchestration layer** for RAG Engine, routing requests to:
- **LightRAG service**: Graph-based retrieval and entity extraction
- **RAG-Anything service**: Multi-format document parsing
- **Neo4j database**: Direct graph queries and statistics

## Running Locally

### Via Docker Compose (Recommended)
```bash
# From repository root
docker-compose up -d api

# View logs
docker-compose logs -f api

# Access API
open http://localhost:8000/docs
```

### Standalone Development
```bash
# Install dependencies
cd services/api
pip install -r requirements.txt

# Set environment variables
export NEO4J_URI=bolt://localhost:7687
export NEO4J_AUTH=neo4j/password
export API_KEY=test-key

# Run with hot-reload
uvicorn app.main:app --reload --port 8000
```

## API Endpoints

### Story 1.3 (Current)
- `GET /` - Root endpoint with API information
- `GET /health` - Basic health check
- `GET /docs` - Swagger UI documentation
- `GET /redoc` - ReDoc documentation
- `GET /openapi.json` - OpenAPI schema

### Future Stories
- `POST /api/v1/documents/ingest` - Ingest document (Epic 2)
- `POST /api/v1/query` - Query knowledge base (Epic 3)
- `GET /api/v1/graph/stats` - Graph statistics (Epic 3)
- And more...

## Configuration

Configuration via environment variables (see `.env.example`):

| Variable | Description | Default |
|----------|-------------|---------|
| `API_PORT` | API service port | 8000 |
| `API_KEY` | API authentication key | change-me-in-production |
| `NEO4J_URI` | Neo4j connection URI | bolt://neo4j:7687 |
| `NEO4J_AUTH` | Neo4j credentials | neo4j/password |
| `LOG_LEVEL` | Logging level | INFO |
| `CORS_ORIGINS` | Allowed CORS origins | http://localhost:3000,http://localhost:8080 |

## Testing

```bash
# Run health check test
./scripts/test-api-health.sh

# Run unit tests (when available)
pytest tests/unit/api/

# Run integration tests (when available)
pytest tests/integration/api/
```

## Architecture

```
app/
├── main.py              # FastAPI application initialization
├── config.py            # Configuration management (Pydantic Settings)
├── dependencies.py      # Shared dependencies (auth, DB connections)
├── routers/             # API route handlers
│   ├── health.py        # Health check endpoints
│   └── ...              # Future routers (documents, query, etc.)
├── models/              # Pydantic request/response models (future)
└── services/            # Business logic layer (future)
```

## Development Notes

- **Hot-reload enabled**: Code changes automatically reload the server
- **Shared code**: `shared/` directory mounted for access to common models/utils
- **Dependencies**: Service depends on Neo4j being healthy before starting
- **Authentication**: Story 1.3 includes basic health check (no auth). Story 4.2 adds API key authentication.

## Next Steps

- Story 1.4: Add Neo4j connectivity check to `/health` endpoint
- Story 1.5: Implement structured logging with structlog
- Epic 2: Add document ingestion endpoints
- Epic 3: Add query and retrieval endpoints
