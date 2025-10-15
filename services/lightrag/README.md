# LightRAG Integration Service

Service wrapper for LightRAG graph-based retrieval engine.

## Purpose

Manages:
- LightRAG instance lifecycle
- Graph-based entity extraction
- Hybrid retrieval (vector + graph + keyword)
- Neo4j backend integration

## Configuration

See `.env.example` for configuration variables:
- `EMBEDDING_MODEL`: Local embeddings model
- `DEFAULT_RETRIEVAL_MODE`: naive, local, global, hybrid, or mix
- `DEFAULT_TOP_K`: Number of results to return

## Development

```bash
# Run locally (from repository root)
cd services/lightrag
pip install -r requirements.txt
python -m app.main

# Run in Docker
docker-compose up lightrag
```
