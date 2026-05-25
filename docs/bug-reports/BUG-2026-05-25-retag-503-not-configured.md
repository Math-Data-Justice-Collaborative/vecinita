# BUG-2026-05-25 — Retag endpoint 503 "Retag job client not configured"

> Status: **verifying**  
> Feature: **F20** (LLM auto-tagging at ingest + admin re-tag), **F21** (admin chunk/tag editor)  
> Component: `apps/internal-write-api/vecinita_internal_write_api/app.py`

## Error description

POST `/internal/v1/documents/{id}/retag` from the admin frontend returns HTTP 503. DigitalOcean App Platform intercepts the upstream 503 and serves its own error page (`via_upstream (503 -)`).

## Error logs

```text
HTTP 503 via_upstream — DigitalOcean App Platform error page:

  Error code: 503
  via_upstream (503 -)
  App Platform failed to forward this request to the application.

Request:
  POST https://vecinita-internal-write-api-icze4.ondigitalocean.app/internal/v1/documents/b39cd779-0275-46fa-997e-485ffa9b6938/retag
  Authorization: Bearer <redacted>
  Referer: https://vecinita-admin-frontend-ef4ob.ondigitalocean.app/
```

## Symptoms & reproduction

| Field | Value |
|-------|-------|
| Symptom | Error / crash — 503 on every retag attempt |
| Where | Production (DigitalOcean staging) |
| When | After last deploy (2026-05-25 EV-001) |
| Frequency | Every time |
| Repro env | Production only |
| Severity | Critical — retag completely broken |
| Evidence | 503 HTML from user |
| Tried | Nothing |

## Remediation path

**local-first** — deploy internal-write-api after user approval.

## Verification plan

| Field | Value |
|-------|-------|
| Success criterion | Original 503 error gone — retag returns a job_id |
| Verification checks | Full main CI parity (local) + gh on main after merge |
| Monitoring | Run 15-service-health follow-up after deploy |

## Investigation

| # | Hypothesis | Result |
|---|------------|--------|
| H1 | `create_app()` called by uvicorn `--factory` without `jobs_client` — retag_jobs is None → 503 | **Confirmed** — `app.py:68` `create_app(*, jobs_client=None)`, `app.py:339-342` returns 503 when None |
| H2 | DO app spec missing `VECINITA_MODAL_DATA_MGMT_URL` and `VECINITA_MODAL_PROXY_KEY` env vars | **Confirmed** — `infra/do/internal-write-api.yaml` only has DATABASE_URL, VECINITA_INTERNAL_API_KEY, VECINITA_ENV, VECINITA_CORS_ORIGINS |
| H3 | `do_apps.py` sync-secrets doesn't include modal env vars for write-api | **Confirmed** — `do_apps.py:195-199` only syncs DATABASE_URL, VECINITA_INTERNAL_API_KEY, VECINITA_CORS_ORIGINS |

## Root cause

`create_app()` accepts `jobs_client` as an optional parameter defaulting to `None`. In production, uvicorn calls the factory with `--factory` flag (no arguments), so `jobs_client` is always `None`. The endpoint then returns:

```python
if retag_jobs is None:
    raise HTTPException(status_code=503, detail="Retag job client not configured")
```

Additionally, the two env vars needed by `DataManagementJobsClient` (`VECINITA_MODAL_DATA_MGMT_URL`, `VECINITA_MODAL_PROXY_KEY`) are not in the DO app spec and not in the sync-secrets helper.

Classification: **Code bug** — `create_app()` factory path doesn't auto-create the jobs client from environment variables.

## Spec conformance

| Doc | Result |
|-----|--------|
| `docs/feature-list.md` F20/F21 | In scope — admin retag |
| `docs/spec.md` §Component Overview | Internal write API should support retag trigger |
| `docs/api-contract.md` | POST `/internal/v1/documents/{id}/retag` documented |
| `docs/deployment-integration.md` | Missing modal env vars for write-api |
| `docs/config-spec.md` | `VECINITA_MODAL_DATA_MGMT_URL` and `VECINITA_MODAL_PROXY_KEY` documented |

**Blocking drift:** `deployment-integration.md` missing env vars for internal-write-api retag client.

## Repro test

| Test | Path | Status |
|------|------|--------|
| Retag 503 when modal env vars set | `tests/bugs/test_bug_2026_05_25_retag_503_not_configured.py` | red → green |

### TDD iteration log

| # | Date | Action | Result |
|---|------|--------|--------|
| 1 | 2026-05-25 | Write repro test — assert retag != 503 when env vars set | RED: `503: {"detail":"Retag job client not configured"}` |
| 2 | 2026-05-25 | User confirmed repro matches symptom | confirmed |
| 3 | 2026-05-25 | Apply fix: `_default_jobs_client()` auto-creates from env vars | GREEN |

## Fix

Three changes:

1. **`apps/internal-write-api/vecinita_internal_write_api/app.py`**: Added `_default_jobs_client()` helper that creates `DataManagementJobsClient` from env vars (`VECINITA_MODAL_DATA_MGMT_URL`, `VECINITA_MODAL_PROXY_KEY`). `create_app()` now calls this as fallback when `jobs_client` is not explicitly provided.

2. **`infra/do/internal-write-api.yaml`**: Added `VECINITA_MODAL_DATA_MGMT_URL` and `VECINITA_MODAL_PROXY_KEY` as `SECRET` env vars in the DO app spec.

3. **`scripts/deploy/do_apps.py`**: Updated `cmd_sync_secrets` for `vecinita-internal-write-api` to include the two new env vars.

## Verification

### Layer 1 — Automated

- [x] Repro test red → green
- [x] Full unit test suite passes (81 passed, 0 failed)
- [ ] CI parity (local) passes

### Layer 2 — Reproduction

- [ ] Same retag POST from admin frontend returns job_id (not 503)

### Layer 3 — Pre-deploy smoke

- [ ] POST retag on staging returns 200 with job_id

### Layer 4 — Production

- [ ] Post-deploy retag from admin frontend works
- [ ] Logs clean — no recurrence of 503

### CI

- [ ] CI parity (local) before PR
- [ ] PR branch CI after push
- [ ] `gh run` on `main` after merge

## Post-deploy monitoring

Pending — 15-service-health follow-up.

## Prevention & countermeasures

Pending — Phase 5.

## Cursor rule

Pending — Phase 5.

## Regression prevention

- `tests/bugs/test_bug_2026_05_25_retag_503_not_configured.py`

## Timeline

| Event | Date |
|-------|------|
| User report | 2026-05-25 |
| Investigation start | 2026-05-25 |
| Root cause confirmed | 2026-05-25 |
| Fix applied | pending |
| Verified in production | pending |
