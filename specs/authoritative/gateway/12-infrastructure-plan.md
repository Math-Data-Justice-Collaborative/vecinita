# Infrastructure Plan: Gateway
> Auto-generated: 2026-05-12

## Build

| Property | Value |
|----------|-------|
| Dockerfile | `apis/gateway/Dockerfile.gateway` |
| Base image | `python:3.11-slim-bookworm` |
| Build context | Repository root (`.`) |
| Multi-stage | Yes (builder + runtime) |
| Runtime deps installed in | `/usr/local` (via `--prefix=/install`) |
| Source copied | `apis/gateway/src/` → `/app/src/`, `apis/gateway/scripts/` → `/app/scripts/` |
| Entrypoint | `scripts/start_gateway_render.sh` |

### Build Args / Env

| Variable | Value | Purpose |
|----------|-------|---------|
| `PYTHONUNBUFFERED` | 1 | Real-time log output |
| `TF_ENABLE_ONEDNN_OPTS` | 0 | Suppress TensorFlow warnings |
| `PORT` | 10000 | Render default port |

## Deployment Target

| Property | Value |
|----------|-------|
| Platform | Render |
| Service type | Web service |
| Region | US (default) |
| Health check | `GET /health` |
| Health check interval | 30s |
| Health check timeout | 10s |
| Start period | 40s |
| Retries | 5 |

## Scaling

| Property | Current | Notes |
|----------|---------|-------|
| Instances | 1 | Single instance (rate limiting is in-memory) |
| Auto-scale | Not configured | Requires Redis for rate limiting before scale-out |
| CPU | Render default | No resource constraints specified |
| Memory | Render default | — |

## Environment Variables

### Required

| Variable | Purpose | Example |
|----------|---------|---------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:5432/db` |
| `AGENT_SERVICE_URL` | Agent service base URL | `http://vecinita-agent:8000` |

### Conditional (Modal)

| Variable | Purpose | Required When |
|----------|---------|---------------|
| `MODAL_FUNCTION_INVOCATION` | Enable Modal SDK (`auto`, `1`, `true`) | Using Modal for embed/scrape/reindex |
| `MODAL_TOKEN_ID` | Modal auth token ID | `MODAL_FUNCTION_INVOCATION` is on/auto |
| `MODAL_TOKEN_SECRET` | Modal auth token secret | `MODAL_FUNCTION_INVOCATION` is on/auto |
| `MODAL_SCRAPER_PERSIST_VIA_GATEWAY` | Gateway-owned scrape job persistence | Gateway manages job state |
| `SCRAPER_API_KEYS` | Auth tokens for Modal worker callbacks | Pipeline ingest endpoints |

### Optional

| Variable | Default | Purpose |
|----------|---------|---------|
| `GATEWAY_PORT` | 8004 (local), 10000 (Render) | Listen port |
| `ENABLE_AUTH` | false | Toggle Bearer authentication |
| `ALLOWED_ORIGINS` | localhost:5173,5174,4173 | CORS origins |
| `ALLOWED_ORIGIN_REGEX` | (empty) | CORS regex pattern |
| `EMBEDDING_UPSTREAM_URL` | localhost:8001 (local), Modal URL (Render) | Embedding service |
| `DEMO_MODE` | false | Return demo responses for Q&A |
| `AGENT_TIMEOUT` | 180 | Agent HTTP read timeout (seconds) |
| `AGENT_STREAM_TIMEOUT` | 180 | Agent SSE stream timeout (seconds) |
| `MAX_URLS_PER_REQUEST` | 100 | Scrape URL limit |
| `JOB_RETENTION_HOURS` | 24 | Scrape job cleanup threshold |
| `EMBEDDING_MODEL` | sentence-transformers/all-MiniLM-L6-v2 | Embedding model name |
| `EMBEDDING_DIMENSION` | 384 | Embedding vector dimension |
| `DEFAULT_PROVIDER` | ollama | LLM provider |
| `OLLAMA_MODEL` | gemma3 | Default LLM model |
| `RATE_LIMIT_*` | Various | Per-endpoint rate limit overrides |
| `GUARDRAILS_*` | Various | GuardrailsAI feature flags |

## Observability

| Concern | Current State |
|---------|--------------|
| Logging | Python `logging` module, structured messages with correlation IDs |
| Metrics | None (no Prometheus/StatsD) |
| Tracing | `X-Correlation-ID` header propagation, LangSmith integration available |
| Alerting | Render health check failures trigger platform alerts |
| Log aggregation | Render log viewer (no external aggregator configured) |

## Networking

| Connection | Protocol | Direction |
|-----------|----------|-----------|
| Frontend → Gateway | HTTPS (Render external) | Inbound |
| Gateway → Agent | HTTP (Render internal mesh / `fromService`) | Outbound |
| Gateway → PostgreSQL | TCP (Render managed) | Outbound |
| Gateway → Modal | HTTPS (Modal SDK) | Outbound |
| Modal Workers → Gateway | HTTPS (Render external) | Inbound |
