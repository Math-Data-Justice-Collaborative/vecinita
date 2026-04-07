# Environment Variables Contract - Three-Tier Structure

This document describes Vecinita's canonical environment variable organization, which follows the three-tier pattern recommended for multi-service Render deployments.

## Overview: Three Tiers of Environment Variables

```
Tier 1 (SHARED)
├─ Infrastructure: DATABASE_URL, POSTGRES_AUTO_*, etc.
├─ API Keys: GROQ_API_KEY, OPENAI_API_KEY, MODAL_TOKEN_*, etc.
├─ External endpoints: VECINITA_*_API_URL, MODAL_TOKEN_*, etc.
└─ Common settings: LOG_LEVEL, DEFAULT_PROVIDER, etc.
   ↓ Used by: All services (agent, gateway, frontend via build/runtime)

Tier 2 (PER-SERVICE)
├─ Agent-only: EMBEDDING_STRICT_STARTUP, REINDEX_SERVICE_URL, etc.
├─ Gateway-only: ALLOWED_ORIGINS, AGENT_SERVICE_URL, etc.
└─ Frontend-only: VITE_GATEWAY_URL, VITE_AGENT_REQUEST_TIMEOUT_MS, etc.
   ↓ Used by: One service only

Tier 3 (LOCAL DEVELOPMENT)
├─ .env file (git-ignored)
├─ Shell exports: `export FOO=bar`
└─ docker-compose overrides
   ↓ Used by: Local development mode only; never committed to git
```

## Tier 1: Shared Infrastructure Config

These variables apply to **all services** and represent infrastructure-level configuration. Sensitive values (API keys, tokens, passwords) are managed in the Render dashboard with `sync: false`, meaning they are not overwritten by the Blueprint.

### Database Configuration

```env
# Automatically bound by render.yaml fromDatabase bindings
DATABASE_URL=postgresql://vecinita:PASSWORD@dpg-xxxxx.onrender.internal:5432/vecinita
DB_HOST=dpg-xxxxx.onrender.internal
DB_PORT=5432
DB_NAME=vecinita
DB_USER=vecinita
DB_PASSWORD=<secret>
PGHOST=dpg-xxxxx.onrender.internal
PGPORT=5432
PGDATABASE=vecinita
PGUSER=vecinita
PGPASSWORD=<secret>
```

**Why shared:** All services need database access (agent for queries, gateway for sessions, scraper for ingestion).  
**Who owns:** Render database binding (automated, not editable).  
**Can be dashboard-managed:** No, these are automatic from `fromDatabase` bindings.

---

### LLM Provider Configuration

```env
# Which provider to use by default
DEFAULT_PROVIDER=groq                   # values: groq, openai, deepseek, ollama, modal
DEFAULT_MODEL=gpt-4o-mini              # varies by provider

# Groq API
GROQ_API_KEY=gsk_YOUR_KEY_HERE         # sync: false (secret, dashboard-managed)

# OpenAI API
OPENAI_API_KEY=sk-YOUR_KEY_HERE        # sync: false (secret, dashboard-managed)
OPENAI_MODEL_NAME=gpt-4o-mini

# DeepSeek API
DEEPSEEK_API_KEY=sk_YOUR_KEY_HERE      # sync: false (secret, dashboard-managed)
DEEPSEEK_BASE_URL=https://api.deepseek.com

# Ollama (local or remote)
OLLAMA_BASE_URL=http://your-ollama:11434
OLLAMA_MODEL=llama3.1:8b

# Model selection controls
FORCE_LOCAL_MODAL_LLM=false             # if true, prefer local/Modal endpoints
LOCK_MODEL_SELECTION=false              # if true, prevent switching providers
```

**Why shared:** Both agent and gateway need to discover available providers and validate configs.  
**Who owns:** DevOps / Infrastructure team (API key management).  
**Production pattern:** Set actual keys in Render dashboard with `sync: false`; Blueprint has placeholders.

---

### Modal Endpoint Configuration

