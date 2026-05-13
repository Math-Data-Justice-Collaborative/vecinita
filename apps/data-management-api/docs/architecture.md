# Architecture — data-management-api workspace

## Overview

This package is the **Vecinita data-management API** workspace: typed **service-clients**, shared
config/schemas, and the FastAPI app under **`apps/backend/vecinita_dm_api/`** that fronts scraping and
related orchestration for the **data-management SPA**.

## Services (conceptual)

### Data-management API (this repo / Render `vecinita-data-management-api`)

Python service that exposes scraper-compatible **`/health`**, **`/jobs`**, and related HTTP routes
to the **browser** only through the configured public hostname. **Server-side**, it reaches
Modal-deployed scraper, embedding, and model workloads via **`modal.Function.from_name`** +
**`.remote()` / `.spawn()`** when **`MODAL_FUNCTION_INVOCATION`** is enabled — not via direct
browser calls to `*.modal.run` for those responsibilities (feature **007**).

### Data-management SPA (`frontends/data-management/` in monorepo root)

React/Vite dashboard. It MUST use **`VITE_DM_API_BASE_URL`** (HTTP origin of the data-management API)
pointing at the **data-management API** origin; scrape job CRUD uses **`{DM}/jobs`**.

### Scraper / embedding / model Modal apps (`modal-apps/scraper`, `modal-apps/embedding-modal`, …)

Deployed Modal **functions** invoked from backends (gateway, agent, DM API) with workspace tokens.
They are not the primary **browser** surface for operator scraping flows.

## Deployment model (007)

```
data-management SPA  ──HTTPS──►  data-management API  ──Modal SDK──►  scraper / embed / model apps
        (VITE_DM_API_BASE_URL)           (public host)              (Function.from_name + remote/spawn)
```

## Shared packages (this workspace)

| Package | Purpose |
|---------|---------|
| `shared-schemas` | Pydantic models for API contracts |
| `service-clients` | Typed async clients + `modal_invoker` for upstream Modal/HTTP |
| `shared-config` | Base settings using pydantic-settings |
| `shared-logging` | Structured JSON logging |

## Dependency rules

1. `apps` may depend on `packages`
2. `packages` must **never** depend on `apps`
3. Lower-level packages must **not** import FastAPI apps in a way that creates cycles

## Communication patterns

| Caller | Callee | Protocol | Notes |
|--------|--------|----------|-------|
| DM SPA | data-management API | HTTPS | Same origin family as `VITE_DM_API_BASE_URL` |
| data-management API | Modal apps | Modal Python SDK | When `MODAL_FUNCTION_INVOCATION` + tokens set |
| data-management API | upstream HTTP | HTTPS | Allowed for **non-production** / tests per **FR-009** |
