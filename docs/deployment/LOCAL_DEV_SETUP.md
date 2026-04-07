# Local Development Setup - Render Parity Guide

This guide explains how to set up a local development environment that matches Render's topology exactly, enabling you to debug "works locally, fails on Render" issues before they reach production.

## Quick Start

```bash
# Start all services (database, agent, gateway, frontend)
docker-compose -f docker-compose.render-parity.yml up -d --build

# Verify all services are healthy
docker-compose -f docker-compose.render-parity.yml ps

# View logs
docker-compose -f docker-compose.render-parity.yml logs -f vecinita-gateway

# Stop all services
docker-compose -f docker-compose.render-parity.yml down

# Clean up (remove volumes too)
docker-compose -f docker-compose.render-parity.yml down -v
```

## Service Topology

The `docker-compose.render-parity.yml` file defines the canonical local environment that mirrors Render exactly:

```
Browser
  └─ http://localhost:3000 (Frontend - Vite dev server)
       └─ http://localhost:8080/api/v1 (Gateway - public API)
            └─ http://vecinita-agent:10000 (Agent - private service, internal network only)
                 ├─ postgresql://vecinita-postgres:5432 (Database - internal network)
                 └─ EMBEDDING_SERVICE_URL (Modal or local embedding service)
```

## Port Mappings

| Service | Port | Purpose | Access |
|---------|------|---------|--------|
| `vecinita-frontend` | 3000 | React/Vite chat UI | http://localhost:3000 |
| `vecinita-gateway` | 8080 | API router, auth, health | http://localhost:8080 |
| `vecinita-agent` | 10000 | Q&A engine | http://vecinita-agent:10000 (internal only) |
| `vecinita-postgres` | 5432 | PostgreSQL database | postgresql://localhost:5432 (external) or postgresql://vecinita-postgres:5432 (internal) |

**Key principle:** Services reach each other via **internal hostnames** (e.g., `vecinita-agent:10000`), never `localhost` or IP addresses. This matches Render's stable private network behavior.

## Service Descriptions

### vecinita-frontend

- **Type:** Frontend (web service in Render)
- **Technology:** React + Vite dev server
- **Port:** 3000  
- **URL:** http://localhost:3000
- **Calls:** Gateway at `VITE_GATEWAY_URL=http://localhost:8080/api/v1`
- **Purpose:** Chat UI for end users
- **Health Check:** `GET /` (Vite dev server root)

### vecinita-gateway

- **Type:** API / Routing (public web service in Render)
- **Technology:** FastAPI
- **Port:** 8080
- **URL:** http://localhost:8080
- **Calls:** Agent at `AGENT_SERVICE_URL=http://vecinita-agent:10000`
- **Purpose:** Authentication, routing, request authorization, health discovery
- **Health Check:** `GET /health` → 200 OK
- **Endpoints:**
  - `GET /health` — Health check
  - `GET /api/v1/ask` — Proxy to agent
  - `GET /api/v1/config` — LLM provider configuration
  - `GET /admin/reindex` — Trigger reindexing (dev only)

### vecinita-agent

- **Type:** Private service in Render (internal HTTP traffic only)
- **Technology:** FastAPI + LangGraph
- **Port:** 10000
- **URL:** http://vecinita-agent:10000 (internal network only)
- **Calls:**
  - Database at `DATABASE_URL=postgresql://vecinita-postgres:5432/postgres`
  - Embedding service at `EMBEDDING_SERVICE_URL` (Modal or local)
  - Optional scraper/reindex at `REINDEX_SERVICE_URL`
- **Purpose:** Q&A engine, vector search, LLM orchestration
- **Health Check:** `GET /health` → 200 OK
- **Endpoints:**
  - `GET /health` — Health check
  - `GET /ask` — Answer question (async)
  - `GET /ask-stream` — Streaming answer (SSE)
  - `GET /config` — Model configuration

### vecinita-postgres

- **Type:** Database (Render PostgreSQL)
- **Technology:** PostgreSQL 16 + pgvector extension
- **Port:** 5432
- **Connection:**
  - **Internal (from services):** `postgresql://vecinita-postgres:5432/postgres`
  - **External (from host):** `postgresql://localhost:5432/postgres`
- **Credentials:** 
  - User: `postgres`
  - Password: `postgres` (local dev only)
  - Database: `postgres`
- **Purpose:** Vector storage, session management, configuration
- **Health Check:** `pg_isready -U postgres`

## Environment Variables

### Shared (all services in render-parity.yml)

```env
DATABASE_URL=postgresql://postgres:postgres@vecinita-postgres:5432/postgres
DB_HOST=vecinita-postgres
DB_PORT=5432
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=postgres
PGHOST=vecinita-postgres
PGPORT=5432
```