```env
# Modal-deployed services (scraper, embedding, model)
VECINITA_MODEL_API_URL=https://api.modal.run/v1/your-org/model
VECINITA_EMBEDDING_API_URL=https://api.modal.run/v1/your-org/embedding
VECINITA_SCRAPER_API_URL=https://api.modal.run/v1/your-org/scraper

# Modal authentication
MODAL_TOKEN_ID=your-token-id            # sync: false (secret)
MODAL_TOKEN_SECRET=your-token-secret    # sync: false (secret)
```

**Why shared:** Agent (and gateway, for discovery) need these endpoints to function.  
**Who owns:** DevOps (Modal deployment, token management).  
**Production pattern:** Deploy these services in Modal repo; set URLs and tokens via Render dashboard.

---

### Embedding Service Configuration

If using a local embedding service instead of Modal:

```env
EMBEDDING_SERVICE_URL=http://vecinita-embedding-local:8080  # local
# OR
EMBEDDING_SERVICE_URL=https://api.modal.run/v1/your-org/embedding  # Modal

EMBEDDING_SERVICE_AUTH_TOKEN=<token>    # sync: false (secret, if needed)
EMBEDDING_STRICT_STARTUP=true           # if true, fail startup if unreachable
```

**Why shared:** Both agent and gateway need to validate embedding service availability.  
**Who owns:** DevOps / Infrastructure.  
**Note:** Set to local Docker hostname in local dev; set to Modal URL in production.

---

### PostgreSQL Auto-Configuration

```env
POSTGRES_AUTO_CREATE_VECTOR_EXTENSION=true    # auto-create pgvector on init
POSTGRES_AUTO_BOOTSTRAP_SCHEMA=true           # auto-bootstrap schema on startup
```

**Why shared:** All services benefit from a pre-initialized database.  
**Who owns:** Infrastructure (schema management).  
**Production value:** Always `true` on Render (auto-bootstrapping).

---

### Schema & Vectorization Control

```env
DB_DATA_MODE=normal                     # values: normal, test, mock
VECTOR_SYNC_TARGET=modal                # sync vector updates to this target
```

**Why shared:** Affects how all services interact with the database.  
**Who owns:** Backend lead (data model decisions).

---

### Security & Guardrails

```env
GUARDRAILS_REQUIRE_HUB_VALIDATOR=false
GUARDRAILS_HUB_AUTO_INSTALL=false
GUARDRAILS_PERSISTENCE_DIR=/app/guardrails_cache
```

**Why shared:** Affects request validation across all services.  
**Who owns:** Security team (compliance requirements).

---

### Runtime Configuration

```env
PYTHONUNBUFFERED=1                      # improve logging flush for production
TF_ENABLE_ONEDNN_OPTS=0                 # disable TensorFlow optimizations (if unused)
BACKEND_PREFLIGHT_ENABLED=true          # validate startup state
BACKEND_PREFLIGHT_STRICT=false          # if true, fail startup on validation errors
LOG_LEVEL=info                          # values: debug, info, warning, error, critical
```

**Why shared:** Applied to all services for consistent logging and startup behavior.  
**Who owns:** DevOps / Infrastructure (logging policy).

---

### Observability & Tracing

```env
LANGSMITH_API_KEY=<key>                 # sync: false (secret)
LANGSMITH_PROJECT=vecinita-prod
```

**Why shared:** Both agent and gateway use LangSmith for tracing.  
**Who owns:** DevOps / Observability team.

---

### Optional: Web Search

```env
TAVILY_API_KEY=<key>                    # sync: false (secret); for web search fallback
```

**Why shared:** Agent can use web search if configured.  
**Who owns:** DevOps (API key management).

---

## Tier 2: Per-Service Configuration

These variables apply to **one service only** and are specific to its role.

### Agent-Only Variables

Used by `vecinita-agent` service only. Defined in `agent-config` env group.

```env
# Model selection overrides (agent-specific)
FORCE_LOCAL_MODAL_LLM=false
LOCK_MODEL_SELECTION=false

# Inference server selection
RENDER_REMOTE_INFERENCE_ONLY=false      # if true, disable local inference
RENDER_DISABLE_LOCAL_GUARDRAILS=false

# Reindexing & Administrative
REINDEX_SERVICE_URL=http://scraper:9000
REINDEX_TRIGGER_TOKEN=<secret>          # sync: false
```

