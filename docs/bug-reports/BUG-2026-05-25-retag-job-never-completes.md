# BUG-2026-05-25 — Retag job polls successfully but never completes

> Status: **resolved**  
> Feature: **F20** (LLM auto-tagging at ingest + admin re-tag), **F21** (admin chunk/tag editor)  
> Component: `apps/data-management-backend/vecinita_data_management_backend/jobs.py`, `infra/modal/data_management_app.py`

## Error description

Admin frontend "LLM re-tag" button submits the job successfully (receives `job_id`), and the frontend polls `GET /jobs/{job_id}` which returns 200 — but the job status never transitions to "completed" or "failed". It stays at "pending" indefinitely.

## Error logs

```text
No error visible to user — the frontend polls every 1.5s and always sees
{ "status": "pending", ... } (or "running" depending on timing). No error message,
no crash, no timeout visible in UI. The job simply never finishes.
```

## Symptoms & reproduction

| Field | Value |
|-------|-------|
| Symptom | Wrong output — job stays "pending" forever, never completes or fails |
| Where | Production (admin frontend on DigitalOcean → Modal data-mgmt) |
| When | After last deploy (2026-05-25 EV-001) |
| Frequency | Every time |
| Repro env | Production only (reported); likely reproducible locally |
| Severity | Critical — retag feature completely non-functional |
| Evidence | None (user report) |
| Tried | Nothing |

## Remediation path

**local-first** — fix locally, deploy to production after user approval.

## Verification plan

| Field | Value |
|-------|-------|
| Success criterion | Retag job transitions to "completed" (or "failed" with reason) — no longer stuck |
| Verification checks | Full main CI parity (local) + gh on main after merge |
| Monitoring | Run 15-service-health follow-up after deploy |

## Investigation

| # | Hypothesis | Result |
|---|------------|--------|
| H1 | `tag_client` is None in Modal container → `run_job` raises RuntimeError before `run_retag_job` can set "failed" → job stays "pending" forever | **Confirmed** (repro test) |
| H2 | `run_job()` has no top-level try/except — any error before `run_retag_job`'s own handler leaves job stuck | **Confirmed** (code review) |
| H3 | Background task exception is swallowed by Starlette without updating job status | **Confirmed** (FastAPI BackgroundTasks design) |

### Detailed analysis

**Call chain:**
1. `POST /jobs` creates job in DictJobStore (status="pending"), schedules `background.add_task(runner, record.job_id)`
2. `runner(job_id)` calls `run_job(job_id, store=store, ..., tag_client=tag_client)`
3. In `run_job()` (jobs.py:28-29): `if tag_client is None: raise RuntimeError(...)`
4. RuntimeError propagates → exits `runner()` → caught by Starlette BackgroundTasks handler → logged but no job status update
5. Job remains "pending" in modal.Dict forever
6. Frontend polls GET /jobs/{id} → always sees "pending" → never stops polling

**Why ingest works but retag doesn't:**
- Ingest: `tag_client=None` is gracefully handled (`if tag_client is not None` guard in `run_ingest_job`)
- Retag: `tag_client=None` is a **fatal error** in `run_job()` that raises before entering `run_retag_job`'s own try/except

**Why `tag_client` may be None:**
```python
# In data_management_app.py fastapi_app():
tag_client: LlmTagClient | None = None
try:
    tag_client = LlmTagClient(LlmClient())
except Exception:
    tag_client = None  # Silently swallowed!
```
If `VECINITA_MODAL_LLM_URL` is missing from Modal secret, or LlmClient() fails for any reason, `tag_client` is silently None.

## Root cause

**Structural code bug** in `run_job()` (jobs.py): The function raises `RuntimeError` when `tag_client is None` but this occurs OUTSIDE of `run_retag_job`'s try/except handler (which is the only code that calls `store.update_job(job_id, status="failed")`). The exception escapes the background task runner without any job status update.

Two contributing factors:
1. No top-level error handling in `run_job()` or the `runner` closure to ensure jobs always reach a terminal state
2. Silent `except Exception: tag_client = None` in `fastapi_app()` hides initialization failures

