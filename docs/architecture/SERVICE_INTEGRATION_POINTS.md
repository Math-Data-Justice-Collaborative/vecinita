# Service Integration Points

Last updated: March 31, 2026

This document summarizes runtime integration points across Vecinita services, including transport, routing, auth, and configuration controls.

## 1. Canonical Service Topology

### Chat stack (this repo)
- Frontend (`frontend`) calls Gateway (`backend/src/api/main.py`) over HTTP.
- Gateway proxies Q&A requests to Agent (`backend/src/agent/main.py`) over HTTP.
- Gateway and Agent call Embedding and Model routes through Modal Proxy when configured.
- Agent/Gateway/Scraper read and write vector/document data via `DATABASE_URL` (Render Postgres target).
- Supabase remains active for auth/session/role/storage flows where applicable.

### Multi-repo deployment mapping
- Chat Frontend: `joseph-c-mcguire/Vecinitafrontend` (Render frontend)
- Data Management Frontend: `Math-Data-Justice-Collaborative/vecinita-data-management-frontend` (Render frontend)
- Data Management API: `Math-Data-Justice-Collaborative/vecinita-data-management` (Render private service)
- Modal Proxy: `Math-Data-Justice-Collaborative/vecinita-modal-proxy` (Render private service)
- Scraper: `Math-Data-Justice-Collaborative/vecinita-scraper` (Modal)
- Embedding: `Math-Data-Justice-Collaborative/vecinita-embedding` (Modal)
- Model: `Math-Data-Justice-Collaborative/vecinita-model` (Modal)

## 2. Integration Matrix

| Caller | Callee | Interface | Key Config | Auth/Security |
|---|---|---|---|---|
| Frontend | Gateway | HTTP REST + SSE (`/api/v1/ask`, `/api/v1/ask/stream`) | `VITE_GATEWAY_URL`, `VITE_BACKEND_URL` | Gateway middleware API-key model; public docs endpoints allowed |
| Frontend | Supabase Auth | Supabase JS SDK | `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY` | JWT/session managed by Supabase |
| Gateway | Agent | HTTP (`/ask`, `/ask-stream`, `/config`) | `AGENT_SERVICE_URL`, `AGENT_TIMEOUT`, `AGENT_STREAM_TIMEOUT` | Internal service-to-service |
| Gateway | Embedding endpoint | HTTP (`/embed`, `/embed/batch`) | `EMBEDDING_SERVICE_URL`, `MODAL_EMBEDDING_ENDPOINT` | `x-embedding-service-token`/Bearer and optional Modal headers |
| Gateway | Scraper/Reindex route | HTTP (`/jobs`) via proxy URL | `REINDEX_SERVICE_URL`, `REINDEX_TRIGGER_TOKEN` | Trigger token-based gate |
| Agent | Embedding endpoint | HTTP (query/document embeddings) | `EMBEDDING_SERVICE_URL`, `MODAL_EMBEDDING_ENDPOINT` | Same token/header pattern as gateway |
| Agent | Model endpoint | HTTP via Ollama-compatible API | `OLLAMA_BASE_URL`, `MODAL_OLLAMA_ENDPOINT` | Proxy path: omit modal creds from client side; proxy injects |
| Agent tools | Postgres vector DB | SQL (`document_chunks`, similarity query) | `DATABASE_URL`, `DB_DATA_MODE`, `POSTGRES_DATA_READS_ENABLED` | DB network + credentials |
| Agent tools (fallback) | Supabase RPC | PostgREST/RPC (`search_similar_documents`) | `SUPABASE_URL`, `SUPABASE_KEY`, `VECTOR_SYNC_SUPABASE_FALLBACK_READS` | Supabase service key |
| Scraper uploader | Chroma | HTTP client (`upsert_chunks`) | `CHROMA_HOST`, `CHROMA_PORT`, collections | Internal network |
| Scraper uploader | Postgres or Supabase sync target | SQL or Supabase upsert | `VECTOR_SYNC_TARGET`, `DATABASE_URL`, `VECTOR_SYNC_*` | DB credentials or Supabase key |
| Documents router | Postgres + Supabase | SQL for corpus stats + Supabase storage URL | `DATABASE_URL`, `SUPABASE_URL`, `SUPABASE_*` | Mixed data-source read path |
| Modal Proxy | Modal backends (model/embedding/scraper) | Pass-through HTTP with route stripping | `VECINITA_MODEL_API_URL`, `VECINITA_EMBEDDING_API_URL`, `VECINITA_SCRAPER_API_URL` | Injects `Modal-Key`/`Modal-Secret`; strips inbound credential headers |