**Who sets these:** Backend lead (Agent behavior).  
**When to change:** Adjusting agent inference strategy, enabling/disabling features.

---

### Gateway-Only Variables

Used by `vecinita-gateway` service only. Defined in `gateway-config` env group.

```env
# CORS Policy
ALLOWED_ORIGINS=https://vecinita-frontend.onrender.com,https://custom-domain.com
ALLOWED_ORIGIN_REGEX=https://.*\.onrender\.com

# Timeout Configuration
AGENT_TIMEOUT=30                        # seconds; wait for agent response
AGENT_STREAM_TIMEOUT=120                # seconds; for SSE streams

# Local Admin API
DEV_ADMIN_ENABLED=true                  # if true, expose /admin/* endpoints
DEV_ADMIN_BEARER_TOKEN=<secret>         # sync: false; bearer token for /admin

# LLM Tag Enhancement (optional feature)
ENABLE_LLM_TAG_ENHANCEMENT=false
LLM_TAG_PROVIDER=deepseek
DEEPSEEK_TAG_MODEL=deepseek-chat
GROQ_TAG_MODEL=llama-3.1-8b-instant
```

**Who sets these:** Backend lead, DevOps (API behavior, security).  
**When to change:** Adjusting CORS policy, enabling admin features, tuning timeouts.

---

### Frontend-Only Variables

Used by `vecinita-frontend` service only. Defined in `frontend-config` env group.

```env
# Backend API URL (build-time & runtime)
VITE_GATEWAY_URL=https://vecinita-gateway.onrender.com/api/v1
VITE_BACKEND_URL=https://vecinita-gateway.onrender.com

# Request Timeouts (milliseconds)
VITE_AGENT_REQUEST_TIMEOUT_MS=30000      # regular request timeout (30 seconds)
VITE_AGENT_STREAM_TIMEOUT_MS=120000      # SSE stream timeout (2 minutes)
VITE_AGENT_STREAM_FIRST_EVENT_TIMEOUT_MS=10000  # time to first event (10 seconds)

# Frontend Admin UI (optional)
VITE_DEV_ADMIN_ENABLED=false
VITE_DEV_ADMIN_EMAIL=admin@example.com
VITE_DEV_ADMIN_PASSWORD=<secret>        # sync: false
VITE_DEV_ADMIN_TOKEN=<secret>           # sync: false
```

**Who sets these:** Frontend lead, DevOps (UI configuration).  
**When to change:** Pointing frontend to new API, adjusting timeouts, enabling admin UI.  
**Build-time note:** These are baked into the frontend image at build time (via Vite build args/env).

---

## Tier 3: Local Development Only

These variables are **git-ignored** and used only in local docker-compose or shell environments. They are never deployed to Render.

### Local `.env` file

```bash
# Create in project root, git-ignored
cat > .env << 'EOF'
# Copy Tier 1 & 2 variables from Render dashboard, but use local URLs:

DATABASE_URL=postgresql://postgres:postgres@vecinita-postgres:5432/postgres
EMBEDDING_SERVICE_URL=http://vecinita-embedding:8080
AGENT_SERVICE_URL=http://vecinita-agent:10000
VITE_GATEWAY_URL=http://localhost:8080/api/v1

# Use real API keys (fetch from Render dashboard or create local development keys)
GROQ_API_KEY=gsk_dev_key_for_local_testing
OPENAI_API_KEY=sk_dev_key_for_local_testing

# Local development overrides
DEV_ADMIN_ENABLED=true
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173
LOG_LEVEL=debug
EOF
```

### Local compose overrides

```bash
# Override specific env vars at runtime
docker-compose -f docker-compose.render-parity.yml up -d \
  -e GROQ_API_KEY=gsk_local_key \
  -e LOG_LEVEL=debug
```

### Shell exports

```bash
export GROQ_API_KEY=gsk_local_key
export DATABASE_URL=postgresql://localhost:5432/postgres
docker-compose -f docker-compose.render-parity.yml up -d
```

---

## Governance & Best Practices

### Rule 1: Never Commit Secrets

