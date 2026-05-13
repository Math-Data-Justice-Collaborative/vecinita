# Data Management API — Dependencies

> Auto-generated: 2026-05-12

## Overview

The data-management API depends on internal monorepo packages for typed clients,
schemas, and config, plus a focused set of external Python packages. At runtime
it requires connectivity to the scraper service and optionally Modal.

## Internal Dependencies (monorepo)

| Package/Module | Path | Purpose |
|----------------|------|---------|
| shared-config | `apis/data-management-api/packages/shared-config/` | `BaseServiceSettings` via pydantic-settings, env var loading, legacy alias warnings |
| shared-schemas | `apis/data-management-api/packages/shared-schemas/` | Pydantic models for `EmbedRequest/Response`, `PredictRequest/Response`, `ScrapeRequest/Result` |
| service-clients | `apis/data-management-api/packages/service-clients/` | `ScraperClient`, `EmbeddingClient`, `ModelClient`, `modal_invoker` |
| shared-logging | `apis/data-management-api/packages/shared-logging/` | Structured logging setup |

## External Dependencies (runtime)

| Package | Version | Purpose | Critical |
|---------|---------|---------|----------|
| fastapi | ≥0.110 | Web framework, routing, middleware | yes |
| uvicorn[standard] | ≥0.27 | ASGI server | yes |
| httpx | ≥0.27 | Async HTTP client for service-to-service calls | yes |
| pydantic | ≥2.6 | Data validation and serialization | yes |
| pydantic-settings | ≥2.0 | Environment-based configuration | yes |
| modal | ≥1.3.5 | Modal SDK for function invocation | conditional (when `MODAL_FUNCTION_INVOCATION` enabled) |
| PyYAML | (transitive) | `env_deprecation.py` reads YAML alias config | no |

**Source:** `apis/data-management-api/apps/backend/pyproject.toml`

## Infrastructure Dependencies

| Resource | Provider | Purpose |
|----------|----------|---------|
| PostgreSQL 16 | Render (`vecinita-postgres`) | Validated at startup via `DATABASE_URL`; actual reads/writes done by scraper |
| Container runtime | Render Docker | Production hosting |
| Modal platform | Modal Labs | Remote function invocation (optional) |

## Service Dependencies (runtime calls)

| Service | Required | Fallback |
|---------|----------|----------|
| Scraper service (`SCRAPER_SERVICE_BASE_URL`) | yes — `/jobs` proxy and `/health` depend on it | 503 to caller |
| Embedding service (`EMBEDDING_SERVICE_BASE_URL`) | yes for `/embed` | 502/503 to caller |
| Model service (`MODEL_SERVICE_BASE_URL`) | yes for `/predict` | 502/503 to caller |
| Modal (SDK) | no — only when `MODAL_FUNCTION_INVOCATION` is enabled | Falls back to HTTP clients |

## Dependency Rules

1. `apps/backend` may import from `packages/*` — never the reverse
2. No circular dependencies between packages
3. Cross-service communication is HTTP or Modal SDK only — no direct Python imports from other deployables
4. `packages/*` must not import FastAPI app modules

**Source:** `apis/data-management-api/README.md` (Dependency Model section)

## Related Documents

- [Infrastructure Plan](12-infrastructure-plan.md)
- [Integration Points](03-integration-points.md)
