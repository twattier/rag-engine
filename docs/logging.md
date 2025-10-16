# Logging Guide

RAG Engine uses structured logging with `structlog` for consistent, parseable log output across all services.

## Log Format

### JSON Format (Production)

Set `LOG_FORMAT=json` in `.env` for machine-readable JSON logs:

```json
{
  "timestamp": "2025-10-15T10:30:45.123Z",
  "level": "info",
  "service": "api",
  "logger": "app.routers.health",
  "event": "health_check_requested",
  "request_id": "abc123-def456"
}
```

### Console Format (Development)

Set `LOG_FORMAT=console` in `.env` for human-readable colored logs:

```
2025-10-15 10:30:45 [info     ] health_check_requested    [app.routers.health] request_id=abc123-def456 service=api
```

## Viewing Logs

### All Services

```bash
# View all logs
docker-compose logs

# Follow all logs (live tail)
docker-compose logs -f

# View last 100 lines
docker-compose logs --tail=100
```

### Specific Service

```bash
# View API service logs
docker-compose logs api

# Follow API service logs
docker-compose logs -f api

# View Neo4j logs
docker-compose logs neo4j
```

### Filter by Timestamp

```bash
# Logs since specific time
docker-compose logs --since 2025-10-15T10:00:00

# Logs from last hour
docker-compose logs --since 1h

# Logs from last 30 minutes
docker-compose logs --since 30m
```

## Log Levels

Configure via `LOG_LEVEL` in `.env`:

- **DEBUG**: Detailed debugging information (verbose)
- **INFO**: General informational messages (default)
- **WARNING**: Warning messages for unexpected situations
- **ERROR**: Error messages for failures
- **CRITICAL**: Critical failures requiring immediate attention

### Example: Debug Mode

```bash
# .env
LOG_LEVEL=DEBUG
LOG_FORMAT=console
```

Restart services:
```bash
docker-compose restart api
```

## Common Log Events

### Service Lifecycle

```json
// Service startup
{"event": "api_service_starting", "version": "0.1.0", "level": "info"}

// Service shutdown
{"event": "api_service_shutting_down", "level": "info"}
```

### HTTP Requests

```json
// Request started
{"event": "request_started", "method": "GET", "path": "/health", "level": "info"}

// Request completed
{"event": "request_completed", "method": "GET", "path": "/health", "status_code": 200, "duration_ms": 45.2, "level": "info"}

// Request failed
{"event": "request_failed", "method": "POST", "path": "/api/v1/query", "error": "ValueError: Invalid query", "level": "error"}
```

### Neo4j Operations

```json
// Connection success
{"event": "neo4j_driver_connected", "uri": "bolt://neo4j:7687", "level": "info"}

// Connection failure
{"event": "neo4j_connection_failed", "uri": "bolt://neo4j:7687", "error": "ServiceUnavailable", "level": "error"}

// Connectivity verified
{"event": "neo4j_connectivity_verified", "response_time_ms": 42.1, "attempt": 1, "level": "info"}
```

### Health Checks

```json
// Health check failure
{"event": "health_check_neo4j_unhealthy", "error": "Connection timeout", "level": "error"}
```

### Unhandled Exceptions

```json
// Exception with stack trace
{
  "event": "unhandled_exception",
  "path": "/api/v1/query",
  "method": "POST",
  "error": "division by zero",
  "error_type": "ZeroDivisionError",
  "level": "error",
  "exc_info": "Traceback (most recent call last):\n  ..."
}
```

## Request Tracing

Each HTTP request is assigned a unique `request_id` that appears in all related log entries:

```json
{"event": "request_started", "request_id": "a1b2c3d4-e5f6-7890", ...}
{"event": "neo4j_query_executed", "request_id": "a1b2c3d4-e5f6-7890", ...}
{"event": "request_completed", "request_id": "a1b2c3d4-e5f6-7890", ...}
```

Response headers include `X-Request-ID` for client-side correlation.

## Filtering and Searching Logs

### Using `jq` (JSON Logs)

```bash
# Filter by log level
docker-compose logs api | jq 'select(.level == "error")'

# Filter by event
docker-compose logs api | jq 'select(.event == "request_completed")'

# Extract specific fields
docker-compose logs api | jq '{timestamp, level, event, duration_ms}'

# Find slow requests (> 1000ms)
docker-compose logs api | jq 'select(.duration_ms > 1000)'
```

### Using `grep` (Console Logs)

```bash
# Find errors
docker-compose logs api | grep ERROR

# Find specific event
docker-compose logs api | grep "health_check_requested"

# Find requests to specific path
docker-compose logs api | grep "path=/api/v1/query"
```

## Log Aggregation (Production)

For production deployments, consider log aggregation solutions:

### ELK Stack (Elasticsearch, Logstash, Kibana)

```yaml
# docker-compose.override.yml (production)
services:
  api:
    logging:
      driver: "syslog"
      options:
        syslog-address: "tcp://logstash:5000"
        tag: "rag-engine-api"
```

### Loki + Grafana

```yaml
services:
  api:
    logging:
      driver: "loki"
      options:
        loki-url: "http://loki:3100/loki/api/v1/push"
        labels: "service=rag-engine-api"
```

### Cloud Logging (AWS CloudWatch, GCP Cloud Logging)

Configure Docker logging driver for your cloud provider.

## Troubleshooting with Logs

### API Not Responding

```bash
# Check if API started successfully
docker-compose logs api | grep "api_service_starting"

# Look for errors during startup
docker-compose logs api | grep ERROR

# Check if port is bound
docker-compose logs api | grep "port"
```

### Neo4j Connection Issues

```bash
# Filter Neo4j-related logs
docker-compose logs api | grep neo4j

# Look for connection failures
docker-compose logs api | jq 'select(.event | contains("neo4j"))'
```

### Slow Performance

```bash
# Find slow requests (JSON format)
docker-compose logs api | jq 'select(.duration_ms > 2000)'

# Average request duration (requires jq processing)
docker-compose logs api | jq -s '[.[] | select(.duration_ms) | .duration_ms] | add / length'
```

### Recent Errors

```bash
# Last 50 error logs
docker-compose logs --tail=1000 api | jq 'select(.level == "error")' | tail -50

# Errors in last hour
docker-compose logs --since 1h api | grep ERROR
```

## Best Practices

1. **Use JSON format in production** for log aggregation and parsing
2. **Use console format in development** for readability
3. **Set appropriate log level**:
   - Production: `INFO` or `WARNING`
   - Development: `DEBUG`
   - Troubleshooting: `DEBUG` temporarily
4. **Include context** in log messages (user_id, request_id, document_id)
5. **Log errors with stack traces** using `exc_info=True`
6. **Avoid logging sensitive data** (passwords, API keys, PII)
7. **Use structured fields** instead of string interpolation

### Good Example

```python
logger.info(
    "document_ingested",
    doc_id=doc_id,
    file_name=file_name,
    file_size_bytes=file_size,
    duration_ms=duration,
)
```

### Bad Example

```python
logger.info(f"Ingested document {doc_id} with name {file_name} ({file_size} bytes) in {duration}ms")
```

## Future Enhancements

Epic 5 Story 5.3 will add:
- Metrics endpoint for Prometheus
- Performance counters and statistics
- Log sampling for high-volume production environments
- Integration with APM tools (Datadog, New Relic)