```bash
# ❌ WRONG (don't do this)
# render.yaml
- key: GROQ_API_KEY
  value: "gsk_real_key_12345"  # EXPOSED IN GIT

# ✅ CORRECT (do this)
# render.yaml
- key: GROQ_API_KEY
  sync: false  # tells Render: use dashboard value, don't override

# Then in Render dashboard: set GROQ_API_KEY to the real key
```

### Rule 2: Use `fromDatabase` and `fromService` Bindings

```bash
# ❌ WRONG (don't hardcode)
- key: DATABASE_URL
  value: "postgresql://..."  # brittle, updates manually

# ✅ CORRECT (Render manages it)
- key: DATABASE_URL
  fromDatabase:
    name: vecinita-postgres
    property: connectionString
```

### Rule 3: Use Environment Groups to Share

```bash
# ❌ WRONG (duplicated across services)
# Agent service
- key: GROQ_API_KEY
  sync: false
- key: OPENAI_API_KEY
  sync: false
# Gateway service
- key: GROQ_API_KEY
  sync: false
- key: OPENAI_API_KEY
  sync: false

# ✅ CORRECT (defined once, referenced by all)
envVarGroups:
  - name: app-shared
    envVars:
      - key: GROQ_API_KEY
        sync: false
      - key: OPENAI_API_KEY
        sync: false

services:
  - name: vecinita-agent
    envVars:
      - fromGroup: app-shared
  - name: vecinita-gateway
    envVars:
      - fromGroup: app-shared
```

### Rule 4: One Place to Update Shared Secrets

If you need to rotate `GROQ_API_KEY`:

1. Update it in **Render Dashboard** (one place)
2. Services pick up the new value on next **redeploy or restart**
3. No need to touch render.yaml

---

## Migration from Old Pattern

If you are migrating from a scattered variable pattern:

1. **Audit current render.yaml** — Find all env vars
2. **Categorize into Tiers** — Which services use each one?
3. **Create env groups** — Define `app-shared`, `agent-config`, `gateway-config`, `frontend-config`
4. **Reference groups in services** — Replace individual vars with `fromGroup:`
5. **Verify dashboard** — Confirm all `sync: false` vars exist in Render dashboard
6. **Test in staging** — Deploy to staging first, verify all services reach each other

---

## Debugging Environment Variables

### Check what services see

```bash
# Inside a running container
docker exec -it vecinita-agent env | sort

# On Render
# Use Render dashboard → Service → Settings → Environment Variables
```

### Verify bindings worked

```bash
# If DATABASE_URL binding didn't work:
docker exec -it vecinita-agent bash
echo $DATABASE_URL
# Should be postgresql://vecinita:PASSWORD@dpg-xxxxx.onrender.internal:5432/vecinita
```

### Test local vs. Render

**Locally:**
```
AGENT_SERVICE_URL=http://vecinita-agent:10000
```

**On Render:**
```
AGENT_SERVICE_URL=http://vecinita-agent.onrender.internal:10000
```

When deployed via Render fromService binding, this is automatic.

---

## Template: Creating a New Service

When adding a new service to Render, create Tier 2 env vars for it:

```yaml
envVarGroups:
  - name: my-service-config
    envVars:
      - key: MY_SERVICE_SETTING_1
        value: "default-value"
      - key: MY_SERVICE_SECRET_TOKEN
        sync: false  # will be set in dashboard

services:
  - type: pserv
    name: vecinita-my-service
    envVars:
      - fromGroup: app-shared  # Tier 1: shared config
      - fromGroup: my-service-config  # Tier 2: my-service-only config
```

Then in Render dashboard, add `vecinita-my-service` to the environment group and set `MY_SERVICE_SECRET_TOKEN`.

---

## Related Documentation

- [SERVICE_BOUNDARIES.md](SERVICE_BOUNDARIES.md) — Which service calls which
- [DEPLOYMENT_WORKFLOW.md](DEPLOYMENT_WORKFLOW.md) — Safe deployment order
- [LOCAL_DEV_SETUP.md](LOCAL_DEV_SETUP.md) — Local development parity
- [Render Documentation: Environment Variables](https://render.com/docs/configure-environment-variables)
