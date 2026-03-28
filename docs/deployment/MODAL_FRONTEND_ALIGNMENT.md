# Modal & Frontend Alignment Verification

## Overview

This document verifies that backend Modal services are properly aligned with frontend API expectations.

## Architecture Overview

```
Frontend (React) @ port 5173
    ↓ (http://localhost:8004/api/v1)
API Gateway (FastAPI) @ port 8004
    ├──→ /ask/config → Agent Service @ 8000 (LLMs)
    ├──→ /ask, /ask/stream → Agent Service @ 8000 (Q&A)
    ├──→ /embed/* → Modal Embedding Service
    │       (or http://localhost:8001 for local dev)
    ├──→ /scrape/* → Scraper + Backend DB
    │       (/reindex → Modal Scraper Service)
    └──→ /documents/* → Chroma/DB

Modal Services (Serverless):
├── Embedding Service (ASGI)
│   └── Port: 443 (https://...)
│   └── Endpoints: /embed, /batch, /config, /health
│   └── Auth: MODAL_API_PROXY_SECRET or EMBEDDING_SERVICE_AUTH_TOKEN
│
└── Scraper Service (ASGI + Cron)
    ├── Port: 443 (https://...)
    ├── HTTP Endpoints: /health, /reindex
    ├── Scheduled Job: weekly_reindex() 
    └── Auth: REINDEX_TRIGGER_TOKEN (x-reindex-token header)
```

## Frontend → API Gateway Endpoints

The frontend (React) communicates via `AgentServiceClient` and `ModelRegistry`:

### From `frontend/src/app/services/agentService.ts`

| Endpoint | Method | Purpose | Query Params |
|----------|--------|---------|--------------|
| `/ask` | GET | Non-streaming Q&A | `question`, `thread_id`, `lang`, `provider`, `model` |
| `/ask/stream` | GET | Streaming Q&A (SSE) | Same as above |
| `/ask/config` | GET | Fetch available LLMs | - |
| `/health` | GET | Health check | - |

### From `frontend/src/app/services/modelRegistry.ts`

| Endpoint | Method | Purpose | Response |
|----------|--------|---------|----------|
| `/ask/config` | GET | LLM providers list | `{ providers: [...], models: {...} }` |
| `/embed/config` | GET | Embedding providers | `{ current, available }` |

### Response Types Expected

```typescript
// Ask Config Response
{
  providers: Array<{ key: string; label: string }>,
  models: Record<string, string[]>
}

// Embed Config Response
{
  current?: { provider?: string; model?: string },
  available?: {
    providers?: Array<{ key: string; label: string }>,
    models?: Record<string, string[]>
  }
}
```

## API Gateway → Backend Services

The API Gateway (`backend/src/api/main.py`) routes to backend services:

| Frontend Request | Gateway Route | Backend Service | Modal Service |
|------------------|---------------|-----------------|---|
| `/api/v1/ask?question=...` | `/ask` (router_ask.py) | Agent @ 8000 | N/A |
| `/api/v1/ask/stream?...` | `/ask/stream` (router_ask.py) | Agent @ 8000 | N/A |
| `/api/v1/ask/config` | `/ask/config` (router_ask.py) | Agent @ 8000 (fallback) | N/A |
| `/api/v1/embed/...` | `/embed/*` (router_embed.py) | Modal/Local @ :8001 | YES |
| `/api/v1/embed/config` | `/embed/config` (router_embed.py) | Modal/Local @ :8001 | YES |
| `/api/v1/scrape/...` | `/scrape/*` (router_scrape.py) | Backend scraper | /reindex → Modal |
| `/api/v1/documents/...` | `/documents/*` (router_documents.py) | Backend/DB | N/A |

## Embedding Service Alignment

### Backend Embedding Service Endpoints

**File**: `backend/src/embedding_service/main.py`

| Endpoint | Method | Input | Output |
|----------|--------|-------|--------|
| `/embed` | POST | `{ text: str }` | `{ embedding: float[], dimension: int, model: str }` |
| `/batch` | POST | `{ texts: str[] }` | `{ embeddings: float[][], dimension: int, count: int, model: str }` |
| `/similarity` | POST | `{ texts: str[], query: str }` | `{ scores: float[], similarities: {...} }` |
| `/config` | GET | - | `{ model: str, provider: str, dimension: int, description: str }` |
| `/health` | GET | - | `{ status: string, service: string }` |

### API Gateway Proxying

**File**: `backend/src/api/router_embed.py`

The gateway proxies requests to embedding service with:
- Auth token injection (from environment):
  1. `EMBEDDING_SERVICE_AUTH_TOKEN` (explicit)
  2. `MODAL_API_PROXY_SECRET` (Modal proxy)
  3. `MODAL_API_KEY` (fallback)
  4. `MODAL_API_TOKEN_SECRET` (final fallback)

- URL resolution order:
  1. `MODAL_EMBEDDING_ENDPOINT` (Modal-hosted)
  2. `EMBEDDING_SERVICE_URL` (fallback)
  3. `http://localhost:8001` (default local)

## Scraper Service Alignment

### Backend Scraper Service