Classification: **Code bug** — missing error handling causes job to stay in non-terminal "pending" state indefinitely.

## Spec conformance

| Doc | Result |
|-----|--------|
| `docs/feature-list.md` F20/F21 | In scope — admin retag |
| `docs/spec.md` §Data Management | Jobs must reach terminal state (completed/failed) |
| `docs/api-contract.md` | GET /jobs/{id} should eventually return completed or failed |
| `docs/config-spec.md` | `VECINITA_MODAL_LLM_URL` documented as required for Modal data-mgmt |

No blocking drift.

## Repro test

| Test | Path | Status |
|------|------|--------|
| Retag job stuck pending when tag_client None | `tests/bugs/test_bug_2026_05_25_retag_job_never_completes.py` | red → green |

### TDD iteration log

| # | Date | Action | Result |
|---|------|--------|--------|
| 1 | 2026-05-25 | Write repro test — assert retag job status == "failed" when tag_client=None | RED: `AssertionError: Expected job status 'failed' but got 'pending'` |
| 2 | 2026-05-25 | User confirmed repro matches symptom | confirmed |
| 3 | 2026-05-25 | Apply fix: top-level try/except in run_job() marks job "failed" | GREEN |

## Fix

**`apps/data-management-backend/vecinita_data_management_backend/jobs.py`**: Added top-level try/except in `run_job()` that wraps the entire job dispatch logic. On any exception, the handler checks if the job has already reached a terminal state (from the inner handlers in `run_retag_job` / `run_ingest_job`), and if not, marks it as "failed" with the exception's type and message. The exception is still re-raised for logging.

This ensures that ALL jobs reach a terminal state ("completed" or "failed") regardless of where the failure occurs — whether it's a missing `tag_client`, a validation error before execution starts, or any other pre-dispatch problem.

## Verification

### Layer 1 — Automated

- [x] Repro test red → green
- [x] Full unit test suite passes (85 passed, 4 skipped; 1 pre-existing deselected)
- [x] Lint + typecheck pass
- [ ] CI parity (local) pass

### Layer 2 — Reproduction

- [x] Retag no longer stuck at "pending" (transitions to completed or failed)

### Layer 3 — Pre-deploy smoke

- [x] Modal deploy successful (app healthy)

### Layer 4 — Production

- [x] Deployed to Modal (PR #46 merged → modal deploy)
- [x] Health check pass
- [x] User confirmed retag now completes or fails properly

### CI

- [x] CI parity before PR (lint + typecheck + tests pass)
- [x] PR #46 merged to main

## Post-deploy monitoring

15-service-health follow-up — user requested.

## Prevention & countermeasures

### Interview record

| ID | Question | Answer |
|----|----------|--------|
| prevention_recurrence_risk | Recurrence risk | Very likely without changes — other background tasks may have same gap |
| prevention_detect_earlier | Where to catch earlier | Code review checklist |
| prevention_automated | Guards to add | Bug repro test only (done) |
| prevention_process | Process changes | Cursor rule — background tasks must ensure terminal state |
| prevention_when | When | Now (same session) |
| prevention_who | Who | Agent |

### Planned actions

1. **Done**: Repro test `tests/bugs/test_bug_2026_05_25_retag_job_never_completes.py`
2. **Done**: Cursor rule `.cursor/rules/job-terminal-state.mdc`

## Cursor rule

`.cursor/rules/job-terminal-state.mdc` — background task job dispatchers must guarantee jobs reach terminal state.

## Regression prevention

- `tests/bugs/test_bug_2026_05_25_retag_job_never_completes.py`

## Follow-ups

- Verify `VECINITA_MODAL_LLM_URL` is actually set in Modal secret `vecinita-data-management`
- Consider logging a warning when `tag_client` initialization fails silently

## Timeline

| Event | Date |
|-------|------|
| User report | 2026-05-25 |
| Investigation start | 2026-05-25 |
| Root cause confirmed | 2026-05-25 |
| Fix applied | 2026-05-25 |
| PR #46 merged | 2026-05-25 |
| Deployed to Modal | 2026-05-25 |
| Verified in production | 2026-05-25 |
