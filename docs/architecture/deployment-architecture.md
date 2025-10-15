# Deployment Architecture

## Deployment Strategy

**Frontend Deployment:** N/A (Backend-only system for MVP)

**Backend Deployment:**
- **Platform:** Docker Compose on self-hosted infrastructure (Linux/macOS/Windows+WSL2)
- **Build Command:** `docker compose build` (builds all service images)
- **Deployment Method:**
  - **Development**: `docker compose up -d` (auto-reload enabled)
  - **Production**: `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d` (optimized images, no dev tools)
- **Scaling**: Single-node deployment for MVP, Kubernetes multi-replica for Phase 2
- **Persistence**: Docker volumes for Neo4j data, document storage, LightRAG cache
- **Backup Strategy**: Automated Neo4j dumps via `scripts/backup_neo4j.sh` (daily recommended)
- **Reverse Proxy**: Optional Nginx for HTTPS termination and domain mapping

**Key Deployment Configurations:**

```yaml
# docker-compose.prod.yml (production overrides)
services:
  api:
    environment:
      - DEBUG=false
      - API_RELOAD=false
      - LOG_LEVEL=WARNING
    deploy:
      resources:
        limits:
          cpus: '4.0'
          memory: 8G
        reservations:
          cpus: '2.0'
          memory: 4G
    restart: unless-stopped

  neo4j:
    environment:
      - NEO4J_HEAP_SIZE=8G          # Increase for production
      - NEO4J_PAGECACHE_SIZE=4G
    deploy:
      resources:
        limits:
          memory: 16G
    volumes:
      - neo4j_data:/data
      - neo4j_logs:/logs
      - ./backups:/backups
    restart: unless-stopped
```

---

## CI/CD Pipeline

```yaml
# .github/workflows/ci.yaml
name: CI - Test and Build

on:
  pull_request:
    branches: [main, develop]
  push:
    branches: [main, develop]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install ruff black mypy

      - name: Lint with ruff
        run: ruff check services/ shared/

      - name: Format check with black
        run: black --check services/ shared/

      - name: Type check with mypy
        run: mypy services/ shared/

  test:
    runs-on: ubuntu-latest
    services:
      neo4j:
        image: neo4j:5.15
        env:
          NEO4J_AUTH: neo4j/test-password
          NEO4J_PLUGINS: '["apoc"]'
        ports:
          - 7687:7687
          - 7474:7474
        options: >-
          --health-cmd "cypher-shell -u neo4j -p test-password 'RETURN 1'"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r services/api/requirements.txt
          pip install -r services/lightrag/requirements.txt
          pip install pytest pytest-cov pytest-asyncio httpx

      - name: Run tests with coverage
        env:
          NEO4J_URI: bolt://localhost:7687
          NEO4J_USERNAME: neo4j
          NEO4J_PASSWORD: test-password
        run: |
          pytest tests/ --cov=services/ --cov-report=xml

      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v4
        with:
          file: ./coverage.xml

  build:
    runs-on: ubuntu-latest
    needs: [lint, test]
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Login to GitHub Container Registry
        uses: docker/login-action@v3
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Build and push API image
        uses: docker/build-push-action@v5
        with:
          context: ./services/api
          push: true
          tags: |
            ghcr.io/${{ github.repository }}/api:latest
            ghcr.io/${{ github.repository }}/api:${{ github.sha }}

      - name: Build and push LightRAG image
        uses: docker/build-push-action@v5
        with:
          context: ./services/lightrag
          push: true
          tags: |
            ghcr.io/${{ github.repository }}/lightrag:latest
            ghcr.io/${{ github.repository }}/lightrag:${{ github.sha }}
```

---

## Environments

| Environment | API URL | Neo4j URI | Purpose |
|------------|---------|-----------|---------|
| Development | `http://localhost:8000` | `bolt://localhost:7687` | Local development with hot-reload |
| Staging | `http://staging.your-domain.com` | `bolt://staging-neo4j:7687` | Pre-production testing (user-deployed) |
| Production | `https://your-domain.com` | `bolt://neo4j:7687` | Live user deployments (self-hosted) |

**Notes:**
- RAG Engine is **self-hosted**, so users deploy their own environments
- "Staging" and "Production" are examples of how users might structure multi-environment setups
- Documentation should guide users on setting up reverse proxy (Nginx/Traefik) for HTTPS
- No centralized hosting - each user manages their own infrastructure

---
