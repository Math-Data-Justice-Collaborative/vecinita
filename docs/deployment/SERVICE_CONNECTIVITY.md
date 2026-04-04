# Service Connectivity & Endpoint Configuration

## Overview

All Vecinita backend services (agent, gateway) resolve internal service endpoints (embedding, Ollama) through a **unified configuration layer** in `src/config.py`. This ensures consistent endpoint routing across local development and Render deployments.

## Unified Configuration

### Source of Truth: `src/config.py`

The `_normalize_internal_service_url()` function in `src/config.py` implements the routing logic for all backend services:

```python
def _normalize_internal_service_url(raw_url: str | None, *, fallback_url: str) -> str:
    """Resolve effective URL for internal upstream services."""
```

**Key behaviors:**
- **On Render**: Forces all traffic through the `vecinita-direct-routing` private service to avoid connection refused errors
- **Off Render (local dev)**: Uses raw environment URLs if available, with fallback only when needed

### Configured Endpoints

Two endpoints are normalized globally:

1. **EMBEDDING_SERVICE_URL**
   - Raw sources: `MODAL_EMBEDDING_ENDPOINT` or `EMBEDDING_SERVICE_URL` env var
   - Fallback (Render): `http://vecinita-embedding-ms-render:8011`
   - Fallback (local dev): defaults to raw URL, no localhost override

2. **OLLAMA_BASE_URL**  
   - Raw sources: `MODAL_OLLAMA_ENDPOINT` or `OLLAMA_BASE_URL` env var
   - Fallback (Render): `http://vecinita-model-ms-render:8000`
   - Fallback (local dev): defaults to raw URL

### Services Using Unified Configuration

Both services import the normalized endpoints from `config.py`:

**Agent (`src/agent/main.py`)**
```python
from src.config import EMBEDDING_SERVICE_URL, OLLAMA_BASE_URL, _running_on_render
```

**Gateway (`src/api/main.py`)**
```python
from src.config import EMBEDDING_SERVICE_URL, OLLAMA_BASE_URL
```

This ensures:
- ✅ Both services resolve the same endpoint for a given environment
- ✅ No duplicate normalization logic
- ✅ Single point of maintenance for routing rules

## Render Deployment Routing

### Modal Routing Architecture

On Render, the `vecinita-direct-routing` private service acts as a **unified ingress** for all upstream Model/Embedding traffic:

```
┌─────────────────────────────────────────────────────┐
│ Render Environment (Virginia)                        │
├─────────────────────────────────────────────────────┤
│                                                       │
│  ┌──────────────┐          ┌──────────────────────┐ │
│  │ Agent        │          │ Gateway              │ │
│  │ (port 10000) │ ─────┐   │ (port 10000)         │ │
│  └──────────────┘      │   └──────────────────────┘ │
│                        │                             │
│                        │   ┌──────────────────────┐ │
│                        │   │ Data Management API  │ │
│                        │   │ (port 8000, private) │ │
│                        │   └──────────────────────┘ │
│                        │                             │
│                        ▼                             │
│            ┌──────────────────────────┐             │
│            │ vecinita-direct-routing     │             │
│            │ (private service)        │             │
│            │ - /model     → Ollama    │             │
│            │ - /embedding → Embedding │             │
│            └──────────────────────────┘             │
│                        │                             │
│                        │ (via Modal)                │
│                        ├──────────────────────┐     │
│                        │                      │     │
│                   ┌────▼────┐          ┌─────▼──┐  │
│                   │ Ollama   │          │Embedding│ │
│                   │(via Modal)       │(via Modal)│  │
│                   └──────────┘          └──────────┘ │
│                                                       │
└─────────────────────────────────────────────────────┘
```

### Environment Variables in `render.yaml`

Both **agent** and **gateway** services should have async-configured endpoints:

```yaml
services:
  - type: web
    name: vecinita-agent
    envVars:
      - key: EMBEDDING_SERVICE_URL
        sync: false
      - key: OLLAMA_BASE_URL
        sync: false
      # ... remaining vars
      
  - type: web
    name: vecinita-gateway
    envVars:
      - key: EMBEDDING_SERVICE_URL
        sync: false
      - key: OLLAMA_BASE_URL
        sync: false
      # ... remaining vars
```

