# Vecinita Environment Reference

> Auto-generated environment documentation. Last updated: 2026-05-11.

## Overview

| Metric | Count |
|--------|-------|
| Total env files scanned | 10 |
| Total unique variables | ~95 |
| Services documented | 10 |
| Deployment targets | local, render-prod, render-staging, modal, ci |

## Env file hierarchy

| Layer | File | Purpose |
|-------|------|---------|
| Canonical | `config/.env.example` | Full catalog, all profiles |
| Local pointer | `.env.local.example` | Quick-start instructions |
| Render prod | `config/.env.prod.render.example` | Production secrets template |
| Render staging | `config/.env.staging.render.example` | Staging parity template |
| Per-service | `apis/gateway/.env.example` | Backend-only overrides |
| Per-service | `frontends/chat/.env.example` | Chat frontend VITE_* vars |
| Per-service | `frontends/data-management/.env.example` | DM frontend VITE_* vars |
| Per-service | `modal-apps/scraper/.env.example` | Scraper Supabase + Modal + crawl config |
| Per-service | `modal-apps/model-modal/.env.example` | Model Modal auth + Ollama |
| Per-service | `tests/.env.example` | Test URLs and flags |

## Per-service environment

### Agent (`apis/agent/`)

**Deploy target:** Render (`vecinita-agent`)

| Variable | Required | Default | Scope | Sensitive | Profile |
|----------|----------|---------|-------|-----------|---------|
| DATABASE_URL | Yes | postgresql://…localhost:5432/postgres | all | Yes | required |
| DB_DATA_MODE | No | postgres | render-prod | No | data-db-routing |
| DEFAULT_MODEL | No | gemma3 | all | No | embedding-and-local-models |
| DEFAULT_PROVIDER | No | ollama | all | No | embedding-and-local-models |
| DEEPSEEK_API_KEY | No | (empty) | all | Yes | alternate-llm-providers |
| DEEPSEEK_BASE_URL | No | https://api.deepseek.com | all | No | alternate-llm-providers |
| EMBEDDING_SERVICE_AUTH_TOKEN | Yes | (empty) | all | Yes | modal-runtime |
| EMBEDDING_STRICT_STARTUP | No | (empty) | render-prod | No | runtime-flags |
| EMBEDDING_UPSTREAM_URL | Yes | http://localhost:8001 | all | No | service-wiring |
| FORCE_LOCAL_MODAL_LLM | No | true | render-prod | No | embedding-and-local-models |
| GROQ_API_KEY | No | (empty) | all | Yes | alternate-llm-providers |
| GUARDRAILS_HUB_AUTO_INSTALL | No | false | all | No | runtime-flags |
| GUARDRAILS_PERSISTENCE_DIR | No | (empty) | render-prod | No | runtime-flags |
| GUARDRAILS_REQUIRE_HUB_VALIDATOR | No | false | all | No | runtime-flags |
| LANGSMITH_API_KEY | No | (empty) | all | Yes | langsmith-tracing |
| LANGSMITH_PROJECT | No | vecinita | all | No | langsmith-tracing |
| LOCK_MODEL_SELECTION | No | true | render-prod | No | embedding-and-local-models |
| MODAL_FUNCTION_INVOCATION | No | auto | all | No | modal-runtime |
| MODAL_TOKEN_ID | Yes (if Modal) | (empty) | all | Yes | modal-runtime |
| MODAL_TOKEN_SECRET | Yes (if Modal) | (empty) | all | Yes | modal-runtime |
| OLLAMA_BASE_URL | No | http://localhost:11434 | all | No | embedding-and-local-models |
| OLLAMA_MODEL | No | gemma3 | all | No | embedding-and-local-models |
| OPENAI_API_KEY | No | (empty) | all | Yes | alternate-llm-providers |
| PORT | Yes | 10000 | render | No | required |
| PYTHONUNBUFFERED | No | 1 | render | No | runtime-flags |
| RENDER_DISABLE_LOCAL_GUARDRAILS | No | true | render-prod | No | runtime-flags |
| RENDER_REMOTE_INFERENCE_ONLY | No | true | render-prod | No | runtime-flags |
| TAVILY_API_KEY | No | (empty) | all | Yes | alternate-llm-providers |
| VECTOR_SYNC_TARGET | No | postgres | render-prod | No | data-db-routing |

**Render `envVars` (from render.yaml):**

| Key | Source | sync |
|-----|--------|------|
| PORT | inline: "10000" | n/a |
| DATABASE_URL | fromDatabase: vecinita-postgres | n/a |
| DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD | fromDatabase | n/a |
| PGHOST/PGPORT/PGDATABASE/PGUSER/PGPASSWORD | fromDatabase | n/a |
| All other vars | env group | false |

