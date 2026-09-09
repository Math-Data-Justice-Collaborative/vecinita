# BUG-2026-09-09-stuck-pending-eval-jobs

[Corpus: staging] [Corpus: tests]  
**Found by:** EV-staging-adversarial-plunge (2026-09-09)  
**Status:** fixed — staging orphan pending evals soft-deleted 2026-09-09 via write API  
**Session:** HF-2026-09-09-staging-plunge-findings

## Error description

Staging Data Management Jobs list shows **`job_type=eval`** rows stuck in
**`pending`** with **`modal_call_id: null`**, **`eval_run_id: null`**, and
**`initiated_by_user_id: null`**. They appeared to share the same create timestamp
(same second), so they never appear to spawn a Modal function call.

## Error logs

```text
GET https://vecinita-staging--vecinita-data-management-fastapi-app.modal.run/jobs
(Authorization: staging Supabase admin JWT)

statuses: completed=37 failed=25 pending=16
pending sample:
  job_id=e60d36ef-9654-44a5-8401-f9b7f628fb33
  job_type=eval status=pending
  modal_call_id=null eval_run_id=null
  created_at=2026-09-09T10:44:45.021670Z
  initiated_by_user_id=null initiated_by_role=null

Re-check ~15s later: still pending_eval=16 with_modal=0
```

Evidence: session
`EV-staging-adversarial-plunge/evidence/jobs-list.json` (+ `jobs-list-2.json`).

## Investigation

| Time (UTC) | Note |
|------------|------|
| 2026-09-09 ~10:42–10:45 | Adversarial plunge; admin UI Jobs page showed many Pending Eval |
| 2026-09-09 10:44:45 | 16 eval jobs “created” in one burst (null initiator) |
| HF triage | All eval rows (incl. completed) lack modal_call_id — shape matches `_fetch_eval_jobs` / `eval_run_to_job`, not JobStore |

**Root cause (confirmed):**

1. **Display:** `eval_run_to_job` used `datetime.now()` when `started_at` was null, so pending
   Postgres `eval_runs` looked like a same-second burst; `eval_run_id` was never mapped.
2. **Orphans:** `POST /eval/runs` inserted `pending` then returned 502 on Modal enqueue failure
   **without** marking the run failed.
3. **Dispatch gap:** Modal DM ASGI used FastAPI `BackgroundTasks` instead of Modal `.spawn`
   (ADR-038 / TP-S013-02), so work could be dropped with no `modal_call_id`.

## Repro test

`tests/bugs/test_bug_2026_09_09_stuck_pending_eval_jobs.py` — green after fix.

Also: `tests/unit/modal/test_dm_job_spawn.py`.

## Fix

- `EvalRunListItem.created_at` + durable mapping + `eval_run_id` on Jobs list
- `fail_eval_run_dispatch` on enqueue failure
- `process_dm_job` Modal function + `job_spawner` sets `modal_call_id` (fail closed)

**Ops follow-up:** Staging orphan pending `eval_runs` soft-deleted 2026-09-09 (write API).
Redeploy Modal DM so `process_dm_job.spawn` is live on staging.

## Interview record

Operator requested hotfix for all plunge findings (2026-09-09).
