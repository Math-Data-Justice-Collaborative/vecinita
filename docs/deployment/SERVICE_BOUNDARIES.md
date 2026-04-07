# Service Boundaries - Vecinita Multi-Service Architecture

This document clarifies which services are public, private, external, and how they interact on Render.

## Core Principle

**Only the frontend and API (gateway) should be public.** Everything else should be private or external unless there is a very specific reason not to be.

## Service Classification

### Public Web Services (onrender.com domains)

These services have public URLs accessible from the internet and serve end-user or critical-path traffic.

#### `vecinita-frontend`

**Type:** Public Web Service  
**URL:** `https://vecinita-frontend.onrender.com` (or custom domain)  
**Port (externally):** 443 (HTTPS) / 80 (HTTP)  
**Port (internally):** 10000  
**Technology:** React + Vite (or Node.js in production)  

**Purpose:**  
- User-facing chat interface
- Authentication UI (if applicable)
- Static assets (CSS, JS, images)

**Calls to:**
- `vecinita-gateway:8080` (public URL `https://vecinita-gateway.onrender.com/api/v1`)

**Called by:**
- End-user browsers
- Data Management Frontend (if applicable)

**Health Check:**
- `GET /` (responds with HTML/200)

**Why public:**
- Users need to access it directly from their browsers
- No intermediate routing layer required

---

#### `vecinita-gateway`

**Type:** Public Web Service  
**URL:** `https://vecinita-gateway.onrender.com` (or custom domain)  
**Port (externally):** 443 (HTTPS) / 80 (HTTP)  
**Port (internally):** 8080  
**Technology:** FastAPI (Python)  

**Purpose:**
- API entry point for frontend
- Authentication / authorization enforcement
- Request routing to agent
- Admin endpoints (if `DEV_ADMIN_ENABLED=true`)
- Health discovery for frontend
- CORS handling

**Calls to:**
- `vecinita-agent:10000` (internal private service)
- Various LLM providers (Groq, OpenAI, Modal, Ollama)
- `vecinita-postgres:5432` (database, internal)

**Called by:**
- `vecinita-frontend` (public URL)
- Data Management Frontend (public URL)
- End-user REST clients
- Admin tools (if enabled)

**Health Check:**
- `GET /health` (responds with JSON/200)
- Also at `GET /api/v1/health` (compatibility endpoint)

**API Endpoints:**
- `GET /health` — Health check
- `GET /api/v1/ask?question=...` — Ask a question
- `GET /api/v1/config` — Get LLM provider config
- `POST /api/v1/ask-stream` — Stream answer (SSE)
- `GET /admin/reindex` — Trigger reindexing (dev only, if enabled)

**Why public:**
- Frontend must call it directly from the browser
- Browser CORS rules require public endpoint
- Admin features optionally exposed (with bearer token protection)

---

### Private Web Services (onrender.internal domains)

These services receive HTTP traffic **only from other Render services on the private network**. They do not have public URLs.

#### `vecinita-agent`

**Type:** Private Web Service  
**URL (internal only):** `http://vecinita-agent.onrender.internal:10000` (on Render) or `http://vecinita-agent:10000` (local Docker)  
**Port:** 10000  
**Technology:** FastAPI + LangGraph (Python)  

**Purpose:**
- Q&A engine core logic
- Vector similarity search
- LLM orchestration
- Source attribution

**Calls to:**
- `vecinita-postgres:5432` (database, internal)
- Modal API endpoints (external, for scraper/embedding/model)
- LLM providers (Groq, OpenAI, etc.)
- Optional: `vecinita-scraper` (if reindexing)

**Called by:**
- `vecinita-gateway` (private network only)

**Health Check:**
- `GET /health` (responds with JSON/200)

**Endpoints:**
- `GET /health` — Health check
- `GET /ask?question=...` — Synchronous Q&A
- `GET /ask-stream?question=...` — Streaming Q&A (SSE)
- `GET /config` — Model configuration
- `GET /db-search?query=...` — Raw vector search
- Internal tools: `/rank`, `/rewrite-question`, `/clarify`

**Why private:**
- Only the gateway and internal administrative tools should call it
- Users and external systems must go through the gateway
- Reduces attack surface (no public IP, no internet routing)
- Render's internal network is faster and more secure than public internet

---

### External Services (Modal or 3rd-party APIs)

These services are deployed outside Render and accessed via public HTTP/HTTPS endpoints.

#### `vecinita-scraper` (Modal deployed)

**Type:** External API (Modal)  
**URL:** `https://api.modal.run/v1/your-org/vecinita-scraper` (or similar)  
**Port:** 443 (HTTPS)  
**Technology:** Modal serverless (Python)  

**Purpose:**
- Web scraping and document ingestion
- Chunking and preprocessing
- Scheduled data reprocessing