---

### Gateway (`apis/gateway/`)

**Deploy target:** Render (`vecinita-gateway`)

| Variable | Required | Default | Scope | Sensitive | Profile |
|----------|----------|---------|-------|-----------|---------|
| AGENT_SERVICE_URL | Yes (Render: fromService) | http://localhost:8000 | all | No | local-chat-and-gateway-tuning |
| AGENT_STREAM_TIMEOUT | No | 180 | all | No | local-chat-and-gateway-tuning |
| AGENT_TIMEOUT | No | 180 | all | No | local-chat-and-gateway-tuning |
| ALLOWED_ORIGINS | No | (empty) | render-prod | No | required |
| ALLOWED_ORIGIN_REGEX | No | (empty) | render-prod | No | required |
| DATABASE_URL | Yes | postgresql://…localhost:5432/postgres | all | Yes | required |
| DEEPSEEK_API_KEY | No | (empty) | all | Yes | alternate-llm-providers |
| DEEPSEEK_BASE_URL | No | https://api.deepseek.com | all | No | alternate-llm-providers |
| DEV_ADMIN_BEARER_TOKEN | Conditional | (empty) | local/dev | Yes | gateway-admin |
| DEV_ADMIN_ENABLED | No | true (local) | local | No | gateway-admin |
| EMBEDDING_SERVICE_AUTH_TOKEN | Yes | (empty) | all | Yes | modal-runtime |
| EMBEDDING_UPSTREAM_URL | Yes | http://localhost:8001 | all | No | service-wiring |
| ENABLE_LLM_TAG_ENHANCEMENT | No | true | all | No | service-wiring |
| GATEWAY_PORT | No | 8004 | local | No | gateway-admin |
| GROQ_API_KEY | No | (empty) | all | Yes | alternate-llm-providers |
| LLM_TAG_PROVIDER | No | auto | all | No | service-wiring |
| MODAL_FUNCTION_INVOCATION | No | auto | all | No | modal-runtime |
| MODAL_SCRAPER_PERSIST_VIA_GATEWAY | No | 1 | render-prod | No | service-wiring |
| MODAL_TOKEN_ID | Yes (if Modal) | (empty) | all | Yes | modal-runtime |
| MODAL_TOKEN_SECRET | Yes (if Modal) | (empty) | all | Yes | modal-runtime |
| OLLAMA_BASE_URL | No | http://localhost:11434 | all | No | embedding-and-local-models |
| OPENAI_API_KEY | No | (empty) | all | Yes | alternate-llm-providers |
| PORT | Yes | 10000 | render | No | required |
| SCRAPER_API_KEYS | Yes (prod) | (empty) | render-prod | Yes | service-wiring |
| SCRAPER_DEBUG_BYPASS_AUTH | No | false | render-prod | No | service-wiring |

**Render `envVars` (from render.yaml):**

| Key | Source | sync |
|-----|--------|------|
| PORT | inline: "10000" | n/a |
| AGENT_SERVICE_URL | fromService: vecinita-agent (hostport) | n/a |
| DATABASE_URL | fromDatabase: vecinita-postgres | n/a |
| DB_*/PG* | fromDatabase | n/a |
| MODAL_SCRAPER_PERSIST_VIA_GATEWAY | inline: "1" | n/a |
| All other vars | env group | false |

---

### Chat frontend (`frontends/chat/`)

**Deploy target:** Render (`vecinita-frontend`)

| Variable | Required | Default | Scope | Sensitive | Profile |
|----------|----------|---------|-------|-----------|---------|
| VITE_AGENT_REQUEST_TIMEOUT_MS | No | 90000 | all | No | local-chat-and-gateway-tuning |
| VITE_AGENT_STREAM_FIRST_EVENT_TIMEOUT_MS | No | 15000 | all | No | local-chat-and-gateway-tuning |
| VITE_AGENT_STREAM_TIMEOUT_MS | No | 120000 | all | No | local-chat-and-gateway-tuning |
| VITE_BACKEND_URL | Yes | http://localhost:8004/api/v1 | all | No | required |
| VITE_DEV_ADMIN_EMAIL | Conditional | (empty) | local/dev | No | gateway-admin |
| VITE_DEV_ADMIN_ENABLED | No | true (local) | local | No | gateway-admin |
| VITE_DEV_ADMIN_PASSWORD | Conditional | (empty) | local/dev | Yes | gateway-admin |
| VITE_DEV_ADMIN_TOKEN | Conditional | (empty) | local/dev | Yes | gateway-admin |
| VITE_GATEWAY_PROXY_TARGET | No | http://127.0.0.1:8004 | local | No | local-chat-and-gateway-tuning |
| VITE_GATEWAY_URL | Yes | /api (dev proxy) | all | No | required |

