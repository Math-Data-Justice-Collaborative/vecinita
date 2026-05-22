# BUG-2026-05-22 — Admin POST /jobs Failed to fetch (Modal proxy auth)

> Status: **resolved** (pending user browser confirm)  
> Feature: **F8** (data management / ingest jobs)  
> Component: `infra/modal/data_management_app.py`, `apps/data-management-backend`

## Error description

Submitting a scrape job from the admin frontend shows browser **Failed to fetch** (network error).

Target: `POST https://vecinita--vecinita-data-management-fastapi-app.modal.run/jobs`  
Referer: `https://vecinita-admin-frontend-ef4ob.ondigitalocean.app/`

## Error logs

```text
# Live OPTIONS preflight (agent, 2026-05-22) — browser sends this before POST
curl -X OPTIONS \
  'https://vecinita--vecinita-data-management-fastapi-app.modal.run/jobs' \
  -H 'Origin: https://vecinita-admin-frontend-ef4ob.ondigitalocean.app' \
  -H 'Access-Control-Request-Method: POST' \
  -H 'Access-Control-Request-Headers: content-type, modal-key'

HTTP/2 401
content-length: 56
# No access-control-allow-origin — request blocked at Modal proxy before ASGI
```

User DevTools: POST with `Modal-Key` and JSON body `{ urls, options }` — **Failed to fetch** in browser.

User PowerShell POST (same URL/headers) — evidence pasted in hotfix intake (contains proxy key — **rotate after incident**).

## Symptoms & reproduction

| Field | Value |
|-------|--------|
| Symptom | Error — Failed to fetch |
| Where | Production — admin frontend → Modal data-mgmt |
| When | After last deploy |
| Frequency | Every time |
| Repro env | User: neither yet; agent: OPTIONS preflight 401 reproducible |
| Severity | Critical — cannot submit jobs |
| Evidence | User curl + PowerShell; agent OPTIONS |
| Tried | Nothing |

## Remediation path

**local-first** — Modal redeploy after user approval.

## Investigation

| # | Hypothesis | Result |
|---|------------|--------|
| H1 | Modal `requires_proxy_auth` blocks OPTIONS preflight (401 at edge) | **Confirmed** — live OPTIONS 401, no CORS headers |
| H2 | Missing CORS origin on Modal (`VECINITA_CORS_ORIGINS`) | **Confirmed** — OPTIONS returned 405; secret lacks CORS; staging fallback added |
| H5 | `parents[2]` IndexError on Modal mount `/root/data_management_app.py` | **Confirmed** — container crash loop → 504/timeout |
| H3 | Wrong API URL in frontend bundle (H5) | **Ruled out** — request hits correct Modal host |
| H4 | App-level auth rejects POST | **Ruled out for preflight** — failure is before ASGI |

## Root cause

**Primary (browser):** `@modal.asgi_app(requires_proxy_auth=True)` rejected CORS **OPTIONS** at the
Modal edge (401) before FastAPI. Fixed: `requires_proxy_auth=False`; `Modal-Key` stays on POST/GET.

**Secondary (post-deploy outage):** Module import used `Path(__file__).parents[2]` but Modal mounts the
deploy file at `/root/data_management_app.py` → `IndexError` → container never started (504/timeout).
Fixed: `_resolve_repo_root()`.

**Tertiary (preflight 405):** Modal secret `vecinita-data-management` has no `VECINITA_CORS_ORIGINS`, so
`configure_cors()` attached no middleware. Fixed: staging origin fallback in `fastapi_app()` when unset.

## Spec conformance

| Doc | Result |
|-----|--------|
| `docs/feature-list.md` F8 | In scope (ingest job API) |
| `connectivity-gates.md` H4 | Implementation drift — Modal H4 was waived; browser POST /jobs requires fix |
| `docs/deploy-report.md` | Documented deferred resolution — now implementing app-level auth |
| ADR-002 | Hybrid Modal/DO — browser-facing Modal HTTP must be CORS-reachable |

**Blocking drift:** none.

## Repro test

| Test | Path | Status |
|------|------|--------|
| Modal ASGI must not use edge proxy auth | `tests/bugs/test_bug_2026_05_22_modal_jobs_failed_to_fetch.py` | red → green |
| OPTIONS without Modal-Key | same | green |
| Live OPTIONS H4 | same (`-m live`) | green (200 + Allow-Origin) |

## TDD iteration log

| # | Action | Result |
|---|--------|--------|
| 1 | Added repro tests | `test_modal_data_mgmt_asgi_does_not_use_edge_proxy_auth` RED |
| 2 | `requires_proxy_auth=False` on Modal ASGI | unit tests GREEN |
| 3 | `_resolve_repo_root()` for `/root` mount | health 200 |
| 4 | Staging `VECINITA_CORS_ORIGINS` fallback | OPTIONS 200 (pending redeploy) |

## Fix

- `infra/modal/data_management_app.py`: `requires_proxy_auth=False`, `_resolve_repo_root()`, staging
  CORS fallback when `VECINITA_CORS_ORIGINS` unset.
- **Deploy:** `modal deploy infra/modal/data_management_app.py` (redeployed 2026-05-22).
- **Follow-up:** Add `VECINITA_CORS_ORIGINS` to Modal secret `vecinita-data-management` (remove reliance on fallback).
- **Security:** Rotate `Modal-Key` / `VECINITA_MODAL_PROXY_KEY` exposed in DevTools intake.

## Verification plan

| Layer | Checks |
|-------|--------|
| Success | Failed to fetch gone — job submit works in admin UI |
| L1 | pytest bugs + `test_cors_policy.py` |
| L3 | Live OPTIONS + POST smoke on Modal after deploy |
| L4 | User browser repro + `15-service-health` follow-up |

## Timeline

| When | Event |
|------|--------|
| 2026-05-22 | Reported via 14-hotfix; live OPTIONS 401 observed |