## 3. Primary Runtime Flows

### 3.1 Chat request flow
1. Frontend calls Gateway endpoint `/api/v1/ask` or `/api/v1/ask/stream`.
2. Gateway forwards to Agent service URL.
3. Agent performs retrieval (Chroma primary, DB fallback path per mode/flags).
4. Agent calls model endpoint (typically through Modal Proxy).
5. Gateway returns normalized response to frontend.

### 3.2 Embedding flow
1. Gateway/Agent use embedding client wrappers.
2. If endpoint is modal-proxy route, proxy-level headers/tokens are used.
3. Embedding service returns vectors (single or batch).

### 3.3 Scrape + ingest flow
1. Scrape job accepted at Gateway scraper router.
2. Scraper extracts/segments content and invokes uploader.
3. Uploader writes to Chroma and sync target (`VECTOR_SYNC_TARGET=postgres` in cutover envs).
4. Loader/uploader can write `document_chunks`/`processing_queue` directly with Postgres mode.

## 4. Environment-Specific Wiring

### Render
- Render blueprints define service URLs and private-network links:
  - `render.yaml`
  - `render.staging.yaml`
- Agent is configured for data path cutover:
  - `DB_DATA_MODE=postgres`
  - `VECTOR_SYNC_TARGET=postgres`
  - `VECTOR_SYNC_SUPABASE_FALLBACK_READS=false`

### Local Compose
- `docker-compose.yml` and `docker-compose.dev.yml` run full local stack.
- PostgREST is used for local Supabase-like REST access.
- Chroma, Postgres, Agent, Gateway, Frontend are connected by bridge network.

### Microservices Compose
- `docker-compose.microservices.yml` runs modal-proxy-centric local simulation.
- Model/embedding/scraper backends are individually wired to proxy route prefixes.

## 5. Auth and Secret Boundaries

- Frontend should only receive public Supabase anon credentials.
- Gateway auth middleware enforces API key model for protected endpoints.
- Modal Proxy strips any inbound Modal credential headers and injects server-side credentials.
- Embedding/model requests can require proxy token and/or service token headers.
- Production secrets are expected in Render dashboard (not committed files).

## 6. Current Split of Responsibility

### Supabase (active)
- Authentication and session lifecycle.
- Role/admin metadata paths still tied to Supabase.
- Storage/public object URL construction for uploaded docs in some routes.

### Render Postgres (target data path)
- Canonical vector/document retrieval and ingestion data (`document_chunks`, `processing_queue`).
- `DATABASE_URL`-based read/write path in agent tools and loader/uploader.

### Transitional components
- Chroma remains active in current runtime for primary retrieval in several paths, with DB fallback.
- Some legacy docs still describe Supabase as vector backend and should be treated as historical unless updated.

## 7. Key Integration Files

### Deployment wiring
- `render.yaml`
- `render.staging.yaml`
- `docker-compose.yml`
- `docker-compose.dev.yml`
- `docker-compose.microservices.yml`

### Frontend integration
- `frontend/src/app/services/agentService.ts`
- `frontend/src/lib/supabase.ts`

### Gateway integration
- `backend/src/api/main.py`
- `backend/src/api/router_ask.py`
- `backend/src/api/router_embed.py`
- `backend/src/api/router_scrape.py`
- `backend/src/api/router_documents.py`

### Agent/data integration
- `backend/src/config.py`
- `backend/src/agent/tools/db_search.py`
- `backend/src/services/scraper/uploader.py`
- `backend/src/agent/utils/vector_loader.py`

### Proxy integration
- `services/modal-proxy/app/config.py`
- `services/modal-proxy/app/backends/defaults.py`
- `services/modal-proxy/app/proxy.py`
- `services/modal-proxy/app/middleware.py`
- `services/modal-proxy/BACKEND_API_SPECIFICATION.md`

## 8. Integration Risks to Watch

1. Config drift between local compose and Render blueprints (different defaults can hide regressions).
2. Mixed Chroma + Postgres behavior during cutover can produce inconsistent retrieval behavior.
3. Legacy Supabase vector assumptions in old docs can mislead operators.
4. Proxy/header misconfiguration can yield 401s for Modal-backed model/embedding routes.
5. Partial migration in dependent repos (data-management, modal services) can break cross-repo flows if env contracts diverge.

## 9. Recommended Operational Checks

- Verify startup preflight logs include expected `data_mode` and backend health detail.
- Verify gateway `/health` and proxy `/health` plus upstream probes before rollout.
- Validate one end-to-end ask-stream call and one scrape/upload flow per environment.
- Track retrieval backend metrics during transition windows.
