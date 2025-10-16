# RAG Engine Deployment Guide

This comprehensive guide walks you through deploying RAG Engine from scratch.

## Prerequisites

Before deploying RAG Engine, ensure your system meets these requirements:

### Required Software

1. **Docker 24.0+**
   - [Install Docker](https://docs.docker.com/get-docker/)
   - Verify: `docker --version`

2. **Docker Compose V2**
   - Included with Docker Desktop
   - Linux: Install via Docker package
   - Verify: `docker compose version`

### System Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| RAM | 8GB | 16GB |
| CPU Cores | 4 | 8 |
| Disk Space | 50GB free | 100GB+ free |
| OS | Linux, macOS 12+, Windows 10+ (WSL2) | Ubuntu 22.04, macOS 14+ |

### Required Ports

RAG Engine uses the following ports by default (configurable in `.env`):

- **7474**: Neo4j HTTP (Browser UI)
- **7687**: Neo4j Bolt (Database protocol)
- **8000**: RAG Engine API

**Port conflicts?** See [Changing Ports](#changing-ports) section.

## Quick Start (5 Minutes)

### 1. Clone Repository

```bash
git clone https://github.com/your-org/rag-engine.git
cd rag-engine
```

### 2. Configure Environment

```bash
# Copy example configuration
cp .env.example .env

# Edit configuration (optional for testing, required for production)
nano .env
```

**Minimum required changes for production:**
- Change `NEO4J_AUTH` password
- Change `API_KEY`
- Set `OPENAI_API_KEY` or configure local LLM

### 3. Start Services

```bash
docker compose up -d
```

### 4. Validate Deployment

```bash
# Automated validation
./scripts/validate-deployment.sh

# Or manual verification
curl http://localhost:8000/health
```

### 5. Access Services

- **API Documentation**: http://localhost:8000/docs
- **Neo4j Browser**: http://localhost:7474 (login: neo4j / password from .env)
- **Health Check**: http://localhost:8000/health

## Detailed Deployment Steps

### Step 1: Prerequisites Verification

#### Check Docker Installation

```bash
docker --version
# Expected: Docker version 24.0.0 or higher

docker compose version
# Expected: Docker Compose version v2.x.x

docker info
# Should show Docker daemon running
```

#### Check Available Resources

```bash
# Linux: Check RAM
free -h

# macOS: Check Docker Desktop resources
# Docker Desktop → Settings → Resources

# Windows (WSL2): Check allocated memory
wsl --set-default-version 2
```

**Docker Desktop Users**: Allocate at least 8GB RAM (16GB recommended):
- Docker Desktop → Settings → Resources → Memory

#### Verify Port Availability

```bash
# Linux/macOS
lsof -i :7474
lsof -i :7687
lsof -i :8000

# If ports are in use, see "Changing Ports" section
```

### Step 2: Repository Setup

#### Clone Repository

```bash
# HTTPS
git clone https://github.com/your-org/rag-engine.git
cd rag-engine

# SSH
git clone git@github.com:your-org/rag-engine.git
cd rag-engine
```

#### Verify Repository Structure

```bash
ls -la
# Expected:
#   .env.example
#   docker-compose.yml
#   services/
#   docs/
#   scripts/
```

### Step 3: Configuration

#### Create `.env` File

```bash
cp .env.example .env
```

#### Essential Configuration Variables

Edit `.env` and configure:

```bash
# Neo4j Configuration (REQUIRED)
NEO4J_AUTH=neo4j/YOUR_STRONG_PASSWORD_HERE

# API Authentication (REQUIRED for production)
API_KEY=your-secret-api-key-change-me

# LLM Provider (REQUIRED - choose one)
# Option 1: OpenAI
OPENAI_API_KEY=sk-your-openai-api-key
LLM_PROVIDER=openai

# Option 2: Local LLM (Ollama)
LLM_PROVIDER=local
LOCAL_LLM_ENDPOINT=http://host.docker.internal:11434
LOCAL_LLM_MODEL=llama3.1

# Option 3: LiteLLM proxy (enterprise)
LLM_PROVIDER=litellm
LITELLM_MASTER_KEY=sk-your-litellm-key
```

**All configuration options** are documented in `.env.example`.

### Step 4: Launch Services

#### Start All Services

```bash
docker compose up -d
```

**Expected output:**
```
[+] Running 5/5
 ✔ Network rag-engine_rag-engine-network  Created
 ✔ Container rag-engine-neo4j             Started
 ✔ Container rag-engine-api               Started
 ✔ Container rag-engine-lightrag          Started
 ✔ Container rag-engine-rag-anything      Started
```

#### Monitor Startup

```bash
# Follow all logs
docker compose logs -f

# Follow specific service
docker compose logs -f api

# Press Ctrl+C to stop following
```

#### Check Service Status

```bash
docker compose ps
```

**Expected output:**
```
NAME                    STATUS              PORTS
rag-engine-api          Up (healthy)        0.0.0.0:8000->8000/tcp
rag-engine-neo4j        Up (healthy)        0.0.0.0:7474->7474/tcp, 0.0.0.0:7687->7687/tcp
...
```

### Step 5: Verification

#### Automated Validation

```bash
./scripts/validate-deployment.sh
```

Successful output shows:
```
✓ Docker installed
✓ Docker Compose V2 installed
✓ Docker daemon is running
✓ All required ports are available
✓ Services started successfully
✓ API Service is healthy
✓ Neo4j Browser is healthy
✓ API health check passed
✅ RAG Engine deployed successfully!
```

#### Manual Verification

**1. API Health Check**

```bash
curl http://localhost:8000/health | jq
```

Expected response (HTTP 200):
```json
{
  "status": "healthy",
  "service": "rag-engine-api",
  "version": "0.1.0",
  "dependencies": {
    "neo4j": {
      "status": "healthy",
      "response_time_ms": 45.2
    }
  },
  "timestamp": "2025-10-15T10:30:00.000Z"
}
```

**2. API Documentation**

Open in browser: http://localhost:8000/docs

Should see Swagger UI with API endpoints.

**3. Neo4j Browser**

Open in browser: http://localhost:7474

Login:
- **Connect URL**: `bolt://localhost:7687`
- **Username**: `neo4j`
- **Password**: (value from `NEO4J_AUTH` in `.env`)

Run test query:
```cypher
RETURN "RAG Engine Connected!" AS message
```

### Step 6: Test Basic Operations

#### Create Test Document (Coming in Epic 2)

```bash
# Document ingestion will be available in Epic 2
# For now, verify services are running
```

## Changing Ports

If default ports conflict with existing services:

1. Edit `.env` file:
   ```bash
   # Change Neo4j ports
   NEO4J_HTTP_PORT=7475
   NEO4J_BOLT_PORT=7688

   # Change API port
   API_PORT=8001
   ```

2. Restart services:
   ```bash
   docker compose down
   docker compose up -d
   ```

3. Update access URLs:
   - API: `http://localhost:8001`
   - Neo4j Browser: `http://localhost:7475`

## Stopping and Restarting

### Stop Services

```bash
# Stop all services (preserves data)
docker compose stop

# Stop and remove containers (preserves data volumes)
docker compose down
```

### Restart Services

```bash
# Restart all services
docker compose restart

# Restart specific service
docker compose restart api
```

### Complete Cleanup (DELETE ALL DATA!)

```bash
# WARNING: This deletes all data including Neo4j database
docker compose down -v

# Remove all images too
docker compose down -v --rmi all
```

## Upgrading RAG Engine

```bash
# Pull latest code
git pull origin main

# Rebuild services
docker compose build

# Restart with new images
docker compose up -d
```

## Platform-Specific Notes

### Linux (Ubuntu/Debian)

```bash
# Add user to docker group (avoid sudo)
sudo usermod -aG docker $USER
newgrp docker

# Start Docker daemon (if not running)
sudo systemctl start docker
sudo systemctl enable docker
```

### macOS

- Use Docker Desktop for Mac
- Allocate at least 8GB RAM in Docker Desktop settings
- File performance may be slower than Linux (use mounted volumes sparingly)

### Windows (WSL2)

1. **Enable WSL2**:
   ```powershell
   wsl --install
   wsl --set-default-version 2
   ```

2. **Install Ubuntu** from Microsoft Store

3. **Install Docker Desktop** with WSL2 backend

4. **Run all commands** in WSL2 Ubuntu terminal

**File paths**:
- Windows: `C:\Users\username\rag-engine`
- WSL2: `/mnt/c/Users/username/rag-engine`
- Native: `/home/username/rag-engine` (recommended)

## Next Steps

After successful deployment:

1. **Configure metadata schema**: See Epic 2 Story 2.2
2. **Ingest documents**: See Epic 2 documentation
3. **Query knowledge base**: See Epic 3 documentation
4. **Integrate with Open-WebUI**: See Epic 5 documentation

## Troubleshooting

If validation fails, see:
- [Troubleshooting Guide](troubleshooting.md)
- [Neo4j Setup Guide](neo4j-setup.md)
- [Health Monitoring Guide](health-monitoring.md)
- [Logging Guide](logging.md)

## Support

- **Issues**: [GitHub Issues](https://github.com/your-org/rag-engine/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/rag-engine/discussions)
- **Documentation**: [docs/](README.md)