**Calls to:**
- `vecinita-postgres:5432` (via Render internal URL if whitelisted, or external)
- 3rd-party websites (for scraping)
- `vecinita-embedding` (to embed chunks)

**Called by:**
- `vecinita-agent` (for reindexing jobs)
- Administration tools (manual triggers)

**Why external:**
- Resource-intensive (long-running, bursty load)
- Modal handles scaling, concurrency, cold starts better than fixed Render instances
- Can pull from external data sources without Render network restrictions
- Scheduled and triggered workflows fit Modal's execution model

---

#### `vecinita-embedding` (Modal deployed)

**Type:** External API (Modal)  
**URL:** `https://api.modal.run/v1/your-org/vecinita-embedding` (or similar)  
**Port:** 443 (HTTPS)  
**Technology:** Modal serverless (Python)  

**Purpose:**
- Generate embeddings for queries and documents
- Fast vector representation of text

**Calls to:**
- HuggingFace transformer models (cached locally in Modal)

**Called by:**
- `vecinita-agent` (for query embeddings during search)
- `vecinita-scraper` (for document embeddings)

**Why external:**
- Compute-intensive (GPU-friendly on Modal)
- Stateless (no session state to maintain)
- Consistent latency and availability as a dedicated Modal endpoint
- Modal auto-scales replicas based on load

---

#### `vecinita-model` (Modal deployed)

**Type:** External API (Modal)  
**URL:** `https://api.modal.run/v1/your-org/vecinita-model` (or similar)  
**Port:** 443 (HTTPS)  
**Technology:** Modal serverless (Python) or Ollama  

**Purpose:**
- LLM inference (optional, if using local model instead of Groq/OpenAI)
- Used when `DEFAULT_PROVIDER=modal` or `OLLAMA_BASE_URL` is set

**Calls to:**
- LLM weights (HuggingFace, downloaded into Modal)

**Called by:**
- `vecinita-agent` (for LLM predictions)

**Why external:**
- Compute-intensive (GPU required for fast inference)
- Modal handles scaling and GPU provisioning
- Simplifies Render setup (no need for GPU instances)
- Optional (can use Groq/OpenAI API instead)

---

### Databases & Infrastructure

#### `vecinita-postgres` (Render PostgreSQL)

**Type:** Private Database  
**URL (internal):** `postgresql://dpg-xxxxx.onrender.internal:5432/vecinita` (on Render)  
**URL (external):** `postgresql://user:passwd@dpg-xxxxx.onrender.com:5432/vecinita`  
**Port:** 5432  

**Purpose:**
- Vector storage (pgvector extension)
- Session management
- Configuration and metadata

**Accessed by:**
- `vecinita-agent` (read/write)
- `vecinita-gateway` (read, for session/config)
- `vecinita-scraper` (write, for ingestion)
- Local tools (via external URL)

**Why private/Render:**
- Data persistence tied to Render services
- Private network for fast, secure access
- Auto-backups, managed by Render
- pgvector extension support out-of-the-box

---

## Communication Patterns

### Internal Service-to-Service (Private Network)

```
Gateway
  → http://vecinita-agent:10000/ask
       ↓
Agent
  → postgresql://dpg-xxxxx.onrender.internal:5432/vecinita
  → https://api.modal.run/v1/scraper (external)
  → https://api.modal.run/v1/embedding (external)
  → https://api.groq.com (external API)
```

**Characteristics:**
- Fast (same region, private network)
- No CORS checks
- No firewall ingress rules needed (Render manages it)
- Credentials passed in env vars or request headers

### External API Calls

```
Agent / Gateway
  → https://api.groq.com (GROQ_API_KEY in header)
  → https://api.openai.com (OPENAI_API_KEY in header)
  → https://api.modal.run/v1/scraper (Modal auth token in header)
```

**Characteristics:**
- Goes over public internet
- Subject to rate limiting (provider-specific)
- Requires valid credentials
- Potential for outages if external service fails

### Browser-to-Public (CORS-protected)

```
Browser (https://custom-domain.com)
  → https://vecinita-gateway.onrender.com/api/v1/ask
       ↓
Gateway validates CORS (ALLOWED_ORIGINS)
       ↓
Gateway
  → http://vecinita-agent:10000/ask (internal, no CORS check)
```

**Characteristics:**
- Subject to CORS policy (`ALLOWED_ORIGINS` env var)
- TLS encryption (HTTPS)
- User authentication (if implemented)
- Gateway enforces authorization before calling agent

---

## Network Isolation Rules

1. **Frontend cannot call Agent directly** — Always through Gateway
   - Enforces authentication
   - Central logging and rate limiting
   - Simpler debugging of who's calling what

