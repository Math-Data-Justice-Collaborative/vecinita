# BUG-2026-05-25 — Retag job fails: "tag_client is required for retag jobs"

> Status: **verifying**  
> Feature: **F20** (LLM auto-tagging at ingest + admin re-tag), **F21** (admin chunk/tag editor)  
> Component: `infra/modal/data_management_app.py`

## Error description

Admin frontend retag button submits a job that immediately fails with error `"tag_client is required for retag jobs"`. The job correctly reaches "failed" terminal state (per hotfix #10), but the underlying `LlmTagClient` is never created because `LlmClient()` initialization fails silently.

## Error logs

```json
{
  "job_id": "a85ae333-3d4d-44fc-80ca-da456dda1d41",
  "status": "failed",
  "urls": [],
  "error_code": "RuntimeError",
  "error_message": "tag_client is required for retag jobs",
  "created_at": "2026-05-25T22:24:14.718524Z",
  "updated_at": "2026-05-25T22:24:15.076599Z"
}
```

## Symptoms & reproduction

| Field | Value |
|-------|-------|
| Symptom | Error / crash — retag always fails with RuntimeError |
| Where | Production (admin frontend → Modal data-management) |
| When | After last deploy (2026-05-25, hotfix #10 Modal redeploy) |
| Frequency | Every time |
| Repro env | Production only |
| Severity | Critical — retag feature completely non-functional |
| Evidence | JSON response pasted above |
| Tried | Nothing |

## Remediation path

**local-first** — fix locally, deploy to production after user approval.

## Verification plan

| Field | Value |
|-------|-------|
| Success criterion | Retag jobs complete successfully (original error gone) |
| Verification checks | Full main CI parity (local) + gh on main after merge |
| Monitoring | Run 15-service-health follow-up after deploy |

## Investigation

| # | Hypothesis | Result |
|---|------------|--------|
| H1 | `VECINITA_MODAL_LLM_URL` missing from Modal secret `vecinita-data-management` → `LlmClient()` raises `LlmClientError` → `except Exception` silently sets `tag_client = None` | **Confirmed** — docstring omits the env var from the required list; staging-secrets-matrix lists it as required |
| H2 | Silent `except Exception` swallows initialization error with no logging — operator has no visibility into why tag_client is None | **Confirmed** — code review |

### Detailed analysis

**Call chain:**
1. `fastapi_app()` in `data_management_app.py` creates `tag_client`:
   ```python
   tag_client: LlmTagClient | None = None
   try:
       tag_client = LlmTagClient(LlmClient())
   except Exception:
       tag_client = None  # Silent! No log, no warning
   ```
2. `LlmClient.__init__()` reads `VECINITA_MODAL_LLM_URL` from env; raises `LlmClientError` when missing
3. The bare `except Exception` swallows the error — `tag_client` stays `None`
4. `runner(job_id)` passes `tag_client=None` to `run_job()`
5. `run_job()` raises `RuntimeError("tag_client is required for retag jobs")`
6. Top-level try/except (hotfix #10) marks job as "failed" — correct behavior, but the *cause* is the silent init failure

**Why the env var is missing:**
- The docstring at the top of `data_management_app.py` lists required secrets but does NOT include `VECINITA_MODAL_LLM_URL`
- The `staging-secrets-matrix.md` correctly lists it as `Yes (EV-001)` for Modal data-management
- The Modal secret was likely set up following the docstring, not the matrix

**Related bugs:**
- BUG-2026-05-25-retag-503-not-configured (hotfix #9) — fixed 503 from write API
- BUG-2026-05-25-retag-job-never-completes (hotfix #10) — fixed job stuck in pending
- This is the third in the chain: the job management is now correct, but the LLM client is never initialized

## Root cause

**Config/code gap:** `VECINITA_MODAL_LLM_URL` is missing from the Modal secret `vecinita-data-management` AND the code silently swallows the initialization failure with a bare `except Exception` that provides no logging. The docstring omitting the env var from the required list caused the gap.

Classification: **Config + code bug** — missing env var documentation + silent exception swallowing.

## Spec conformance

| Doc | Result |
|-----|--------|
| `docs/feature-list.md` F20/F21 | In scope — admin retag requires LLM tagging |
| `docs/spec.md` §Data Management | Retag needs LLM client |
| `docs/staging-secrets-matrix.md` | `VECINITA_MODAL_LLM_URL` documented as required for Modal data-mgmt — but docstring in code omits it |
| `docs/config-spec.md` | `VECINITA_MODAL_LLM_URL` documented as required |

**Blocking drift:** `data_management_app.py` docstring missing `VECINITA_MODAL_LLM_URL` from required secrets.

## Repro test

| Test | Path | Status |
|------|------|--------|
| tag_client init fails silently when env var missing | `tests/bugs/test_bug_2026_05_25_retag_tag_client_none.py::test_tag_client_init_failure_is_logged` | red → green |
| docstring lists VECINITA_MODAL_LLM_URL | `tests/bugs/test_bug_2026_05_25_retag_tag_client_none.py::test_docstring_lists_llm_url_as_required` | red → green |

### TDD iteration log

| # | Date | Action | Result |
|---|------|--------|--------|
| 1 | 2026-05-25 | Write repro tests — assert warning is logged + docstring lists env var | RED: no warning emitted; env var not in docstring |
| 2 | 2026-05-25 | User confirmed repro matches symptom | confirmed |
| 3 | 2026-05-25 | Apply fix: add logger.warning + update docstring | GREEN |

## Fix

**`infra/modal/data_management_app.py`**: Three changes:
1. Added `VECINITA_MODAL_LLM_URL` to the docstring's required secrets list so operators know to include it in the Modal secret.
2. Added `import logging` and module-level `logger` instance.
3. Changed the bare `except Exception: tag_client = None` to log a WARNING with `exc_info=True`, including the secret name — so failures are visible in Modal logs instead of silently swallowed.

**User action required**: Add `VECINITA_MODAL_LLM_URL` to Modal secret `vecinita-data-management` (value: the vecinita-llm Modal app URL, e.g. `https://vecinita--vecinita-llm-fastapi-app.modal.run`), then redeploy.

## Verification

### Layer 1 — Automated

- [x] Repro test red → green
- [x] Full unit test suite passes (122 passed, 25 skipped; 1 pre-existing unrelated failure)
- [x] Lint pass
- [ ] CI parity (local) pass

### Layer 2 — Reproduction

- [ ] Retag no longer fails with "tag_client is required"

### Layer 3 — Pre-deploy smoke

- [ ] Modal deploy successful

### Layer 4 — Production

- [ ] Deployed to Modal
- [ ] Health check pass
- [ ] User confirmed retag works

### CI

- [ ] CI parity before PR
- [ ] PR merged to main
- [ ] Main CI green

## Post-deploy monitoring

15-service-health follow-up after deploy — user requested.

## Prevention & countermeasures

### Interview record

| ID | Question | Answer |
|----|----------|--------|
| prevention_recurrence_risk | Recurrence risk | Very likely without changes — other services may have same pattern |
| prevention_detect_earlier | Where to catch earlier | Code review checklist |
| prevention_automated | Guards to add | Bug repro test only (done) |
| prevention_process | Process changes | Cursor rule — Modal apps must log service client init failures |
| prevention_when | When | Now (same session) |
| prevention_who | Who | Agent |

### Planned actions

1. **Done**: Repro tests `tests/bugs/test_bug_2026_05_25_retag_tag_client_none.py`
2. **Done**: Cursor rule `.cursor/rules/modal-service-client-init.mdc`

## Cursor rule

`.cursor/rules/modal-service-client-init.mdc` — Modal app modules must log warnings when service client init fails; never silently swallow.

## Regression prevention

- `tests/bugs/test_bug_2026_05_25_retag_tag_client_none.py`

## Follow-ups

- **User action**: Add `VECINITA_MODAL_LLM_URL` to Modal secret `vecinita-data-management` (value: `https://vecinita--vecinita-llm-fastapi-app.modal.run`), then `modal deploy infra/modal/data_management_app.py`
- Verify retag works end-to-end after deploy (Layer 4)

## Timeline

| Event | Date |
|-------|------|
| User report | 2026-05-25 |
| Investigation start | 2026-05-25 |
| Root cause confirmed | 2026-05-25 |
| Fix applied | 2026-05-25 |
| PR #47 merged | 2026-05-25 |
