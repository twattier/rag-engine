# Neo4j Setup and Configuration Guide

This guide covers Neo4j deployment, configuration, and troubleshooting for RAG Engine.

## Overview

RAG Engine uses **Neo4j 5.x Community Edition** as the combined graph and vector database. Neo4j stores:
- **Knowledge Graph**: Entities, relationships, documents
- **Vector Embeddings**: For similarity search and hybrid retrieval
- **Metadata**: Custom metadata fields for filtering

## Accessing Neo4j Browser

Neo4j Browser provides a web-based interface for graph exploration and Cypher queries.

**URL:** `http://localhost:7474`

**Default Credentials:**
- **Username:** `neo4j`
- **Password:** Set in `.env` file as `NEO4J_AUTH=neo4j/YOUR_PASSWORD`

### First-Time Login

1. Open `http://localhost:7474` in your browser
2. Enter **Connect URL:** `bolt://localhost:7687`
3. Enter credentials from `.env` file
4. Click **Connect**

## Changing Neo4j Credentials

**IMPORTANT:** Change the default password before production deployment.

### Method 1: Update `.env` Before First Start

Edit `.env` file:
```bash
NEO4J_AUTH=neo4j/your-strong-password-here
```

Then start services:
```bash
docker-compose up -d
```

### Method 2: Reset Password on Running Instance

1. Stop Neo4j container:
   ```bash
   docker-compose stop neo4j
   ```

2. Remove existing data volume (WARNING: destroys all data):
   ```bash
   docker volume rm rag-engine_neo4j-data
   ```

3. Update `.env` with new password:
   ```bash
   NEO4J_AUTH=neo4j/new-password-here
   ```

4. Restart Neo4j:
   ```bash
   docker-compose up -d neo4j
   ```

## Neo4j Memory Configuration

Neo4j memory settings significantly impact performance for large knowledge bases.

### Memory Settings in `.env`

```bash
# Initial heap size (allocated at startup)
NEO4J_HEAP_INITIAL=1g

# Maximum heap size (JVM heap memory)
# Recommended: 4g for 1k documents, 8g for 10k+ documents
NEO4J_HEAP_MAX=2g

# Page cache size (stores graph data in memory)
# Recommended: 2g for 1k documents, 4g for 10k+ documents
NEO4J_PAGECACHE=1g
```

### Recommended Settings by Knowledge Base Size

| Documents | HEAP_MAX | PAGECACHE | Total RAM |
|-----------|----------|-----------|-----------|
| < 500     | 2g       | 1g        | 8GB       |
| 500-1k    | 4g       | 2g        | 16GB      |
| 1k-10k    | 8g       | 4g        | 32GB      |
| 10k+      | 16g      | 8g        | 64GB      |

## Volume Backup and Restore

Neo4j data is persisted to Docker volume `rag-engine_neo4j-data`.

### Backup Neo4j Database

**Option 1: Manual Backup (Recommended)**

```bash
# Stop Neo4j service
docker-compose stop neo4j

# Create backup directory
mkdir -p ./backups

# Copy data volume to backup
docker run --rm \
  -v rag-engine_neo4j-data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/neo4j-backup-$(date +%Y%m%d-%H%M%S).tar.gz -C /data .

# Restart Neo4j
docker-compose start neo4j
```

**Option 2: Automated Backup Script**

Use provided script:
```bash
./scripts/backup-neo4j.sh
```

### Restore Neo4j Database

```bash
# Stop Neo4j service
docker-compose stop neo4j

# Remove existing data volume
docker volume rm rag-engine_neo4j-data

# Recreate volume
docker volume create rag-engine_neo4j-data

# Restore from backup
docker run --rm \
  -v rag-engine_neo4j-data:/data \
  -v $(pwd)/backups:/backup \
  alpine sh -c "cd /data && tar xzf /backup/neo4j-backup-YYYYMMDD-HHMMSS.tar.gz"

# Restart Neo4j
docker-compose start neo4j
```

## Troubleshooting

### Issue: Cannot Connect to Neo4j Browser

**Symptoms:**
- `http://localhost:7474` shows "Connection refused" or timeout
- Neo4j Browser shows "ServiceUnavailable" error

**Solutions:**

1. **Check Neo4j container is running:**
   ```bash
   docker ps | grep neo4j
   ```

   If not running:
   ```bash
   docker-compose up -d neo4j
   ```

2. **Check Neo4j logs:**
   ```bash
   docker logs rag-engine-neo4j
   ```

   Look for errors like:
   - `OutOfMemoryError` → Increase heap size in `.env`
   - `Address already in use` → Port 7474/7687 conflict, change ports in `.env`

3. **Verify port binding:**
   ```bash
   docker port rag-engine-neo4j
   ```

   Should show:
   ```
   7474/tcp -> 0.0.0.0:7474
   7687/tcp -> 0.0.0.0:7687
   ```

