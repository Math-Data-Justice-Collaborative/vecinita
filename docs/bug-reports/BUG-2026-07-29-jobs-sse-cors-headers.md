# BUG-2026-07-29 — Admin Jobs SSE blocked by CORS (Cache-Control / Last-Event-ID)

**Status:** resolved (PR #155 merged; Modal redeployed; live OPTIONS PASS)  
**Severity:** high — Jobs tab falls back to polling; live SSE never connects  
**Feature:** F32 / EV-012 — Modal `GET /jobs/events` (TC-148, RD-173)  
**Session:** S015-hotfix-jobs-sse-cors  
**Reported:** 2026-07-29  
**Environment:** Production admin → Modal data-management

## Error description

On the admin **Jobs** menu, the UI shows **“Live updates unavailable — polling every 4s.”**
SSE (`GET /jobs/events`) does not stay connected. Operator reported Network activity on
`/jobs/events` with body `{"detail":"Not found"}`. Job **list** still loads and polls.

## Error logs

```text
# Agent live probe 2026-07-29 — OPTIONS preflight matching FE subscribeJobEvents headers
OPTIONS https://vecinita--vecinita-data-management-fastapi-app.modal.run/jobs/events
Origin: https://vecinita-admin-frontend-ef4ob.ondigitalocean.app
Access-Control-Request-Method: GET
Access-Control-Request-Headers: accept,authorization,cache-control,x-vecinita-proxy-key

HTTP 400
Disallowed CORS headers

Access-Control-Allow-Headers: Accept, Accept-Language, Authorization,
  Content-Language, Content-Type, X-Vecinita-Proxy-Key
# Note: Cache-Control and Last-Event-ID are absent from Allow-Headers.

# Same path without Cache-Control / Last-Event-ID → OPTIONS 200
# GET /jobs (list) preflight with authorization + proxy key → 200 (poll path OK)
```

User-reported body on `/jobs/events`: `{"detail":"Not found"}` (interview A). Live OPTIONS
failure body is plain `Disallowed CORS headers` (not JSON). Treat CORS disallow as the
confirmed SSE breaker; reconcile the JSON body if it persists after CORS fix + redeploy.

## Symptoms & reproduction

| Field | Answer |
|-------|--------|
| Symptom | Live updates unavailable; SSE broken |
| Where | Production admin (ondigitalocean) |
| When | Ongoing (post EV-012 Jobs SSE) |
| Frequency | Every time |
| Repro env | Production |
| Severity | High |
| Evidence | UI pollFallback + live OPTIONS 400 |
| Jobs list | Loads / polls OK |

## Interview record (Phase 0)

| Field | Answer |
|-------|--------|
| Environment | A — Production admin |
| `Not found` location | A — Network on `GET …/jobs/events` |
| List behavior | A — List OK; only live-updates unavailable |
| Path | A — Fix CORS + Modal redeploy after approval |

## Investigation

| # | Hypothesis | Result |
|---|------------|--------|
| H1 | `/jobs/events` missing on production Modal | **Ruled out** — OpenAPI lists `/jobs/events`; unauthenticated GET → 401 |
| H2 | Wrong admin API host (write-api) | **Ruled out** — FE bundle `VITE_VECINITA_ADMIN_API_URL` is Modal ASGI |
| H3 | Proxy key / JWT only | **Partial** — missing JWT → 401; does not explain SSE-only failure while list polls |
| H4 | CORS preflight rejects SSE headers from `subscribeJobEvents` | **Confirmed** — `Cache-Control: no-cache` and `Last-Event-ID` not in `allow_headers` → OPTIONS 400 |

## Root cause

`subscribeJobEvents` (`apps/data-management-frontend/src/api/jobs.ts`) sends
`Cache-Control: no-cache` (and optionally `Last-Event-ID`). Data-management
`configure_cors(..., extra_allow_headers=[X-Vecinita-Proxy-Key])` did not allow those
headers. Browser OPTIONS failed → SSE never started → JobsPage `pollFallback`.

## Spec conformance

| Check | Result |
|-------|--------|
| `docs/api-contract.md` `GET /jobs/events` | Required; implemented |
| CORS / connectivity-gates H0c / H4 | Preflight must allow headers the browser actually sends |
| TC-148 / RD-173 | SSE primary; 4s poll fallback |

## Repro test

- Path: `tests/bugs/test_bug_2026_07_29_jobs_sse_cors_headers.py`
- Assert OPTIONS `/jobs/events` with `cache-control` + `last-event-id` (+ auth/proxy) → 200
  and Allow-Headers includes both.

### TDD iteration log

| # | Date | Action | Result |
|---|------|--------|--------|
| 1 | 2026-07-29 | Add unit repro for SSE CORS headers | **RED** — OPTIONS → 400 `Disallowed CORS headers` |
| 2 | 2026-07-29 | Allow `Cache-Control` + `Last-Event-ID` in DM CORS | **GREEN** |

## Remediation path

Local-first: extend data-management CORS `extra_allow_headers` with `Cache-Control` and
`Last-Event-ID`. Modal redeploy after user approval (Phase 4).

## Fix

`apps/data-management-backend/.../app.py` — `extra_allow_headers` includes
`Cache-Control` and `Last-Event-ID` alongside `X-Vecinita-Proxy-Key`.

## Verification plan

- Success: Jobs tab does not show pollFallback when SSE connects; OPTIONS with SSE headers → 200.
- Checks: bug repro green; `tests/unit/test_cors_policy.py`; local CI parity before PR.
- Post-deploy: user confirms production Jobs live updates; optional `@pytest.mark.live` OPTIONS.
