# Development Workflow

## Local Development Setup

### Prerequisites

```bash
# Install Docker and Docker Compose
# Linux (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install docker.io docker-compose-v2

# macOS (via Homebrew)
brew install docker docker-compose

# Windows: Install Docker Desktop from docker.com
# Ensure WSL2 backend is enabled

# Verify installations
docker --version  # Should be 24.0+
docker compose version  # Should be v2.x
```

### Initial Setup

```bash
# Clone repository
git clone https://github.com/your-org/rag-engine.git
cd rag-engine

# Copy environment template
cp .env.example .env

# Edit .env file with your configuration
# IMPORTANT: Set LLM API keys if using external models
nano .env

# Pull required Docker images (optional, compose will do this)
docker compose pull

# Start all services
docker compose up -d

# Wait for services to be ready (check health endpoint)
curl http://localhost:8000/health

# View logs
docker compose logs -f

# Expected output: All services show "healthy" status
```

### Development Commands

```bash
# Start all services in detached mode
docker compose up -d

# Start specific service(s) only
docker compose up -d api neo4j

# View real-time logs
docker compose logs -f api
docker compose logs -f lightrag

# Rebuild services after code changes
docker compose up -d --build api

# Stop all services (preserves data)
docker compose stop

# Stop and remove containers (preserves volumes)
docker compose down

# Remove everything including volumes (DESTRUCTIVE)
docker compose down -v

# Run tests inside containers
docker compose exec api pytest tests/

# Access Neo4j Browser for graph visualization
open http://localhost:7474
# Username: neo4j
# Password: (from .env NEO4J_PASSWORD)

# Access FastAPI interactive docs
open http://localhost:8000/docs

# Backup Neo4j data
./scripts/backup_neo4j.sh

# Restore Neo4j from backup
./scripts/restore_neo4j.sh ./backups/neo4j-2025-10-15.dump
```

---

## Environment Configuration

### Required Environment Variables

```bash
# Frontend (N/A for backend-only MVP)
# No frontend in MVP

# Backend (.env in repository root)
# FastAPI Configuration
API_HOST=0.0.0.0
API_PORT=8000                        # USER CONFIGURABLE
API_WORKERS=4
API_RELOAD=true                      # Development only
LOG_LEVEL=INFO

# Authentication (MVP: Simple API key, Phase 2: OAuth2)
ENABLE_AUTH=false                    # Set to true to enable API key auth
API_KEYS=your-secret-key-1,your-secret-key-2

# Neo4j Configuration
NEO4J_URI=bolt://neo4j:7687          # Internal Docker network
NEO4J_HTTP_PORT=7474                 # USER CONFIGURABLE (host binding)
NEO4J_BOLT_PORT=7687                 # USER CONFIGURABLE (host binding)
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-secure-password  # CHANGE THIS
NEO4J_DATABASE=neo4j

# Neo4j Memory Settings (adjust based on available RAM)
NEO4J_HEAP_SIZE=4G                   # Heap memory (4GB minimum)
NEO4J_PAGECACHE_SIZE=2G              # Page cache (2GB minimum)

# LightRAG Configuration
LIGHTRAG_WORKING_DIR=./lightrag_storage
LIGHTRAG_WORKSPACE=default           # Data isolation namespace
LIGHTRAG_CHUNK_SIZE=1200             # Tokens per chunk
LIGHTRAG_CHUNK_OVERLAP=100           # Overlap tokens
LIGHTRAG_TOP_K=60                    # Default top_k for queries
LIGHTRAG_CHUNK_TOP_K=20              # Chunks to retrieve

# RAG-Anything Configuration
RAGANYTHING_OUTPUT_DIR=./output      # Parsed document output
RAGANYTHING_PARSER=mineru            # mineru or docling
RAGANYTHING_PARSE_METHOD=auto        # auto, ocr, txt

# LLM Configuration (OpenAI-compatible endpoint)
LLM_ENDPOINT=http://host.docker.internal:11434/v1  # Ollama example
# LLM_ENDPOINT=https://api.openai.com/v1            # OpenAI
# LLM_ENDPOINT=http://external-litellm:4000/v1      # External LiteLLM proxy

# LLM API Keys (if required by endpoint)
OPENAI_API_KEY=sk-...                # Required for OpenAI endpoint
ANTHROPIC_API_KEY=sk-ant-...         # Required if using Anthropic via proxy
AZURE_API_KEY=...                    # Required for Azure OpenAI

# Embedding Model Configuration
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2  # Local (MVP)
# EMBEDDING_MODEL=openai/text-embedding-3-large        # Enterprise (optional)
EMBEDDING_DIMENSIONS=384             # Must match model (384 for MiniLM, 3072 for OpenAI)

# Reranking Configuration (optional)
ENABLE_RERANKING=true
RERANKER_MODEL=jina                  # jina or ms-marco
JINA_API_KEY=jina_...                # Required if using Jina reranker

# Shared Configuration
ENVIRONMENT=development              # development, staging, production
DEBUG=true                           # Development only
```

**IMPORTANT PORT NOTES**:
- All port numbers marked as "USER CONFIGURABLE" can be changed to avoid conflicts
- Internal Docker network always uses default ports (no conflicts)
- Only host bindings (in `ports:` section of docker-compose.yml) need to be unique
- Example: If port 8000 is in use, change `API_PORT=8000` to `API_PORT=8080` and update docker-compose.yml

---
