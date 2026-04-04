# Service Connectivity Unification - Change Summary

## Problem

The **agent** (`src/agent/main.py`) and **gateway** (`src/api/main.py`) services had **different endpoint resolution logic** for internal services (embedding, Ollama), causing inconsistency when routing to Modal routing on Render deployments.

### Specific Issues

1. **Duplicate normalization code**: Both services implemented `_normalize_internal_service_url()` with identical logic
2. **Inconsistent configuration**: Agent used one set of normalization rules; gateway used different rules
3. **No single source of truth**: Endpoint resolution scattered across multiple modules
4. **Render configuration gaps**: Neither agent nor gateway had explicit `EMBEDDING_SERVICE_URL` and `OLLAMA_BASE_URL` in render.yaml

### Symptom

Both services could end up with different endpoint URLs in the same Render deployment, causing one to fail while the other succeeds:
- Agent successfully reaches embedding service via Modal routing
- Gateway fails to reach same service due to stale direct Modal URL

## Solution: Unified Configuration

### 1. Centralized Endpoint Resolution ✅

**File: `src/config.py`**
- Moved `_normalize_internal_service_url()` and `_running_on_render()` to central config
- Single source of truth for endpoint resolution logic
- Handles Render vs local-dev routing in one place

```python
def _normalize_internal_service_url(raw_url: str | None, *, fallback_url: str) -> str:
    """Resolve effective URL for internal upstream services."""
    # On Render: force routing routing for non-local URLs
    # Off Render: trust raw URLs with sensible fallback
```

### 2. Normalized Configuration Constants ✅

**File: `src/config.py`**
- `EMBEDDING_SERVICE_URL` — normalized via `_normalize_internal_service_url()`
- `OLLAMA_BASE_URL` — normalized via `_normalize_internal_service_url()`

Both use the same routing logic and fallback to Modal routing on Render.

### 3. Agent & Gateway Import from Central Config ✅

**File: `src/agent/main.py`**
```python
from src.config import EMBEDDING_SERVICE_URL, OLLAMA_BASE_URL, _running_on_render
```

**File: `src/api/main.py`**
```python
from src.config import EMBEDDING_SERVICE_URL, OLLAMA_BASE_URL
```

Removed duplicate functions and local calculations. Both now use identical endpoints.

### 4. Render Manifest Updated ✅

**Files: `render.yaml`, `render.staging.yaml`**
- Added explicit `EMBEDDING_SERVICE_URL` (sync: false) to both agent and gateway
- Added explicit `OLLAMA_BASE_URL` (sync: false) to both agent and gateway
- Now clear in manifest that both services need to be synchronized

## Changes Made

### Code Changes

| File | Change |
|---|---|
| `src/config.py` | Added `_running_on_render()` and `_normalize_internal_service_url()` |
| `src/config.py` | Refactored endpoint constants to use normalization |
| `src/agent/main.py` | Removed duplicate functions, import from config |
| `src/agent/main.py` | Use `EMBEDDING_SERVICE_URL` and `OLLAMA_BASE_URL` from config |
| `src/api/main.py` | Removed `_normalize_embedding_service_url()` |
| `src/api/main.py` | Import `EMBEDDING_SERVICE_URL` and `OLLAMA_BASE_URL` from config |
| `render.yaml` | Added `EMBEDDING_SERVICE_URL` and `OLLAMA_BASE_URL` env vars to agent & gateway |
| `render.staging.yaml` | Added `EMBEDDING_SERVICE_URL` and `OLLAMA_BASE_URL` env vars to agent-staging & gateway-staging |

### Documentation

| File | Purpose |
|---|---|
| `docs/deployment/SERVICE_CONNECTIVITY.md` | Complete guide to unified endpoint routing, Render routing architecture, local dev setup, troubleshooting |

## Behavior After Fix

### Local Development
- Agent and Gateway import `EMBEDDING_SERVICE_URL` from `src/config.py`
- Both use same endpoint (typically Docker hostname or localhost)
- No hardcoded fallbacks override each other

### Render Deployment
- Both services must have identical `EMBEDDING_SERVICE_URL` and `OLLAMA_BASE_URL` set in Render dashboard
- Recommended values:
  - `EMBEDDING_SERVICE_URL = http://vecinita-embedding-ms-render:8011`
  - `OLLAMA_BASE_URL = http://vecinita-model-ms-render:8000`
- If raw URLs point anywhere (localhost, Docker hostname), normalization forces both to use routing
- Both services route through SAME routing, preventing connection mismatches

## Testing

### ✅ Verified

```
[Test 1] Configuration imports
  ✅ EMBEDDING_SERVICE_URL: http://vecinita-embedding-ms-render:8011
  ✅ OLLAMA_BASE_URL: http://localhost:11434
  ✅ Running on Render: False

[Test 2] Normalization logic (all scenarios)
  ✅ Local dev (raw=localhost): preserves http://localhost:8001
  ✅ Local dev (raw=remote): preserves https://some-modal-app.modal.run/embedding
  ✅ Render (raw=localhost): forces http://vecinita-embedding-ms-render:8011
  ✅ Render (raw=remote): allows https://some-modal-app.modal.run/embedding

[Test 3] Both services compile
  ✅ src/config.py
  ✅ src/agent/main.py
  ✅ src/api/main.py
```

## Next Steps

### For Render Deployment
1. Navigate to Render dashboard for `vecinita-agent` service
2. Ensure env vars are configured:
   - `EMBEDDING_SERVICE_URL = http://vecinita-embedding-ms-render:8011`
   - `OLLAMA_BASE_URL = http://vecinita-model-ms-render:8000`
3. Repeat for `vecinita-gateway` service
4. Repeat for staging services if present

### For Local Development
- No action required if your `.env` or docker-compose already sets `EMBEDDING_SERVICE_URL`
- If unset, defaults from config will be used:
  - Non-Render: falls back to provided URL or local candidate
  - Container services: use docker hostnames (e.g., `embedding-service:8001`)

## Impact

**Zero breaking changes:** Both services now consistently resolve endpoints, eliminating the class of errors where one service succeeds and the other fails with connection/404 errors.
