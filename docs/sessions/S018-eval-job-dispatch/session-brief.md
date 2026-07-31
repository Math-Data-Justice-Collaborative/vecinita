# S018 — Hotfix: Modal eval job dispatch

| Field | Value |
|-------|--------|
| **Type** | hotfix |
| **Intent** | Admin Evaluation enqueues Modal `job_type=eval`, but `run_job` falls through to ingest and fails |
| **Bug** | [BUG-2026-07-31-eval-job-dispatch](../../bug-reports/BUG-2026-07-31-eval-job-dispatch.md) |
| **Branch** | `fix/S018-eval-job-dispatch` |
| **Interview** | New bug; both staging+production; medium; path A (wire `run_job` → eval); include top_k/`max_model_len` |

## Scope

- Dispatch `job_type=eval` in Modal `run_job` to an eval worker (not ingest).
- Modal worker triggers DO write-api execute (no `DATABASE_URL` on Modal — ADR-007).
- Pass adhoc `question` through enqueue options when present.
- Cap eval synthesis context so default `top_k=5` + 256-token chunks do not exceed vLLM `max_model_len=2048`.

## Out of scope

- Redesigning eval metrics storage; ChatRAG production `top_k`; full corpus backfill.
