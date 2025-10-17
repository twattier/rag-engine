# Environment Variable Loading Guide

This document explains how environment variables from `.env` are loaded in the RAG Engine project.

---

## Overview

The RAG Engine project uses a **hybrid approach** for environment variable management:

1. **Python/FastAPI**: Pydantic Settings automatically loads `.env`
2. **Shell Scripts**: Auto-load `.env` at script startup
3. **Manual Override**: Environment variables can still override `.env` values

---

## Python Scripts & FastAPI

### Automatic Loading via Pydantic Settings

All Python services automatically load `.env` through Pydantic Settings configuration:

**Location:** `services/api/app/config.py`

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",              # ← Automatically loads .env
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",               # ← Allows extra vars in .env
    )
```

**Usage:**
```bash
# .env is automatically loaded
cd services/api
python3 -m uvicorn app.main:app --reload

# Run tests (Pydantic loads .env automatically)
pytest services/api/tests/ -v
```

### Manual Loading in Python Scripts

For standalone Python scripts, use `python-dotenv`:

```python
from dotenv import load_dotenv
load_dotenv()  # Loads .env from project root

# Now use environment variables
import os
api_url = os.getenv("API_URL", "http://localhost:9000")
```

---

## Shell Scripts

### Automatic Loading (Updated Scripts)

The following scripts **automatically load `.env`** at startup:

1. **`scripts/test-ingestion-pipeline.sh`** - Health validation script
2. **`scripts/clear-test-data.sh`** - Cleanup script

**Implementation:**
```bash
#!/bin/bash
set -e

# ============ Load Environment Variables ============

# Get project root directory
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="$PROJECT_ROOT/.env"

# Load .env file if it exists
if [ -f "$ENV_FILE" ]; then
    set -a  # Automatically export all variables
    source "$ENV_FILE"
    set +a  # Stop auto-exporting
fi

# ============ Configuration ============

# Variables from .env are now available, with defaults as fallback
API_URL="${API_URL:-http://localhost:9000}"
NEO4J_HTTP_PORT="${NEO4J_HTTP_PORT:-7474}"
# ... etc
```

**Usage:**
```bash
# .env is automatically loaded
./scripts/test-ingestion-pipeline.sh

# .env is loaded, then overridden by environment variable
API_URL=http://localhost:9100 ./scripts/test-ingestion-pipeline.sh

# With flags
./scripts/test-ingestion-pipeline.sh --clean
./scripts/clear-test-data.sh --all --force
```

---

## Priority Order

When multiple sources define the same variable, the priority is:

1. **Command-line environment variable** (highest priority)
   ```bash
   API_URL=http://custom:9000 ./scripts/test-ingestion-pipeline.sh
   ```

2. **Exported shell variable**
   ```bash
   export API_URL=http://localhost:9100
   ./scripts/test-ingestion-pipeline.sh
   ```

3. **`.env` file value**
   ```bash
   # .env
   API_URL=http://localhost:9000
   ```

4. **Script default value** (lowest priority)
   ```bash
   API_URL="${API_URL:-http://localhost:9000}"
   ```

---

## Common Environment Variables

### API Service

| Variable | Default (.env) | Script Default | Description |
|----------|----------------|----------------|-------------|
| `API_URL` | `http://localhost:9100` | `http://localhost:9100` | API base URL for external access |
| `API_PORT` | `9100` | (internal only) | API service port (used by Docker) |
| `API_KEY` | (empty) | `test-key-12345` | API authentication key |

### Neo4j

| Variable | Default (.env) | Script Default | Description |
|----------|----------------|----------------|-------------|
| `NEO4J_URI` | `bolt://localhost:8687` | N/A | Neo4j connection URI |
| `NEO4J_HTTP_PORT` | `8474` | `8474` | Neo4j HTTP port |
| `NEO4J_BOLT_PORT` | `8687` | `8687` | Neo4j Bolt port |
| `NEO4J_AUTH` | `neo4j/your_secure_password_here` | N/A | Neo4j authentication |

### Configuration Paths

