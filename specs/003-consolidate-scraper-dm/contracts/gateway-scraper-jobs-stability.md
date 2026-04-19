# Contract: Gateway `/api/v1/modal-jobs/scraper*` stability and persistence boundary

**Status**: Draft (feature `003-consolidate-scraper-dm`)  
**Related doc**: [RENDER_SHARED_ENV_CONTRACT.md](../../../docs/deployment/RENDER_SHARED_ENV_CONTRACT.md)

## Purpose

Stabilize **public** gateway operations for Modal-backed scraping jobs so live contract tests do not
observe **5xx** when the deployment is advertised as healthy.

## Operations

- `POST /api/v1/modal-jobs/scraper` — create job  
- `GET /api/v1/modal-jobs/scraper` — list jobs  
- `GET /api/v1/modal-jobs/scraper/{job_id}` — status  
- `POST /api/v1/modal-jobs/scraper/{job_id}/cancel` — cancel  

## Success and error semantics (healthy dependency tier)

| Condition | Expected class |
|-----------|----------------|
| Valid create payload, DB + Modal available | **2xx** with job representation per OpenAPI |
| Unknown `job_id` | **404** with stable error body |
| Invalid client input | **422** / **400** per OpenAPI |
| Dependency misconfiguration (e.g. DB unreachable from gateway) | **503** (preferred) or **500** only if unavoidable — **response body MUST NOT** include internal DNS names (**FR-002**) |
| Modal RPC failure after gateway persisted row | Documented **5xx** with operator-safe message + correlation ID |

## Persistence split (`MODAL_SCRAPER_PERSIST_VIA_GATEWAY`)

When enabled (see deployment contract):

- Gateway **inserts** `scraping_jobs` (or equivalent) using gateway **`DATABASE_URL`**.  
- Modal submit is **enqueue-only** with `job_id` in payload.  
- List / get / cancel use **gateway** DB access without calling Modal RPCs for those paths.

Operators **MUST** set Modal secrets so workers do not use internal-only Render hostnames for stages
that run **outside** Render’s private network.

## Correlation identifiers (**FR-006**)

- **HTTP**: Gateway responses for the operations above **MUST** expose a stable correlation
  identifier (header and/or `ErrorResponse`-shaped JSON) consistent with other gateway routes.  
- **Modal submit**: When the gateway calls `modal_scrape_job_submit`, the same identifier **MUST**
  appear inside the RPC `payload` dict using a key the scraper accepts (exact key is chosen during
  **T011**—common patterns include a dedicated top-level field or nesting under `metadata`).  
- **Record**: Once implemented, add the chosen payload key and any worker log field name to
  `specs/003-consolidate-scraper-dm/baseline-notes-schemathesis.md` (or a one-line amendment here) so
  operators know what to grep in Modal logs.

## Testing hooks

Schemathesis hooks may set `SCHEMATHESIS_MODAL_SCRAPER_JOB_ID` and related env vars (see
`backend/scripts/run_schemathesis_live.sh`) so `GET`/`cancel` paths hit **existing** rows where
required.