### Agent-specific

```env
DEFAULT_PROVIDER=groq
GROQ_API_KEY=<your-groq-key>
EMBEDDING_SERVICE_URL=http://vecinita-embedding:8080
EMBEDDING_SERVICE_AUTH_TOKEN=<token-if-needed>
PORT=10000
```

### Gateway-specific

```env
PORT=8080
AGENT_SERVICE_URL=http://vecinita-agent:10000
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
DEV_ADMIN_ENABLED=true
DEV_ADMIN_BEARER_TOKEN=vecinita-dev-admin-token-2026
```

### Frontend-specific

```env
VITE_GATEWAY_URL=http://localhost:8080/api/v1
VITE_BACKEND_URL=http://localhost:10000
```

### Optional/Modal-based

```env
# If using Modal instead of local embedding
VECINITA_EMBEDDING_API_URL=https://api.modal.run/...
VECINITA_MODEL_API_URL=https://api.modal.run/...
```

## Setting Environment Variables Locally

### Option 1: Create .env file in project root

```bash
cat > .env << EOF
GROQ_API_KEY=gsk_YOUR_KEY_HERE
EMBEDDING_SERVICE_URL=http://vecinita-embedding:8080
DEFAULT_PROVIDER=groq
EOF

docker-compose -f docker-compose.render-parity.yml up -d
```

### Option 2: Export to shell

```bash
export GROQ_API_KEY=gsk_YOUR_KEY_HERE
export DEFAULT_PROVIDER=groq
docker-compose -f docker-compose.render-parity.yml up -d
```

### Option 3: Pass via docker-compose

```bash
docker-compose -f docker-compose.render-parity.yml up -d \
  --build \
  -e GROQ_API_KEY=gsk_YOUR_KEY_HERE \
  -e DEFAULT_PROVIDER=groq
```

## Testing Service Connectivity

### 1. Is the database healthy?

```bash
docker exec -it vecinita-postgres pg_isready -U postgres
```

**Expected output:** `accepting connections`

### 2. Is the agent healthy?

```bash
curl http://localhost:10000/health
```

**Expected output:**
```json
{
  "status": "ok",
  "timestamp": "2026-04-07T12:00:00Z",
  "checks": {
    "database": "ok",
    "embedding_service": "ok or degraded"
  }
}
```

### 3. Is the gateway healthy?

```bash
curl http://localhost:8080/health
```

**Expected output:**
```json
{
  "status": "ok",
  "timestamp": "2026-04-07T12:00:00Z",
  "agent_url": "http://vecinita-agent:10000"
}
```

### 4. Can frontend reach the gateway?

```bash
curl http://localhost:3000
```

**Expected output:** HTML (Vite dev server)

Then check browser console at http://localhost:3000 for any CORS or connectivity errors.

### 5. Test a complete chat flow

```bash
# From gateway
curl "http://localhost:8080/api/v1/ask?question=Hello"

# Or directly from agent
curl "http://localhost:10000/ask?question=Hello"
```

## Common Issues & Fixes

### Issue: "Cannot connect to Docker daemon"

**Solution:** Ensure Docker Desktop is running or `docker` CLI is available.

```bash
docker ps  # Should list containers, not error
```

### Issue: "driver failed programming external connectivity"

**Ports already in use.** Check what's listening:

```bash
lsof -i :3000   # Frontend port
lsof -i :8080   # Gateway port
lsof -i :10000  # Agent port
lsof -i :5432   # Database port

# Kill the process if needed (example for port 8080)
kill -9 <PID>
```

### Issue: "Database is unhealthy after 1 minute"

**Solution:** Check database logs and migration status:

```bash
docker logs vecinita-postgres | head -20
docker exec -it vecinita-postgres psql -U postgres -c "\dt"
```

If tables are missing, migrations didn't run. Check agent logs:

```bash
docker logs vecinita-agent | grep -i "migrat\|table"
```

### Issue: "Agent cannot connect to embedding service"

**Check which embedding backend is configured:**

```bash
echo $EMBEDDING_SERVICE_URL
# If http://vecinita-embedding:8080, then embedding service must be running
# If https://api.modal.run/..., check VECINITA_EMBEDDING_API_URL instead
```

**If using local embedding, uncomment it in compose file:**

```yaml
  vecinita-embedding:
    build: ...
```

Then rebuild:

```bash
docker-compose -f docker-compose.render-parity.yml up -d --build
```

### Issue: "Gateway cannot reach agent"

**Verify internal network connectivity:**

```bash
# From inside gateway container
docker exec -it vecinita-gateway curl http://vecinita-agent:10000/health

# Should return 200 OK
```

