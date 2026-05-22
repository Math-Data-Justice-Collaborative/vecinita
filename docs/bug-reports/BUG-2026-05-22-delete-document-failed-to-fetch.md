# BUG-2026-05-22 — Admin DELETE document Failed to fetch (CORS)

> Status: **verifying**  
> Feature: **F12** (admin corpus / internal write API)  
> Component: `packages/shared-schemas/vecinita_shared_schemas/cors.py`, `apps/internal-write-api`

## Error description

Deleting a document from the admin frontend shows browser **Failed to fetch** (network error, no HTTP response body in DevTools).

Target: `DELETE https://vecinita-internal-write-api-icze4.ondigitalocean.app/internal/v1/documents/{id}`  
Referer: `https://vecinita-admin-frontend-ef4ob.ondigitalocean.app/`

## Error logs

```text
# Live OPTIONS preflight (agent, 2026-05-22) — simulates browser before DELETE
curl -X OPTIONS \
  'https://vecinita-internal-write-api-icze4.ondigitalocean.app/internal/v1/documents/e4d0f450-19dc-48dd-971b-3ff5739ad902' \
  -H 'Origin: https://vecinita-admin-frontend-ef4ob.ondigitalocean.app' \
  -H 'Access-Control-Request-Method: DELETE' \
  -H 'Access-Control-Request-Headers: authorization'

HTTP/2 400
access-control-allow-methods: GET, POST, OPTIONS
access-control-allow-origin: https://vecinita-admin-frontend-ef4ob.ondigitalocean.app
```

User also shared a direct `curl DELETE` from DevTools (includes Bearer token — **rotate key after incident**).

## Symptoms & reproduction

| Field | Value |
|-------|--------|
| Symptom | Error / crash — Failed to fetch |
| Where | Production DO (admin frontend → internal-write-api) |
| When | After last deploy (CORS redeploy 2026-05-21) |
| Frequency | Every time |
| Repro env | Production only (browser); server DELETE may work via curl without preflight |
| Severity | Critical — cannot delete documents |
| Evidence | User curl + agent preflight |
| Tried | Nothing |

## Remediation path

**local-first** — deploy internal-write-api after user approval.

## Investigation

| # | Hypothesis | Result |
|---|------------|--------|
| H1 | CORS `allow_methods` omits DELETE — browser blocks preflight | **Confirmed** — `cors.py:34`; live + unit preflight 400 |
| H2 | Wrong API URL in frontend bundle (H5) | Ruled out — request hits correct write-api host |
| H3 | Auth / 401 masked as fetch | Ruled out — preflight fails before auth |
| H4 | Origin not in VECINITA_CORS_ORIGINS | Ruled out — `access-control-allow-origin` set correctly |

## Root cause

`configure_cors()` in `vecinita_shared_schemas/cors.py` sets `allow_methods=["GET", "POST", "OPTIONS"]`.
Admin frontend `DELETE /internal/v1/documents/{id}` triggers a CORS preflight; Starlette returns 400
**Disallowed CORS method** and the browser surfaces **Failed to fetch**.

## Spec conformance

| Doc | Result |
|-----|--------|
| `docs/feature-list.md` F12 | In scope (admin corpus) |
| `connectivity-gates.md` H4 | DELETE preflight must succeed for browser DELETE |
| `cors.py` | Implementation drift — middleware missing DELETE |

**Blocking drift:** none.

## Repro test

| Test | Path | Status |
|------|------|--------|
| DELETE preflight on document path | `tests/bugs/test_bug_2026_05_22_delete_document_failed_to_fetch.py` | red → green (user confirmed) |

## Fix

- Added `DELETE` to `allow_methods` in `packages/shared-schemas/vecinita_shared_schemas/cors.py`.
- H0c: `test_internal_write_cors_preflight_allows_delete_document` in `tests/unit/test_cors_policy.py`.
- H4: `test_h4_write_api_cors_preflight_delete_document`; `assert_cors_preflight` checks `Allow-Methods`.

**Deploy:** Redeploy DO `internal-write-api` (and chat/data-mgmt if sharing package — same image rebuild).

## Verification plan

| User choice | Value |
|-------------|--------|
| Success | Failed to fetch gone; DELETE works in admin UI |
| Checks | Unit + DO smoke (H4 DELETE preflight) |
| Follow-up | 15-service-health after deploy |

| Layer | Check |
|-------|--------|
| L1 | Bug repro + `test_cors_policy.py` + full pytest |
| L2 | User DELETE in admin UI |
| L3 | Live OPTIONS DELETE preflight on staging write URL |
| L4 | Post-deploy admin DELETE + 15-service-health |

## TDD iteration log

| Run | Action | Result |
|-----|--------|--------|
| 1 | DELETE preflight repro test | red — 400 Disallowed CORS method |
| 2 | Add DELETE to `configure_cors` allow_methods | green — bug + H0c tests pass |