**Render `envVars` (from render.yaml):**

| Key | Source | sync |
|-----|--------|------|
| PORT | inline: "10000" | n/a |
| VITE_* | env group | false |

---

### DM frontend (`frontends/data-management/`)

**Deploy target:** Render (`vecinita-data-management-frontend-v1`)

| Variable | Required | Default | Scope | Sensitive | Profile |
|----------|----------|---------|-------|-----------|---------|
| VITE_DEFAULT_SCRAPER_USER_ID | No | frontend-user | all | No | local-chat-and-gateway-tuning |
| VITE_DM_API_BASE_URL | Yes | http://localhost:8005 | all | No | required |
| VITE_EMBEDDING_UPSTREAM_URL | No | (empty) | render-prod | No | service-wiring |
| VITE_OLLAMA_BASE_URL | No | (empty) | render-prod | No | service-wiring |

**Render `envVars` (from render.yaml):**

| Key | Source | sync |
|-----|--------|------|
| PORT | inline: "10000" | n/a |
| VITE_* | env group | false |

---

### Scraper (`modal-apps/scraper/`)

**Deploy targets:** Render (`vecinita-data-management-api-v1`) + Modal (`vecinita-scraper`)

| Variable | Required | Default | Scope | Sensitive | Profile |
|----------|----------|---------|-------|-----------|---------|
| CHUNK_MAX_SIZE_TOKENS | No | 1024 | modal | No | service-wiring |
| CHUNK_MIN_SIZE_TOKENS | No | 256 | modal | No | service-wiring |
| CHUNK_OVERLAP_RATIO | No | 0.2 | modal | No | service-wiring |
| CORS_ORIGINS | No | (empty) | render-prod | No | required |
| CRAWL4AI_MAX_DEPTH | No | 3 | modal | No | service-wiring |
| CRAWL4AI_TIMEOUT_SECONDS | No | 60 | modal | No | service-wiring |
| DATABASE_URL | Yes | (from Render) | render-prod | Yes | required |
| EMBEDDING_UPSTREAM_URL | Yes | (Modal URL) | all | No | service-wiring |
| ENVIRONMENT | No | development | all | No | runtime-flags |
| LOG_LEVEL | No | INFO | all | No | runtime-flags |
| MODAL_PROXY_AUTH_ENABLED | No | true | modal | No | modal-runtime |
| MODAL_TOKEN_ID | Yes | (empty) | all | Yes | modal-runtime |
| MODAL_TOKEN_SECRET | Yes | (empty) | all | Yes | modal-runtime |
| MODAL_WORKSPACE | Yes | your-workspace | all | No | modal-runtime |
| OLLAMA_BASE_URL | Yes | (Modal URL) | all | No | service-wiring |
| PORT | Yes | 10000 | render | No | required |
| SCRAPER_API_KEYS | Yes (prod) | (empty) | render-prod | Yes | service-wiring |
| SCRAPER_DEBUG_BYPASS_AUTH | No | false | render-prod | No | service-wiring |
| SUPABASE_ANON_KEY | Conditional | (empty) | modal | Yes | supabase-extended |
| SUPABASE_PROJECT_URL | Conditional | (empty) | modal | No | supabase-extended |
| SUPABASE_PUBLISHABLE_KEY | Conditional | (empty) | modal | Yes | supabase-extended |
| SUPABASE_SERVICE_KEY | Conditional | (empty) | modal | Yes | supabase-extended |
| UPSTREAM_TIMEOUT_SECONDS | No | 55 | render-prod | No | service-wiring |

**Modal secrets (`vecinita-scraper-env`):**
MODAL_TOKEN_ID, MODAL_TOKEN_SECRET, MODAL_WORKSPACE, MODAL_DATABASE_URL,
DATABASE_URL, SUPABASE_PROJECT_URL, SUPABASE_SERVICE_KEY,
EMBEDDING_UPSTREAM_URL, OLLAMA_BASE_URL, SCRAPER_API_KEYS

---

### Embedding (`modal-apps/embedding-modal/`)

**Deploy target:** Modal (`vecinita-embedding`)