**File**: `backend/src/scraper/modal_app.py`

| Function | Type | Purpose | Schedule |
|----------|------|---------|----------|
| `run_reindex()` | Modal function | Manual reindex trigger | On-demand |
| `weekly_reindex()` | Modal cron job | Scheduled scraping | Default: Sundays 2 AM UTC |
| `web_app()` | Modal ASGI app | HTTP endpoints | Always running |

### HTTP Endpoints

| Endpoint | Method | Headers | Response |
|----------|--------|---------|----------|
| `/health` | GET | - | `{ status: "ok", service: "scraper-reindex", schedule: "..." }` |
| `/reindex` | POST | `x-reindex-token` | `{ status: "queued", call_id: string }` |

### API Gateway Integration

**File**: `backend/src/api/router_scrape.py`

Triggers reindex via HTTP POST to `REINDEX_SERVICE_URL/reindex` with:
- Header: `x-reindex-token: ${REINDEX_TRIGGER_TOKEN}`
- Query params: `clean`, `stream`, `verbose`

## Environment Variable Configuration

### Precedence & Resolution

```
EMBEDDING_SERVICE_URL Resolution:
  MODAL_EMBEDDING_ENDPOINT (1st priority)
    ↓
  EMBEDDING_SERVICE_URL
    ↓
  http://localhost:8001 (default)

EMBEDDING_SERVICE_AUTH_TOKEN Resolution:
  EMBEDDING_SERVICE_AUTH_TOKEN (1st priority)
    ↓
  MODAL_API_PROXY_SECRET
    ↓
  MODAL_API_KEY
    ↓
  MODAL_API_TOKEN_SECRET (final fallback)

REINDEX_SERVICE_URL Resolution:
  REINDEX_SERVICE_URL (set explicitly)
    ↓
  Fallback to no reindex (optional feature)
```

## Verification Checklist

### ✅ Frontend Expectations Met

- [x] **Ask Endpoints**: `/ask` and `/ask/stream` proxied to Agent Service
- [x] **Config Endpoints**: `/ask/config` and `/embed/config` return proper structure
- [x] **Embedding Service**: Properly integrated with auth headers and precedence
- [x] **Error Handling**: Fallback configs when services unavailable

### ✅ Backend Modal Functions

- [x] **Embedding Service Modal App**: 
  - Location: `backend/src/embedding_service/modal_app.py`
  - Exports: `web_app()` ASGI entrypoint, `health()` function
  - Image: debian_slim + fastapi + uvicorn + sentence-transformers
  - Auth: Supports EMBEDDING_SERVICE_AUTH_TOKEN

- [x] **Scraper Service Modal App**:
  - Location: `backend/src/scraper/modal_app.py`
  - Exports: `run_reindex()`, `weekly_reindex()`, `web_app()` ASGI
  - Cron: Default schedule `0 2 * * 0` (weekly)
  - Auth: REINDEX_TRIGGER_TOKEN header validation

### ✅ CI/CD Setup

- [x] **GitHub Actions Workflow**: `.github/workflows/modal-deploy.yml`
- [x] **Deployment Triggers**: Push to main, manual dispatch
- [x] **Secrets**: `MODAL_TOKEN_ID`, `MODAL_TOKEN_SECRET`
- [x] **Deploy Script**: `backend/scripts/deploy_modal.sh`

### ✅ Documentation

- [x] **Modal Deployment Guide**: `docs/deployment/MODAL_DEPLOYMENT.md`
- [x] **.env.example**: Updated with Modal config guidance
- [x] **GitHub Secrets Instructions**: Documented in workflow
- [x] **Troubleshooting**: Included in deployment guide

## Known Issues & Deprecated Code

### ⚠️ Deprecated: `backend/src/services/embedding/modal_app.py`

**Status**: Deprecated, not deployed

**Reason**: 
- References non-existent `src.services.embedding.server:app`
- Not tested or imported anywhere
- Use `backend/src/embedding_service/modal_app.py` instead

**Action**: Keep for backwards compatibility, but do not deploy

## Testing Alignment

### Local Development

```bash
# Start embedding service locally (no Modal needed)
python -m uvicorn src.embedding_service.main:app --reload --port 8001

# Start gateway
python -m uvicorn src.api.main:app --reload --port 8004

# Test embedding endpoint
curl -X POST http://localhost:8004/api/v1/embed \
  -H "Content-Type: application/json" \
  -d '{"text": "hello world"}'

# Test config endpoints
curl http://localhost:8004/api/v1/ask/config
curl http://localhost:8004/api/v1/embed/config
```

### CI/CD Testing

```bash
# Manual deployment trigger
gh workflow run modal-deploy.yml \
  -f deploy_embedding=true \
  -f deploy_scraper=true

# Check deployment status
modal app list --all
modal app logs vecinita-embedding
modal app logs vecinita-scraper
```

## Additional Resources

- [Modal Documentation](https://modal.com/docs)
- [Modal Deployment Guide](./MODAL_DEPLOYMENT.md)
- [Backend API Documentation](../backend/src/api/README.md)
- [Embedding Service README](../backend/src/embedding_service/README.md)
