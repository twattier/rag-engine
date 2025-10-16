# RAG Engine Troubleshooting Guide

This guide covers common issues and their solutions.

## Table of Contents

- [Port Conflicts](#port-conflicts)
- [Neo4j Authentication](#neo4j-authentication)
- [Insufficient Memory](#insufficient-memory)
- [Service Startup Timeouts](#service-startup-timeouts)
- [Docker Issues](#docker-issues)
- [Network Issues](#network-issues)
- [Platform-Specific](#platform-specific)

---

## Port Conflicts

### Symptoms

```
Error starting userland proxy: listen tcp4 0.0.0.0:7474: bind: address already in use
```

### Solution

**Option 1: Change RAG Engine Ports**

Edit `.env`:
```bash
NEO4J_HTTP_PORT=7475
NEO4J_BOLT_PORT=7688
API_PORT=8001
```

Restart:
```bash
docker compose down
docker compose up -d
```

**Option 2: Stop Conflicting Service**

Find what's using the port:
```bash
# Linux/macOS
lsof -i :7474

# Kill the process
kill -9 <PID>
```

---

## Neo4j Authentication

### Symptoms

- "The client is unauthorized due to authentication failure"
- Cannot login to Neo4j Browser
- API health check shows Neo4j unhealthy

### Solutions

**1. Verify Credentials**

Check `.env` file:
```bash
grep NEO4J_AUTH .env
```

Format must be: `NEO4J_AUTH=username/password`

**2. Reset Password**

```bash
# Stop Neo4j
docker compose stop neo4j

# Remove data volume (WARNING: deletes all data!)
docker volume rm rag-engine_neo4j-data

# Update .env with new password
nano .env
# Change NEO4J_AUTH=neo4j/NEW_PASSWORD

# Restart Neo4j
docker compose up -d neo4j
```

**3. Check Special Characters**

Avoid special characters in password (`@`, `$`, `/`, `` ` ``).

Use alphanumeric + underscore only: `my_password_123`

---

## Insufficient Memory

### Symptoms

- Services crash or restart repeatedly
- "OutOfMemoryError" in logs
- Docker Compose shows "(unhealthy)" status

### Solutions

**1. Increase Docker Memory Allocation**

**Docker Desktop (macOS/Windows):**
1. Docker Desktop → Settings → Resources
2. Increase Memory to at least 8GB (16GB recommended)
3. Click "Apply & Restart"

**Linux:**
- Docker uses all available system RAM by default
- Ensure at least 8GB system RAM available

**2. Increase Neo4j Memory**

Edit `.env`:
```bash
NEO4J_HEAP_MAX=4g      # Increase from default 2g
NEO4J_PAGECACHE=2g     # Increase from default 1g
```

Restart:
```bash
docker compose restart neo4j
```

**3. Check System Resources**

```bash
# Check available memory
free -h

# Check Docker stats
docker stats

# Check disk space
df -h
```

---

## Service Startup Timeouts

### Symptoms

- Health check fails during validation
- Services shown as "starting" for long time
- Timeout errors in logs

### Solutions

**1. Wait Longer**

Neo4j can take 30-60 seconds to start on first run.

**2. Check Logs**

```bash
# View specific service logs
docker compose logs neo4j
docker compose logs api

# Look for error messages
docker compose logs | grep -i error
```

**3. Verify Dependencies**

API service depends on Neo4j:
```bash
# Ensure Neo4j is healthy first
docker compose ps neo4j

# Then check API
docker compose ps api
```

**4. Restart Services**

```bash
docker compose restart
```

---

## Docker Issues

### Docker Daemon Not Running

**Symptoms:**
```
Cannot connect to the Docker daemon at unix:///var/run/docker.sock
```

**Solutions:**

**Linux:**
```bash
sudo systemctl start docker
sudo systemctl enable docker
```

**macOS/Windows:**
- Start Docker Desktop application

### Permission Denied

**Symptoms:**
```
permission denied while trying to connect to the Docker daemon socket
```

**Solution (Linux):**
```bash
# Add user to docker group
sudo usermod -aG docker $USER

# Log out and back in, or run:
newgrp docker

# Test
docker ps
```

### Image Build Failures

**Symptoms:**
```
ERROR [internal] load build definition from Dockerfile
```

**Solutions:**

1. **Clean Docker cache:**
   ```bash
   docker system prune -a
   ```

2. **Rebuild without cache:**
   ```bash
   docker compose build --no-cache
   docker compose up -d
   ```

3. **Check disk space:**
   ```bash
   df -h
   ```

---

## Network Issues

### Services Can't Communicate

**Symptoms:**
- API can't connect to Neo4j
- Health check shows "ServiceUnavailable"

**Solutions:**

**1. Verify Network**

```bash
docker network ls | grep rag-engine
docker network inspect rag-engine_rag-engine-network
```

**2. Recreate Network**

```bash
docker compose down
docker network prune
docker compose up -d
```

**3. Check Firewall**

Ensure Docker network is not blocked by firewall.

**Linux:**
```bash
# Check firewall status
sudo ufw status

# Allow Docker (if needed)
sudo ufw allow from 172.16.0.0/12 to any
```

### External API Access (Ollama, OpenAI)

**Symptoms:**
- LLM requests timeout
- "Connection refused" for external APIs

**Solutions:**

**1. Use `host.docker.internal`** for services on host:

```bash
# .env
LOCAL_LLM_ENDPOINT=http://host.docker.internal:11434
```

**2. Check network connectivity:**

```bash
# Test from within container
docker compose exec api curl http://host.docker.internal:11434
```

**3. Verify API keys:**

```bash
grep OPENAI_API_KEY .env
# Ensure no leading/trailing spaces
```

---

## Platform-Specific

### Linux

**Issue: SELinux Blocking Volumes**

```bash
# Check SELinux
getenforce

# If "Enforcing", add :z flag to volumes in docker-compose.yml
volumes:
  - ./services/api:/app:z
```

### macOS

**Issue: Slow File Performance**

Symptom: Slow hot-reload during development.

Solution: Avoid mounting large directories. Use Docker volumes for data:

```yaml
volumes:
  - api-cache:/app/.cache  # Use named volume instead of bind mount
```

**Issue: M1/M2 (Apple Silicon) Compatibility**

Use multi-architecture images:
```bash
docker pull --platform linux/amd64 neo4j:5.15-community
```

### Windows WSL2

**Issue: Docker Desktop Not Starting**

1. Enable WSL2 feature:
   ```powershell
   wsl --set-default-version 2
   wsl --install Ubuntu-22.04
   ```

2. Enable integration in Docker Desktop:
   - Settings → Resources → WSL Integration
   - Enable your Ubuntu distro

**Issue: File Path Issues**

Use WSL paths, not Windows paths:

```bash
# ✓ Correct (Linux path in WSL)
cd ~/rag-engine

# ✗ Wrong (Windows path)
cd /mnt/c/Users/username/rag-engine
```

**Issue: Clock Skew**

```bash
# Reset WSL clock
wsl --shutdown
wsl
sudo hwclock -s
```

---

## Still Having Issues?

### Collect Diagnostic Information

```bash
# System info
docker info > diagnostics.txt
docker compose version >> diagnostics.txt

# Service status
docker compose ps >> diagnostics.txt

# Logs
docker compose logs >> diagnostics.log

# Network
docker network inspect rag-engine_rag-engine-network >> diagnostics.txt
```

### Get Help

1. **Check existing issues**: [GitHub Issues](https://github.com/your-org/rag-engine/issues)
2. **Search discussions**: [GitHub Discussions](https://github.com/your-org/rag-engine/discussions)
3. **Create new issue** with diagnostic information

### Debug Mode

Enable debug logging:

```bash
# .env
LOG_LEVEL=DEBUG
LOG_FORMAT=console
```

Restart and check logs:
```bash
docker compose restart
docker compose logs -f
```

---

## Related Documentation

- [Deployment Guide](deployment-guide.md)
- [Neo4j Setup Guide](neo4j-setup.md)
- [Health Monitoring](health-monitoring.md)
- [Logging Guide](logging.md)