2. **Agent cannot accept external requests** — Always private
   - No random internet traffic can reach it
   - Callers must be on Render's private network or authenticated
   - Reduces attack surface

3. **Database is private** — Only Render services access via internal URL
   - External URL exists for local tools (only expose to specific IPs)
   - Production services use internal URL
   - Passwords never exposed in logs

4. **Modal services authenticate via header tokens** — Not via TLS client certs
   - `X-Proxy-Token` or `Authorization: Bearer <token>` in requests
   - Tokens stored as `sync: false` env vars in Render dashboard
   - Never hardcoded in render.yaml

---

## Debugging Service Connectivity

### Question: "Frontend can't call Gateway"

**Possible causes:**
1. CORS error → Check `ALLOWED_ORIGINS` in gateway env
2. Network error → Gateway not responding to `GET /health`?
3. Public DNS → Frontend URL resolves correctly?

**Debug steps:**
```bash
# 1. Is gateway healthy?
curl https://vecinita-gateway.onrender.com/health

# 2. Is CORS configured?
curl -H "Origin: https://vecinita-frontend.onrender.com" \
     https://vecinita-gateway.onrender.com/health

# 3. Check gateway logs for CORS errors
```

### Question: "Gateway can't reach Agent"

**Possible causes:**
1. Agent not healthy → `GET /health` returns 500
2. Wrong URL → `AGENT_SERVICE_URL=http://vecinita-agent` (missing `:10000`)
3. Agent service type wrong → Must be web, not worker

**Debug steps:**
```bash
# 1. Inside gateway container, ping agent
docker exec -it vecinita-gateway curl http://vecinita-agent:10000/health

# 2. Check gateway logs for connection errors
docker logs vecinita-gateway | grep -i agent

# 3. Verify AGENT_SERVICE_URL binding
docker exec -it vecinita-gateway env | grep AGENT_SERVICE_URL
```

### Question: "Agent can't reach Database"

**Possible causes:**
1. Database not ready → Startup race condition
2. Wrong connection string → `DATABASE_URL` points to wrong host/port/credentials
3. Migration failed → Schema doesn't exist

**Debug steps:**
```bash
# 1. Can you connect externally?
psql -h dpg-xxxxx.onrender.com -U vecinita -d vecinita

# 2. Inside agent container
docker exec -it vecinita-agent psql -c "SELECT 1"

# 3. Check agent startup logs for DB connection errors
docker logs vecinita-agent | grep -i "database\|connection"
```

### Question: "Agent can't reach Modal (embedding/scraper/model)"

**Possible causes:**
1. Wrong URL → `VECINITA_EMBEDDING_API_URL` typo or wrong endpoint
2. Auth token missing → `MODAL_TOKEN_ID` / `MODAL_TOKEN_SECRET` not set
3. Modal service not deployed → Endpoint returns 404
4. Firewall/IP blocking → Render IP is not whitelisted on Modal

**Debug steps:**
```bash
# 1. Test Modal endpoint directly from agent
docker exec -it vecinita-agent curl https://api.modal.run/v1/your-org/vecinita-embedding

# 2. Check env var
docker exec -it vecinita-agent env | grep MODAL

# 3. Check agent logs for Modal auth errors
docker logs vecinita-agent | grep -i "modal\|401\|unauthorized"
```

---

## Updating Service Communication

### Scenario: Moving embedding from Modal to local

1. **Add local embedding service** to render.yaml:
   ```yaml
   - type: pserv
     name: vecinita-embedding-local
     docker...
   ```

2. **Update agent env var:**
   ```yaml
   - key: EMBEDDING_SERVICE_URL
     value: "http://vecinita-embedding-local:8080"
   ```

3. **Remove old Modal env var:**
   ```yaml
   - key: VECINITA_EMBEDDING_API_URL
     sync: false  # or remove entirely
   ```

### Scenario: Adding a new internal service

1. **Define in render.yaml:**
   ```yaml
   - type: pserv  # private service
     name: vecinita-jobs-worker
     docker...
     envVars:
       - fromGroup: app-shared
   ```

2. **Update gateway or agent to reach it:**
   ```yaml
   # In agent or gateway
   - key: JOBS_WORKER_URL
     fromService:
       name: vecinita-jobs-worker
       type: pserv  # note: private service type
       property: host
   ```

3. **Add health check:**
   ```yaml
     healthCheckPath: /health
   ```

---

## Related Documentation

- [Render Private Network Docs](https://render.com/docs/private-network)
- [Render Private Services](https://render.com/docs/private-services)
- [Render Health Checks](https://render.com/docs/health-checks)
- [ENV_GROUPS_CONTRACT.md](ENV_GROUPS_CONTRACT.md) — Environment variable ownership
- [DEPLOYMENT_WORKFLOW.md](DEPLOYMENT_WORKFLOW.md) — Safe deployment order