| Variable | Required | Default | Scope | Sensitive | Profile |
|----------|----------|---------|-------|-----------|---------|
| MODAL_TOKEN_ID | Yes | (empty) | modal | Yes | modal-runtime |
| MODAL_TOKEN_SECRET | Yes | (empty) | modal | Yes | modal-runtime |

Minimal env surface — the embedding app relies on Modal Secrets for auth tokens and uses built-in fastembed with no external service calls.

---

### Model (`modal-apps/model-modal/`)

**Deploy target:** Modal (`vecinita-model`)

| Variable | Required | Default | Scope | Sensitive | Profile |
|----------|----------|---------|-------|-----------|---------|
| DEFAULT_MODEL | No | gemma3 | all | No | embedding-and-local-models |
| MODAL_TOKEN_ID | Yes | (empty) | modal | Yes | modal-runtime |
| MODAL_TOKEN_SECRET | Yes | (empty) | modal | Yes | modal-runtime |
| MODELS_PATH | No | /models | modal | No | embedding-and-local-models |
| OLLAMA_HOST | No | http://localhost:11434 | local | No | embedding-and-local-models |

---

### Tests (`tests/`)

**Deploy target:** CI

| Variable | Required | Default | Scope | Sensitive | Profile |
|----------|----------|---------|-------|-----------|---------|
| API_TIMEOUT | No | 10 | ci | No | testing |
| BACKEND_URL | No | http://localhost:8000 | ci | No | testing |
| E2E_TIMEOUT | No | 30 | ci | No | testing |
| FRONTEND_URL | No | http://localhost:5173 | ci | No | testing |
| PLAYWRIGHT_DEBUG | No | false | ci | No | testing |
| PLAYWRIGHT_HEADLESS | No | true | ci | No | testing |
| PLAYWRIGHT_SLOWMO | No | 0 | ci | No | testing |
| SKIP_E2E | No | false | ci | No | testing |
| SKIP_INTEGRATION | No | false | ci | No | testing |

---

### Website (`docs-site/`)

**Deploy target:** Static (no env vars required)

No environment variables. Docusaurus site built as static HTML.

---

## Cross-service variable matrix

| Variable | Agent | Gateway | Chat FE | DM FE | Scraper | Embedding | Model |
|----------|-------|---------|---------|-------|---------|-----------|-------|
| DATABASE_URL | x | x | | | x | | |
| DEEPSEEK_API_KEY | x | x | | | | | |
| DEEPSEEK_BASE_URL | x | x | | | | | |
| EMBEDDING_SERVICE_AUTH_TOKEN | x | x | | | | | |
| EMBEDDING_UPSTREAM_URL | x | x | | | x | | |
| GROQ_API_KEY | x | x | | | | | |
| MODAL_FUNCTION_INVOCATION | x | x | | | | | |
| MODAL_TOKEN_ID | x | x | | | x | x | x |
| MODAL_TOKEN_SECRET | x | x | | | x | x | x |
| MODAL_WORKSPACE | | | | | x | | |
| OLLAMA_BASE_URL | x | x | | | x | | |
| OLLAMA_MODEL | x | | | | | | |
| OPENAI_API_KEY | x | x | | | | | |
| PORT | x | x | x | x | x | | |
| SCRAPER_API_KEYS | | x | | | x | | |

## Deployment target comparison

| Variable | Local | Render prod | Render staging | Modal | CI |
|----------|-------|-------------|----------------|-------|----|
| DATABASE_URL | localhost:5432 | fromDatabase (internal) | fromDatabase (internal) | External Render URL | localhost:5432 |
| EMBEDDING_UPSTREAM_URL | http://localhost:8001 | Modal HTTPS URL | Modal HTTPS URL | (same app) | mock |
| MODAL_FUNCTION_INVOCATION | auto | auto | auto | n/a | off |
| OLLAMA_BASE_URL | http://localhost:11434 | Modal HTTPS URL | Modal HTTPS URL | http://localhost:11434 | mock |
| VITE_GATEWAY_URL | /api (proxy) | https://…onrender.com/api/v1 | https://…staging.onrender.com/api/v1 | n/a | http://localhost:8004/api/v1 |

## Sensitive variables (never commit)

