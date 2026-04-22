# Data model — configuration and API DTOs

## Configuration entities

### ChatFrontendGatewayConfig

| Field / env var | Type | Description |
|-----------------|------|---------------|
| `VITE_GATEWAY_URL` | string | Preferred API base; often `/api` in dev (Vite proxy) or absolute gateway URL in prod. |
| `VITE_BACKEND_URL` | string (optional) | Fallback base for resolution helpers. |
| `VITE_GATEWAY_PROXY_TARGET` | string | Dev-only proxy upstream (e.g. `http://127.0.0.1:8004`). |
| `VITE_AGENT_REQUEST_TIMEOUT_MS` | number | Non-stream HTTP timeout. |
| `VITE_AGENT_STREAM_TIMEOUT_MS` | number | Full SSE stream timeout. |
| `VITE_AGENT_STREAM_FIRST_EVENT_TIMEOUT_MS` | number | Time to first SSE event. |

### BackendGatewayAgentConfig

| Field / env var | Type | Description |
|-----------------|------|---------------|
| `GATEWAY_PORT` | int | Local gateway listen port (e.g. 8004). |
| `AGENT_SERVICE_URL` | URL | Gateway → agent backend (compose/local). |
| `AGENT_TIMEOUT` / `AGENT_STREAM_TIMEOUT` | int | Server-side upstream timeouts; should stay **below** browser abort thresholds. |
| `RENDER_GATEWAY_URL` / `RENDER_AGENT_URL` | URL (optional) | Documented Render examples in templates; not read directly by Vite—used for ops and schema URLs. |
| `GATEWAY_SCHEMA_URL` / `AGENT_SCHEMA_URL` | URL | OpenAPI JSON endpoints for contract tests. |

### DataManagementFrontendConfig

| Field / env var | Type | Description |
|-----------------|------|---------------|
| `VITE_VECINITA_SCRAPER_API_URL` | absolute URL | Base origin for scraper API (`/health`, `/jobs`…); required for non-localhost dashboards. |
| `VITE_DEFAULT_SCRAPER_USER_ID` | string | Default user id on job requests. |
| `VITE_USE_GATEWAY_MODAL_JOBS` | boolean string | When true, use gateway modal-jobs scraper root. |
| `VITE_VECINITA_GATEWAY_URL` | URL | Gateway origin for modal-jobs path when flag enabled. |

### DataManagementApiRuntime

| Field / env var | Type | Description |
|-----------------|------|---------------|
| `PORT` / listen | int | API listen (e.g. 8005 local convention). |
| `ALLOWED_ORIGINS` | JSON array string | CORS allowlist including `http://localhost:5174` per `BaseServiceSettings`. |

## API DTOs (scrape jobs)

Align these between **Python** (`shared_schemas.scraper`, FastAPI routes in scraper service) and **TypeScript** (`modal-types`, `rag-api.ts`):

- **ScrapeRequest**: `url` (HTTP URL), `depth` (integer, clamped in UI as today).
- **Job identity**: `job_id` string; status fields as returned by list/detail endpoints (including Modal-specific status mapping already centralized in `mapModalStatusToFrontendStatus`).
- **List/detail responses**: Shapes returned by `GET /jobs`, `GET /jobs/:id`, `POST /jobs`, cancel route — must match OpenAPI operation schemas after implementation tasks.

## Relationships

- `ChatFrontendGatewayConfig` → HTTP → `BackendGatewayAgentConfig` (gateway aggregates agent).
- `DataManagementFrontendConfig` → HTTP → `DataManagementApiRuntime` (direct) **or** via `VITE_VECINITA_GATEWAY_URL` modal-jobs subtree when gateway flag is set.
- `DataManagementApiRuntime` may proxy to remote scraper/model/embedding URLs via `BaseServiceSettings` — out of scope for UI field parity beyond scrape job JSON.

## Validation rules

- DM dashboard: `VITE_VECINITA_SCRAPER_API_URL` must be a valid `http:` or `https:` URL when not in mock mode (`getScraperConfigDiagnostic`).
- Chat: relative gateway URL only where `agentApiResolution` explicitly supports current host (localhost vs deployed).

## State transitions

- Scrape job status transitions remain those already defined in the frontend mapper and backend; this feature does not introduce new states—only ensures env and schemas do not desynchronize.

## Typed testing artifacts (TypeScript)

Use one **canonical type** (or Zod schema + inferred type) per HTTP JSON boundary so **runtime client**, **Pact matchers**, and **Vitest fixtures** import the same definition.

| Artifact | Purpose | Chatbot example | DM example |
|----------|---------|-----------------|------------|
| `ApiRequest*` / `ApiResponse*` types or Zod | Request/response bodies for gateway/agent | Agent config DTO, chat completion payload | `ScrapeRequest`, job list row |
| `PactInteractionDescriptor` (optional thin wrapper) | Names provider state + path template for a pact test | “gateway returns 200 for GET /api/v1/…” | “DM GET /jobs returns list” |
| OpenAPI-generated `paths[...]` types | Compile-time tie to exported OpenAPI | From `GATEWAY_SCHEMA_URL` export | From DM `openapi.json` |

**Rule**: No duplicate anonymous object shapes for the same endpoint in `rag-api.ts` / `agentService.ts` and Pact tests—refactor to shared module (e.g. `frontend/src/app/types/contracts.ts`, `apps/data-management-frontend/src/app/api/types/`).

## Python alignment

- **Pydantic** models in `packages/shared-schemas` remain authoritative on the server; OpenAPI emitted from FastAPI must match those models so **Schemathesis** and **OpenAPI codegen** stay consistent.
