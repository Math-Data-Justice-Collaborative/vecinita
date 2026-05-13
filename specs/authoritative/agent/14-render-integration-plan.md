# Vecinita Agent — Render Integration Plan

> Auto-generated: 2026-05-12

## Overview

The agent is deployed as a Docker-based web service on Render under the name `vecinita-agent`. It is defined in the root `render.yaml` blueprint with infrastructure bindings to the shared PostgreSQL database and a comprehensive set of env vars synced from the Render env group.

## Service Definition

| Property | Value |
|----------|-------|
| Name | `vecinita-agent` |
| Type | web |
| Dockerfile | `./apis/agent/Dockerfile` |
| Docker context | `.` (repository root) |
| Start command | `uvicorn src.agent.main:app --host 0.0.0.0 --port ${PORT:-8000} --timeout-graceful-shutdown 30` |
| Plan | starter |
| Health check | `/health` |
| Region | virginia |
| Auto-deploy trigger | `checksPass` |

**Source:** `render.yaml` lines 23–163

## Environment Variables

### Infrastructure Bindings (from render.yaml)

| Variable | Source | Type |
|----------|--------|------|
| PORT | static | `"10000"` |
| DATABASE_URL | fromDatabase: vecinita-postgres | connectionString |
| DB_HOST | fromDatabase: vecinita-postgres | host |
| DB_PORT | fromDatabase: vecinita-postgres | port |
| DB_NAME | fromDatabase: vecinita-postgres | database |
| DB_USER | fromDatabase: vecinita-postgres | user |
| DB_PASSWORD | fromDatabase: vecinita-postgres | password |
| PGHOST | fromDatabase: vecinita-postgres | host |
| PGPORT | fromDatabase: vecinita-postgres | port |
| PGDATABASE | fromDatabase: vecinita-postgres | database |
| PGUSER | fromDatabase: vecinita-postgres | user |
| PGPASSWORD | fromDatabase: vecinita-postgres | password |
| POSTGRES_AUTO_CREATE_VECTOR_EXTENSION | static | `"true"` |
| POSTGRES_AUTO_BOOTSTRAP_SCHEMA | static | `"true"` |

### Env Group Variables (sync: false)

| Variable | Purpose | Category |
|----------|---------|----------|
| PYTHONUNBUFFERED | Disable output buffering | Runtime |
| TF_ENABLE_ONEDNN_OPTS | Disable TensorFlow oneDNN | Runtime |
| OLLAMA_MODEL | Default model tag | AGENT |
| OLLAMA_BASE_URL | LLM endpoint URL | AGENT/MODAL |
| EMBEDDING_UPSTREAM_URL | Embedding service URL | AGENT |
| EMBEDDING_SERVICE_AUTH_TOKEN | Embedding auth token | AGENT |
| EMBEDDING_STRICT_STARTUP | Fail if embedding unreachable | AGENT |
| RENDER_REMOTE_INFERENCE_ONLY | Block local model loading | STRICT |
| RENDER_DISABLE_LOCAL_GUARDRAILS | Disable local guardrails on Render | STRICT |
| DEFAULT_PROVIDER | Default LLM provider | AGENT |
| DEFAULT_MODEL | Default model override | AGENT |
| FORCE_LOCAL_MODAL_LLM | Force Modal native API | AGENT |
| LOCK_MODEL_SELECTION | Lock runtime model switching | AGENT |
| MODAL_TOKEN_ID | Modal SDK auth | MODAL |
| MODAL_TOKEN_SECRET | Modal SDK auth | MODAL |
| MODAL_FUNCTION_INVOCATION | SDK vs HTTP invocation mode | MODAL |
| BACKEND_PREFLIGHT_ENABLED | Enable startup diagnostics | AGENT |
| BACKEND_PREFLIGHT_STRICT | Fail on preflight errors | AGENT |
| GUARDRAILS_REQUIRE_HUB_VALIDATOR | Require Guardrails Hub | AGENT |
| GUARDRAILS_HUB_AUTO_INSTALL | Auto-install Hub validators | AGENT |
| GUARDRAILS_PERSISTENCE_DIR | Cache dir for guardrails | AGENT |
| DB_DATA_MODE | Data backend mode | AGENT |
| VECTOR_SYNC_TARGET | Vector sync target | AGENT |
| GROQ_API_KEY | Groq provider key (legacy) | AGENT |
| OPENAI_API_KEY | OpenAI provider key (legacy) | AGENT |
| DEEPSEEK_API_KEY | DeepSeek provider key (legacy) | AGENT |
| DEEPSEEK_BASE_URL | DeepSeek endpoint (legacy) | AGENT |
| TAVILY_API_KEY | Tavily web search | AGENT |
| LANGSMITH_API_KEY | LangSmith tracing | AGENT |
| LANGSMITH_PROJECT | LangSmith project name | AGENT |
| RENDER_GATEWAY_URL | Gateway internal URL | AGENT |
| RENDER_AGENT_URL | Agent internal URL | AGENT |
| DATA_MANAGEMENT_API_URL | DM API URL | AGENT |
| GATEWAY_SCHEMA_URL | Gateway OpenAPI schema | AGENT |
| AGENT_SCHEMA_URL | Agent OpenAPI schema | AGENT |
| EMBEDDING_SERVICE_SCHEMA_URL | Embedding OpenAPI schema | AGENT |
| VECINITA_SCRAPER_API_URL | Scraper API URL | AGENT |
| REINDEX_SERVICE_URL | Reindex service URL | AGENT |
| REINDEX_TRIGGER_TOKEN | Reindex auth token | AGENT |

## Database Binding

| Database | Variable | Access |
|----------|----------|--------|
| vecinita-postgres | DATABASE_URL | connectionString |
| vecinita-postgres | DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD | Component vars |
| vecinita-postgres | PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD | libpq-compatible vars |

## Service-to-Service Bindings

| Target Service | Variable | Mechanism |
|----------------|----------|-----------|
| vecinita-agent → vecinita-gateway | N/A | Agent is called *by* gateway, not the reverse |
| vecinita-gateway → vecinita-agent | `AGENT_SERVICE_URL` (on gateway) | `fromService: vecinita-agent` (hostport) |

## Preview Environments

PR previews inherit the service definition. Auto-deploy trigger (`checksPass`) ensures only CI-passing commits are deployed to previews.

## Cross-reference

- [Render Landscape](../render/current-landscape.md)

## Related Documents

- [Infrastructure Plan](12-infrastructure-plan.md)
- [Integration Points](03-integration-points.md)
