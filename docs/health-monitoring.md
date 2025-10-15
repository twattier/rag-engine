# Health Monitoring Guide

This guide explains how to use RAG Engine's health check endpoints for monitoring and troubleshooting.

## Health Check Endpoint

**Endpoint:** `GET /health`

**Purpose:** Verify that RAG Engine API and all dependencies are operational.

### Healthy Response (HTTP 200)

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

**Fields:**
- `status`: Overall health status (`healthy` or `unhealthy`)
- `service`: Service name
- `version`: API version
- `dependencies`: Health status of each dependency
- `timestamp`: UTC timestamp of health check

### Unhealthy Response (HTTP 503)

```json
{
  "status": "unhealthy",
  "service": "rag-engine-api",
  "version": "0.1.0",
  "dependencies": {
    "neo4j": {
      "status": "unhealthy",
      "error": "ServiceUnavailable: Unable to connect to Neo4j at bolt://neo4j:7687"
    }
  },
  "timestamp": "2025-10-15T10:35:00.000Z"
}
```

**HTTP Status Codes:**
- `200 OK`: All systems operational
- `503 Service Unavailable`: One or more dependencies unhealthy

## Using Health Checks

### Manual Testing

```bash
# Basic health check
curl http://localhost:8000/health

# Pretty-printed JSON
curl -s http://localhost:8000/health | jq

# Check HTTP status code
curl -I http://localhost:8000/health
```

### Docker Healthchecks

RAG Engine API service includes built-in Docker healthcheck:

```yaml
# docker-compose.yml
api:
  healthcheck:
    test: ["CMD-SHELL", "curl -f http://localhost:8000/health || exit 1"]
    interval: 10s
    timeout: 5s
    retries: 5
```

Check container health:
```bash
docker ps
# Look for "(healthy)" status

docker inspect rag-engine-api --format='{{.State.Health.Status}}'
```

### Monitoring Integration

#### Prometheus

Health check can be scraped by Prometheus for alerting:

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'rag-engine-health'
    metrics_path: '/health'
    static_configs:
      - targets: ['api:8000']
```

#### Uptime Monitoring

Services like UptimeRobot, Pingdom, or Healthchecks.io can monitor the health endpoint:

- **URL:** `http://your-domain.com/health`
- **Expected status:** 200
- **Interval:** 60 seconds (recommended)

## Troubleshooting

### Neo4j Unhealthy

**Symptoms:**
```json
{
  "dependencies": {
    "neo4j": {
      "status": "unhealthy",
      "error": "ServiceUnavailable: Unable to connect"
    }
  }
}
```

**Causes & Solutions:**

1. **Neo4j container not running**
   ```bash
   docker ps | grep neo4j
   # If not running:
   docker-compose up -d neo4j
   ```

2. **Neo4j still starting up**
   - Wait 10-30 seconds for Neo4j to initialize
   - Check logs: `docker logs rag-engine-neo4j`

3. **Authentication failure**
   - Verify `NEO4J_AUTH` in `.env` matches Neo4j configuration
   - Reset password if needed (see Neo4j Setup Guide)

4. **Network connectivity**
   - Verify services are on same Docker network
   - Check: `docker network inspect rag-engine-network`

5. **Neo4j out of memory**
   - Check logs for `OutOfMemoryError`
   - Increase heap size in `.env`: `NEO4J_HEAP_MAX=4g`
   - Restart: `docker-compose restart neo4j`

### Slow Response Times

**Symptoms:**
```json
{
  "dependencies": {
    "neo4j": {
      "status": "healthy",
      "response_time_ms": 2500  // > 1 second
    }
  }
}
```

**Causes & Solutions:**

1. **Resource contention**
   - Check system resources: `docker stats`
   - Increase Docker memory allocation

2. **Large knowledge base**
   - Increase Neo4j page cache: `NEO4J_PAGECACHE=4g`
   - Add indexes (done automatically by LightRAG)

3. **Network latency**
   - Ensure API and Neo4j are on same Docker network
   - Avoid running over slow network links

### Health Check Timeout

**Symptoms:**
- Health endpoint times out (no response)
- Docker healthcheck fails repeatedly

**Causes & Solutions:**

1. **API service crashed**
   ```bash
   docker logs rag-engine-api
   # Look for Python exceptions or errors
   ```

2. **API service not started**
   ```bash
   docker-compose up -d api
   ```

3. **Port binding issue**
   - Check if port 8000 is in use
   - Change `API_PORT` in `.env` if needed

## Best Practices

### Production Deployments

1. **Monitor health endpoint regularly** (every 60s)
2. **Set up alerts** for unhealthy status
3. **Include health checks in load balancer** configuration
4. **Log health check failures** for post-mortem analysis

### Development

1. **Check health after code changes** to verify nothing broke
2. **Use health check in CI/CD** to validate deployment
3. **Test failure scenarios** (stop Neo4j, invalid credentials)

### Kubernetes/Orchestration

```yaml
# Example Kubernetes liveness and readiness probes
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10

readinessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5
```

## Future Enhancements

Epic 5 will add additional monitoring capabilities:
- Detailed metrics endpoint (`/api/v1/metrics`)
- Prometheus-compatible metrics
- Performance counters and request statistics
- Resource usage monitoring

See Epic 5 Story 5.3 for details.
