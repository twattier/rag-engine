# RAG Engine API Service

FastAPI REST API service for RAG Engine.

## Purpose

Provides HTTP endpoints for:
- Document ingestion
- Query processing
- Graph exploration
- System health monitoring

## Development

```bash
# Run locally (from repository root)
cd services/api
pip install -r requirements.txt
uvicorn app.main:app --reload

# Run in Docker
docker-compose up api
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