| Variable | Where to set | Services |
|----------|-------------|----------|
| DATABASE_URL (production) | Render fromDatabase binding | Agent, Gateway, Scraper |
| DEEPSEEK_API_KEY | Render env group / .env.local | Agent, Gateway |
| DEV_ADMIN_BEARER_TOKEN | Render env group / .env.local | Gateway |
| EMBEDDING_SERVICE_AUTH_TOKEN | Render env group / .env.local | Agent, Gateway |
| GROQ_API_KEY | Render env group / .env.local | Agent, Gateway |
| LANGSMITH_API_KEY | Render env group / .env.local | Agent |
| MODAL_TOKEN_ID | Render env group / Modal secret | All Modal callers |
| MODAL_TOKEN_SECRET | Render env group / Modal secret | All Modal callers |
| OPENAI_API_KEY | Render env group / .env.local | Agent, Gateway |
| SCRAPER_API_KEYS | Render env group | Gateway, Scraper |
| SUPABASE_KEY | .env.local / Supabase dashboard | Agent, Gateway |
| SUPABASE_SERVICE_KEY | Modal secret / .env.local | Scraper |
| TAVILY_API_KEY | Render env group / .env.local | Agent |
| VITE_DEV_ADMIN_PASSWORD | .env.local (dev only) | Chat FE |
| VITE_DEV_ADMIN_TOKEN | .env.local (dev only) | Chat FE |

## Profile groups

| Profile | Purpose | Variables |
|---------|---------|-----------|
| alternate-llm-providers | LLM API keys for multi-provider fallback | GROQ_API_KEY, OPENAI_API_KEY, DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL, TAVILY_API_KEY, HUGGINGFACE_ACCESS_TOKEN, GUARDRAILS_AI_API_KEY |
| data-db-routing | Postgres vs Supabase data paths | DB_DATA_MODE, POSTGRES_DATA_READS_ENABLED, SUPABASE_DATA_READS_ENABLED, VECTOR_SYNC_TARGET, VECTOR_SYNC_SUPABASE_FALLBACK_READS |
| deploy-hooks-and-tooling | CI/CD tokens and deploy hooks | CODECOV_TOKEN, GCLOUD_*, RENDER_*_DEPLOY_HOOK |
| embedding-and-local-models | Local embedding/model config | EMBEDDING_MODEL, USE_LOCAL_EMBEDDINGS, EMBEDDING_PROVIDER, FASTEMBED_MODEL, DEFAULT_PROVIDER, DEFAULT_MODEL, OLLAMA_*, AGENT_ENFORCE_ROUTE, LOCK_MODEL_SELECTION, FORCE_LOCAL_MODAL_LLM, RENDER_REMOTE_INFERENCE_ONLY, RENDER_DISABLE_LOCAL_GUARDRAILS |
| gateway-admin | Dev admin authentication | GATEWAY_PORT, DEV_ADMIN_ENABLED, DEV_ADMIN_BEARER_TOKEN |
| langsmith-tracing | Observability and tracing | LANGSMITH_TRACING, LANGSMITH_ENDPOINT, LANGSMITH_API_KEY, LANGSMITH_PROJECT |
| local-chat-and-gateway-tuning | Local dev overrides for timeouts/routing | AGENT_SERVICE_URL, AGENT_TIMEOUT, AGENT_STREAM_TIMEOUT, MODAL_WORKSPACE, MODAL_FUNCTION_INVOCATION, MODAL_SCRAPER_PERSIST_VIA_GATEWAY, ALLOWED_ORIGINS, VITE_GATEWAY_PROXY_TARGET, VITE_AGENT_*_TIMEOUT_MS, VITE_DM_API_BASE_URL, VITE_DEFAULT_SCRAPER_USER_ID |
| modal-runtime | Modal SDK auth and config | MODAL_API_PROFILE, MODAL_API_PROXY_KEY, MODAL_TOKEN_*, MODAL_API_TOKEN_*, MODAL_AUTH_*, EMBEDDING_SERVICE_AUTH_TOKEN, MODAL_EMBEDDING_SERVICE_AUTH_TOKEN |
| render-postgres | Render Postgres connection details | RENDER_POSTGRES_*, RENDER_DATABASE_URL |
| runtime-flags | Misc runtime behavior toggles | TF_ENABLE_ONEDNN_OPTS |
| search-edge | Database search edge function config | DB_SEARCH_EDGE_*, DB_SEARCH_FORCE_SQL_FALLBACK, DB_SEARCH_TRY_TEXT_WRAPPER |
| service-wiring-and-scraper | Cross-service URL wiring | OLLAMA_BASE_URL, EMBEDDING_UPSTREAM_URL, VECINITA_SCRAPER_API_URL, RENDER_GATEWAY_URL, RENDER_AGENT_URL, DATA_MANAGEMENT_API_URL, REINDEX_*, SCRAPER_REINDEX_* |
| supabase-extended | Extended Supabase auth tokens | SUPABASE_PUBLISHABLE_KEY, SUPABASE_SECRET_KEY, SUPABASE_PERSONAL_ACCESS_TOKEN |