If not, check:
1. Both services are connected to the same network: `vecinita-render-parity`
2. Agent service is running: `docker ps | grep vecinita-agent`
3. Agent port 10000 is exposed in compose file

### Issue: Frontend CORS errors

**Check ALLOWED_ORIGINS environment variable:**

```bash
docker exec -it vecinita-gateway env | grep ALLOWED_ORIGINS
# Should include http://localhost:3000 or http://localhost:5173 (Vite)
```

If missing, add to your `.env`:

```env
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
```

Then restart gateway:

```bash
docker-compose -f docker-compose.render-parity.yml restart vecinita-gateway
```

## Comparing with Render

To verify parity with Render, compare these aspects:

| Aspect | Local (render-parity.yml) | Render |
|--------|---------------------------|--------|
| Database hostname | `vecinita-postgres` | `dpg-xxxxx.onrender.internal` |
| Agent call from gateway | `http://vecinita-agent:10000` | `http://vecinita-agent.onrender.internal:10000` |
| Frontend build | Vite dev server on 3000 | Served from CDN or Node |
| Environment variables | `.env` file | Render dashboard env groups |
| CORS | `http://localhost:3000` | `https://frontend.onrender.com` |
| Health checks | Same endpoints (`/health`) | Same polling logic |

The key difference is:
- **Render:** Service names resolve to `.onrender.internal` (private) or `.onrender.com` (public)
- **Local:** Service names resolve to Docker internal hostnames (same concept, different domain)

Both use the same patterns: service name + port, no IPs, no localhost for inter-service calls.

## Advanced: Debugging with docker-compose logs

```bash
# All services
docker-compose -f docker-compose.render-parity.yml logs -f

# Single service
docker-compose -f docker-compose.render-parity.yml logs -f vecinita-agent

# Last 100 lines, follow
docker-compose -f docker-compose.render-parity.yml logs -f --tail=100 vecinita-gateway

# With timestamps
docker-compose -f docker-compose.render-parity.yml logs -f -t
```

## Advanced: Entering a service container

```bash
# Execute shell in agent
docker exec -it vecinita-agent bash

# Or run a command
docker exec -it vecinita-agent python -c "import sys; print(sys.version)"

# Check environment
docker exec -it vecinita-agent env | grep AGENT_SERVICE_URL
```

## Advanced: Inspecting network

```bash
# Show network details
docker network inspect vecinita-render-parity

# Should show all 4 containers with their IPs
```

## Adding New Services

If you add a new microservice locally:

1. **Add to docker-compose.render-parity.yml:**

```yaml
  my-new-service:
    build:
      context: ./services/my-service
      dockerfile: Dockerfile
    container_name: vecinita-my-service
    ports:
      - "8090:8090"
    environment:
      PORT: "8090"
      DATABASE_URL: "postgresql://postgres:postgres@vecinita-postgres:5432/postgres"
    depends_on:
      vecinita-postgres:
        condition: service_healthy
    networks:
      - vecinita-render-parity
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8090/health"]
      interval: 15s
      timeout: 5s
      retries: 3
    restart: unless-stopped
```

2. **Update dependent services' env vars:**

```yaml
  vecinita-agent:
    environment:
      MY_SERVICE_URL: "http://vecinita-my-service:8090"
```

3. **Restart:**

```bash
docker-compose -f docker-compose.render-parity.yml up -d --build
```

4. **Later, add to Render's render.yaml:**

```yaml
  - type: pserv  # or web
    name: vecinita-my-service
    dockerfilePath: ./services/my-service/Dockerfile
    envVars:
      - fromGroup: app-shared
      - key: MY_SERVICE_URL
        value: "http://vecinita-my-service:8090"
```

## When to Use render-parity.yml vs Other Compose Files

| File | Purpose | When to Use |
|------|---------|------------|
| `docker-compose.render-parity.yml` | Minimal Render-equivalent topology | **Default for daily dev** |
| `docker-compose.yml` | Full local stack (pgAdmin, etc.) | Debugging database issues, admin tasks |
| `docker-compose.microservices.yml` | Testing all microservices (model, embedding, scraper, etc.) | Testing full multi-service flow |
| `docker-compose.render-local.yml` | Render simulation with Ollama | Testing offline/Ollama-based workflows |

**Recommendation:** Use `docker-compose.render-parity.yml` 95% of the time. It's the closest match to Render production and prevents surprises.

## References

- [Render Private Network](https://render.com/docs/private-network)
- [Render Service-to-Service Communication](https://render.com/docs/private-services)
- [Render Health Checks](https://render.com/docs/health-checks)
- [Docker Compose Networking](https://docs.docker.com/compose/networking/)
