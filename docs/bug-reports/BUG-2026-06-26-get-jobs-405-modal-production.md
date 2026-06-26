# BUG-2026-06-26 — Production GET /jobs returns 405 Method Not Allowed

**Status:** resolved (Modal redeployed 2026-06-26; GET /jobs → 200)
**Severity:** high — Jobs tab cannot load job list
**Feature:** F32 — `GET /jobs` list API (ADR-023, issue #89)
**Reported:** 2026-06-26
**Branch:** `fix/jobs-dialog-aria-get-jobs-deploy`

## Error description

The admin Jobs tab calls `GET /jobs` on the Modal data-management API. Production returns HTTP **405** with `{"detail":"Method Not Allowed"}`, so the Jobs page shows a load error.

## Repro

1. Open admin Jobs tab (production).
2. Network: `GET https://vecinita--vecinita-data-management-fastapi-app.modal.run/jobs` with `X-Vecinita-Proxy-Key`.
3. **Expected:** `200` + `{ "jobs": [...] }`.
4. **Actual:** `405` + `{"detail":"Method Not Allowed"}`.

## Error logs

```http
GET /jobs → 405
{"detail":"Method Not Allowed"}
```

Agent probe (2026-06-26, no auth): `GET` → 405; `OPTIONS` → 200 (CORS preflight OK).

## Investigation

| Time | Finding |
|------|---------|
| 2026-06-26 | `create_app()` on `main` registers `@app.get("/jobs")` (`app.py:103-114`). |
| 2026-06-26 | E2E `test_uj023_job_management.py` passes locally against `create_app()`. |
| 2026-06-26 | Production Modal still serves pre–PR #95 image where only `POST /jobs` existed. |
| 2026-06-26 | Admin frontend on DO already deployed with Jobs tab calling `listJobs()`. |

**Root cause:** Config/infra — **undeployed Modal image**, not missing route in codebase.

## Spec conformance

| Check | Result |
|-------|--------|
| `docs/api-contract.md` / F32 | `GET /jobs` required; implemented on `main` |
| `deployment-integration.md` | Deploy via `modal deploy infra/modal/data_management_app.py` |

No code drift; deploy gap.

## Repro test

- Path: `tests/bugs/test_bug_2026_06_26_get_jobs_405_modal_production.py`
- `@pytest.mark.live`: `GET` production `/jobs` with proxy key → expect `200` (RED until Modal redeploy).
- Local: `TestClient(create_app()).get("/jobs")` already covered by `tests/unit/data_management/test_app.py`.

### TDD iteration log

| # | Date | Action | Result |
|---|------|--------|--------|
| 1 | 2026-06-26 | Add live repro test; curl confirms 405 on production | RED |
| 2 | 2026-06-26 | User Modal redeploy; probe GET /jobs → 200 (auth via bundle key) | GREEN |

## Remediation path

Local-first. No application code change required; **Modal redeploy** after user approval (Phase 4).

## Verification plan

- Success: `GET /jobs` → 200 on production; Jobs tab lists jobs.
- Checks: full local CI + `@pytest.mark.live` after deploy + user repro on Jobs tab.

## Fix

Redeploy Modal data-management from `main`:

```bash
modal deploy infra/modal/data_management_app.py
```

No Python source change unless redeploy still returns 405.

## Verification

### Layer 1 — Automated

- [x] Local `create_app` GET /jobs tests pass on `main`
- [x] Live repro test green after Modal deploy

### Layer 2 — Reproduction

- [ ] Jobs tab loads without error alert

### Layer 4 — Production

- [x] `GET /jobs` 200 on live Modal URL (user-approved deploy)
