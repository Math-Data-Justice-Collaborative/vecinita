# BUG-2026-05-22 — Admin GET /jobs/{id} returns 404 Not Found

> Status: **resolved** (Modal deployed; API + admin UI verified)  
> Feature: **F8** (data management / ingest jobs)  
> Component: `apps/data-management-backend`, `infra/modal/data_management_app.py`, DO admin frontend

## Error description

After a successful `POST /jobs` (202 + `job_id`), polling with `GET /jobs/{job_id}` returns
**404 Not Found** with body `{"detail":"Not found"}`.

Target: `GET https://vecinita--vecinita-data-management-fastapi-app.modal.run/jobs/{job_id}`  
Origin: `https://vecinita-admin-frontend-ef4ob.ondigitalocean.app/`

Example job_id from user report: `23a92161-b56e-41a6-8df7-34d67db60c38`

## Error logs

```text
# User PowerShell (2026-05-22) — GET with X-Vecinita-Proxy-Key (value redacted)
# Response: 404 Not Found
# Body: {"detail":"Not found"}

# Agent probe — invalid proxy key (route exists; auth before store lookup)
curl -sS .../jobs/23a92161-b56e-41a6-8df7-34d67db60c38 -H 'X-Vecinita-Proxy-Key: invalid-test-key'
HTTP 401
{"detail":"Unauthorized"}
```

Related: [BUG-2026-05-22-admin-jobs-401-unauthorized.md](BUG-2026-05-22-admin-jobs-401-unauthorized.md) (resolved — POST auth).

## Symptoms & reproduction

| Field | Value |
|-------|--------|
| Symptom | Error — HTTP 404 on GET /jobs/{id} after POST 202 |
| Where | Production Modal; reproducible locally with split stores |
| When | After last deploy (POST proxy-header fix) |
| Frequency | Every time (per user) |
| Repro env | Production; local with isolated stores |
| Severity | Critical — cannot poll job status |
| Evidence | User PowerShell + job_id |
| Tried | Nothing |

## Remediation path

**local-first** — `DictJobStore` + `modal.Dict`; Modal deploy after user approval.

## Interview record (Phase 0)

| Field | Answer |
|-------|--------|
| Symptom | 404 on GET /jobs/{id} |
| Where | Production Modal |
| When | After last deploy |
| Frequency | Every time |
| Repro | Production + local |
| Severity | Critical |
| Evidence | PowerShell + job_id in chat |
| Tried | Nothing |

## Investigation

| # | Hypothesis | Result |
|---|------------|--------|
| H1 | Wrong path / route missing | **Ruled out** — 401 with bad key proves route exists |
| H2 | Auth header rejected on GET | **Ruled out** — user gets 404 not 401 with valid key |
| H3 | `InMemoryJobStore` not shared across Modal containers | **Confirmed** |
| H4 | Stale/wrong job_id | **Ruled out** for new jobs after fix; old ids pre-deploy still 404 |

## Root cause

Production used `InMemoryJobStore()` inside `fastapi_app()`. Modal ASGI scales to
multiple containers; `POST /jobs` wrote to container A's memory while `GET /jobs/{id}`
often read container B → `HTTPException(404, "Not found")` from `get_job()` when
`store.get_job` returned `None`. Auth and routing were correct (401 with bad key).

**Fix:** `DictJobStore` backed by `modal.Dict.from_name("vecinita-data-management-jobs")`
so all workers share job state.

## Spec conformance

| Doc | Result |
|-----|--------|
| `docs/feature-list.md` F8 | In scope |
| `docs/api-contract.md` | GET should return 200 for valid job_id |
| `docs/spec.md` §Data Management | Spec expects durable job status (DO store or API) — implementation uses in-memory Modal only (**drift**) |

## Repro test

| Test | Path | Status |
|------|------|--------|
| Isolated in-memory stores | `tests/bugs/test_bug_2026_05_22_admin_jobs_get_404_not_found.py` | green (documents bug class) |
| Split dict backings → 404 | same | green |
| Shared dict → 200 after POST | same | green |

## TDD iteration log

| # | Action | Result |
|---|--------|--------|
| 1 | Repro tests + `DictJobStore` | green locally |

## Fix

- `store.py`: `DictJobStore` with serialize/deserialize payloads.
- `infra/modal/data_management_app.py`: `modal.Dict.from_name("vecinita-data-management-jobs")`.

**Deploy:** `modal deploy infra/modal/data_management_app.py` — **done** 2026-05-22.

**Production smoke (agent):** POST 202 → GET 200 (`job_id` redacted); `status=running` after pipeline start.

## Verification plan

| Field | Value |
|-------|--------|
| Success | GET /jobs/{id} returns 200 after POST 202 in admin UI |
| L1 | `pytest tests/bugs/test_bug_2026_05_22_admin_jobs_get_404_not_found.py` + data-mgmt integration |
| L2 | User PowerShell POST then GET with same job_id |
| L3 | Modal deploy + production POST/GET smoke |
| L4 | User confirms admin poll works |
| Monitoring | 15-service-health follow-up after deploy |

### Verification

| Layer | Result | Notes |
|-------|--------|-------|
| L1 | pass | pytest bugs + data-mgmt integration |
| L2 | pass | Admin UI submit + poll (browser) |
| L3 | pass | Modal deploy + POST 202 / GET 200 smoke |
| L4 | pass | Admin UI: `Job … : completed`; GET network 200 |

## Timeline

| When | Event |
|------|--------|
| 2026-05-22 | Reported via 14-hotfix |
| 2026-05-22 | Admin UI E2E: submit job → poll → `completed`; GET 200 |