4. **Check firewall:**
   Ensure ports 7474 and 7687 are not blocked by firewall.

### Issue: Authentication Failed

**Symptoms:**
- "The client is unauthorized due to authentication failure"

**Solutions:**

1. **Verify credentials in `.env`:**
   ```bash
   grep NEO4J_AUTH .env
   ```

   Format must be: `NEO4J_AUTH=username/password`

2. **Reset password** (see "Changing Neo4j Credentials" above)

3. **Check for special characters:**
   Avoid characters like `@`, `$`, `/` in password (use alphanumeric + `_` only)

### Issue: Port Conflicts

**Symptoms:**
- Error: "bind: address already in use"
- Neo4j fails to start

**Solutions:**

1. **Check what's using the ports:**
   ```bash
   lsof -i :7474
   lsof -i :7687
   ```

2. **Change ports in `.env`:**
   ```bash
   NEO4J_HTTP_PORT=7475
   NEO4J_BOLT_PORT=7688
   ```

3. **Restart services:**
   ```bash
   docker-compose down
   docker-compose up -d
   ```

### Issue: Out of Memory Errors

**Symptoms:**
- Neo4j crashes during queries
- Logs show `java.lang.OutOfMemoryError`

**Solutions:**

1. **Increase heap size:**
   ```bash
   NEO4J_HEAP_MAX=4g
   ```

2. **Increase Docker Desktop memory allocation:**
   - Docker Desktop → Settings → Resources → Memory
   - Allocate at least 8GB for RAG Engine

3. **Check system resources:**
   ```bash
   docker stats rag-engine-neo4j
   ```

### Issue: Slow Query Performance

**Solutions:**

1. **Increase page cache:**
   ```bash
   NEO4J_PAGECACHE=4g
   ```

2. **Create indexes** (done automatically by LightRAG, but verify):
   ```cypher
   // Check existing indexes
   SHOW INDEXES

   // Create index on document IDs (if missing)
   CREATE INDEX document_id IF NOT EXISTS FOR (d:Document) ON (d.doc_id)

   // Create index on entity names (if missing)
   CREATE INDEX entity_name IF NOT EXISTS FOR (e:Entity) ON (e.entity_name)
   ```

3. **Monitor query performance:**
   ```cypher
   // Enable query logging
   CALL dbms.setConfigValue('dbms.logs.query.enabled', 'true')

   // Check slow queries
   CALL dbms.listQueries()
   ```

## Advanced Configuration

### Enable APOC Plugins

APOC (Awesome Procedures On Cypher) provides additional functionality.

Edit `docker-compose.yml`:
```yaml
neo4j:
  environment:
    - NEO4J_PLUGINS=["apoc"]
```

Restart Neo4j:
```bash
docker-compose restart neo4j
```

Verify APOC is loaded:
```cypher
CALL apoc.help("apoc")
```

### Enable Query Logging

Edit `.env`:
```bash
NEO4J_dbms_logs_query_enabled=true
NEO4J_dbms_logs_query_threshold=1s
```

Query logs appear in: `docker logs rag-engine-neo4j`

## Useful Cypher Queries

### Check Database Size
```cypher
// Count nodes by label
MATCH (n)
RETURN labels(n) AS label, count(*) AS count
ORDER BY count DESC

// Count relationships by type
MATCH ()-[r]->()
RETURN type(r) AS relationship, count(*) AS count
ORDER BY count DESC

// Database size estimate
CALL apoc.meta.stats()
```

### Inspect Knowledge Graph
```cypher
// View sample documents
MATCH (d:Document)
RETURN d
LIMIT 10

// View sample entities
MATCH (e:Entity)
RETURN e.entity_name, e.entity_type
LIMIT 20

// View entity relationships
MATCH (e1:Entity)-[r]->(e2:Entity)
RETURN e1.entity_name, type(r), e2.entity_name
LIMIT 20
```

### Clear All Data (Caution!)
```cypher
// Delete all nodes and relationships
MATCH (n)
DETACH DELETE n
```

## Platform-Specific Notes

### Linux
- No special configuration required
- Ensure user is in `docker` group: `sudo usermod -aG docker $USER`

### macOS
- Use Docker Desktop for Mac
- Allocate sufficient memory (16GB recommended) in Docker Desktop settings

### Windows (WSL2)
- Run Docker Desktop with WSL2 backend
- Access Neo4j Browser from Windows browser: `http://localhost:7474`
- File paths in WSL: `/mnt/c/Users/...` for Windows directories

## Next Steps

After Neo4j is running:
1. Run connection test: `./scripts/test-neo4j-connection.py`
2. Proceed to Story 1.3: Create API Service
3. Configure API service to connect to Neo4j

## References

- [Neo4j Documentation](https://neo4j.com/docs/)
- [Neo4j Docker Image](https://hub.docker.com/_/neo4j)
- [Cypher Query Language](https://neo4j.com/docs/cypher-manual/current/)
