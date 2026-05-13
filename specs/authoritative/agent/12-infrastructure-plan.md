# Vecinita Agent — Infrastructure Plan

> Auto-generated: 2026-05-12

## Overview

The agent is built as a Docker container from a multi-stage Dockerfile and deployed as a web service on Render. It connects to the shared `vecinita-postgres` database and external Modal services for LLM inference and embeddings.

## Build

| Property | Value |
|----------|-------|
| Dockerfile | `apis/agent/Dockerfile` |
| Build context | `.` (repository root) |
| Base image | `python:3.11-slim-bookworm` (multi-stage) |
| Build stage | Installs Python deps to `/install` prefix |
| Runtime stage | Copies installed packages + application source |
| Build args | None |
| Source copy strategy | `apis/gateway/src/` → `src/` (shared modules), then `apis/agent/src/agent/` → `src/agent/` (agent package overwrite) |

## Deployment

| Property | Value |
|----------|-------|
| Platform | Render |
| Service type | web |
| Plan | starter |
| Region | virginia |
| Auto-deploy | `checksPass` (deploys after CI checks succeed) |
| Runtime | docker |

## Scaling

| Property | Value |
|----------|-------|
| Min instances | 1 (Render starter default) |
| Max instances | 1 (starter plan limitation) |
| Scaling trigger | None (manual plan upgrade required for auto-scaling) |

## Observability

| Concern | Tool | Config |
|---------|------|--------|
| Logging | stdout (structured `%(asctime)s - %(name)s - %(levelname)s - %(message)s`) | `PYTHONUNBUFFERED=1` |
| Tracing | LangSmith (optional) | `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT` env vars |
| Health check | `GET /health` (Render probe) | `healthCheckPath: /health`, interval 30s, timeout 10s, start-period 40s, retries 5 |
| Preflight | Optional startup diagnostics | `BACKEND_PREFLIGHT_ENABLED`, `BACKEND_PREFLIGHT_STRICT` env vars |
| Latency telemetry | Built-in `latency_breakdown` in `/ask` responses | Per-request timing: `retrieval_invoke_ms`, `llm_ms`, `db_search.*` |

## Environment Variables

See [Render Integration Plan](14-render-integration-plan.md) for the full env var matrix.

## Start Command

```
uvicorn src.agent.main:app --host 0.0.0.0 --port ${PORT:-8000} --timeout-graceful-shutdown 30
```

## Related Documents

- [Render Integration Plan](14-render-integration-plan.md)
- [Modal Integration Plan](13-modal-integration-plan.md)