| Variable | Default | Description |
|----------|---------|-------------|
| `ENTITY_TYPES_CONFIG_PATH` | `config/entity-types.yaml` | Entity types configuration |
| `METADATA_SCHEMA_PATH` | `config/metadata-schema.yaml` | Metadata schema |

### Testing

| Variable | Default | Description |
|----------|---------|-------------|
| `CV_DATA_DIR` | `tests/fixtures/sample-data/cv-pdfs` | CV samples directory |
| `PYTHONPATH` | - | Python module search path |

---

## Examples

### Running Tests with Environment Variables

```bash
# Method 1: Use defaults from .env (automatic)
pytest services/api/tests/integration/test_e2e_cv_ingestion.py -v

# Method 2: Override specific variables
ENTITY_TYPES_CONFIG_PATH=/custom/path/entity-types.yaml \
pytest services/api/tests/integration/test_e2e_cv_ingestion.py -v

# Method 3: Export variables first
export ENTITY_TYPES_CONFIG_PATH=/home/wsluser/dev/rag-engine/config/entity-types.yaml
export METADATA_SCHEMA_PATH=/home/wsluser/dev/rag-engine/config/metadata-schema.yaml
export PYTHONPATH=/home/wsluser/dev/rag-engine/services/api:/home/wsluser/dev/rag-engine
pytest services/api/tests/integration/test_e2e_cv_ingestion.py -v
```

### Running Shell Scripts

```bash
# .env automatically loaded with defaults
./scripts/test-ingestion-pipeline.sh

# Override API URL
API_URL=http://localhost:9100 ./scripts/test-ingestion-pipeline.sh

# Clean mode with custom ports
NEO4J_HTTP_PORT=8474 NEO4J_BOLT_PORT=8687 \
./scripts/test-ingestion-pipeline.sh --clean

# Cleanup with custom data directory
CV_DATA_DIR=/custom/cv/path ./scripts/clear-test-data.sh --all
```

### Running FastAPI Service

```bash
# .env automatically loaded by Pydantic Settings
cd services/api
uvicorn app.main:app --reload

# Override port
API_PORT=9100 uvicorn app.main:app --reload

# With Docker (uses docker-compose.yml environment section)
docker-compose up api
```

---

## Troubleshooting

### Issue: Variables from .env Not Loading

**Check 1:** Verify .env file location
```bash
# Should be at project root
ls -la /home/wsluser/dev/rag-engine/.env
```

**Check 2:** Verify script loads .env
```bash
# For shell scripts, check for this block:
grep -A 5 "Load Environment Variables" scripts/test-ingestion-pipeline.sh
```

**Check 3:** Check variable names (case-sensitive)
```bash
# .env uses exact variable names
API_URL=...  # Correct
api_url=...  # Wrong (case mismatch)
```

### Issue: .env Values Being Ignored

**Cause:** Environment variables already set take priority

**Solution:** Unset conflicting variables
```bash
# Check current environment
env | grep API_URL

# Unset if needed
unset API_URL

# Then run script (will use .env value)
./scripts/test-ingestion-pipeline.sh
```

### Issue: Docker Paths vs Local Paths

**Cause:** `.env` contains Docker container paths like `/app/config/...`

**Solution:** Override for local development
```bash
# For local testing
export ENTITY_TYPES_CONFIG_PATH=/home/wsluser/dev/rag-engine/config/entity-types.yaml
export METADATA_SCHEMA_PATH=/home/wsluser/dev/rag-engine/config/metadata-schema.yaml

# Or set in .env.local (not tracked in git)
# Then load it: source .env.local
```

---

## Best Practices

1. **Keep `.env` in `.gitignore`** - Never commit secrets
2. **Use `.env.example`** - Document all required variables
3. **Override for local development** - Export local paths when needed
4. **Use defaults in scripts** - Fallback values prevent failures
5. **Document environment variables** - Update this guide when adding new vars

---

## Files Modified

The following files were updated to auto-load `.env`:

- [scripts/test-ingestion-pipeline.sh](../scripts/test-ingestion-pipeline.sh)
- [scripts/clear-test-data.sh](../scripts/clear-test-data.sh)

The following files already support `.env` via Pydantic Settings:

- [services/api/app/config.py](../services/api/app/config.py)

---

**Last Updated:** 2025-10-17