**Setting URLs in Render Dashboard:**
1. Goal: Agent and Gateway should have **identical** `EMBEDDING_SERVICE_URL` and `OLLAMA_BASE_URL` values
2. Standard production values:
   - `EMBEDDING_SERVICE_URL = http://vecinita-embedding-ms-render:8011`
   - `OLLAMA_BASE_URL = http://vecinita-model-ms-render:8000`

## Local Development Routing

### Docker Compose Stack

In local development, services can reference each other by container hostname:

```yaml
services:
  agent:
    environment:
      - EMBEDDING_SERVICE_URL=http://embedding-service:8001
      - OLLAMA_BASE_URL=http://vecinita-model-ms-render:8000
  
  gateway:
    environment:
      - EMBEDDING_SERVICE_URL=http://embedding-service:8001
      - OLLAMA_BASE_URL=http://vecinita-model-ms-render:8000
```

The `_normalize_internal_service_url()` function recognizes local hostnames and preserves them:
- `localhost`, `127.0.0.1`, `embedding-service`, `vecinita-direct-routing-v1` are all valid

## Troubleshooting Connectivity Issues

### Both Services Must See the Same Embedding Service

**Symptom:** Agent can query embeddings, but gateway returns 404 or timeout.

**Root Cause:** `EMBEDDING_SERVICE_URL` is not synchronized.

**Fix:**
1. Check `src/config.py` to verify the normalization logic is being used
2. Verify both services have the same `EMBEDDING_SERVICE_URL` env var on Render
3. If on Render, ensure both use the routing: `http://vecinita-embedding-ms-render:8011`

### Connection Refused Errors on Render

**Symptom:** `[Errno 111] Connection refused` when connecting to embedding/Ollama.

**Root Cause:** Env vars point to localhost or Docker-internal hostnames instead of the routing.

**Fix:**
1. On Render, `_running_on_render()` detects the env and forces routing routing
2. Ensure `MODAL_EMBEDDING_ENDPOINT` or `EMBEDDING_SERVICE_URL` is set to a non-local URL
3. If  using fallback, ensure it includes the routing path prefix (e.g., `/embedding`)

### Local Dev Prefers Non-Routing Endpoints

**Symptom:** Local agent/gateway reach remote Modal endpoints instead of local embeddings.

**Root Cause:** `MODAL_EMBEDDING_ENDPOINT` env var still points to production Modal app.

**Fix:**
1. In local dev, `_running_on_render()` returns False
2. `_normalize_internal_service_url()` trusts the raw URL if provided
3. Either unset `MODAL_EMBEDDING_ENDPOINT` or ensure it points to `http://localhost:8001` or `http://embedding-service:8001`

## Code Examples

### Agent Startup

```python
# src/agent/main.py
from src.config import EMBEDDING_SERVICE_URL, OLLAMA_BASE_URL

embedding_service_url = EMBEDDING_SERVICE_URL
embedding_model = create_embedding_client(
    embedding_service_url,
    validate_on_init=True,
)
logger.info("Embedding Service: %s", embedding_service_url)

llm_client_manager = LocalLLMClientManager(
    base_url=OLLAMA_BASE_URL,
    default_model=ollama_model,
    # ...
)
logger.info("Ollama Base URL: %s", OLLAMA_BASE_URL)
```

### Gateway Health Check

```python
# src/api/main.py
from src.config import EMBEDDING_SERVICE_URL, OLLAMA_BASE_URL

def lifespan(app: FastAPI):
    print(f"[Gateway] Embedding Service: {EMBEDDING_SERVICE_URL}")
    print(f"[Gateway] Ollama Base URL: {OLLAMA_BASE_URL}")
    yield
```

## Maintenance Notes

**If you need to change endpoint routing logic:**
1. Edit `src/config.py` → `_normalize_internal_service_url()`
2. Both agent and gateway will automatically pick up the new logic
3. No changes needed in `src/agent/main.py` or `src/api/main.py` (they just import)

**If you need to add a new internal service:**
1. Add a new configuration constant in `src/config.py` using `_normalize_internal_service_url()`
2. Import it in agent and gateway
3. Update `render.yaml` to include the new env var with `sync: false`
