# ADR-038: Modal job lifecycle + DO storage SoT (EV-012 / #116)

**Status:** Accepted (2026-07-28)  
**Session:** S013-unified-job-monitoring / EV-012  
**Amends:** [ADR-033](ADR-033-ev008-rag-evaluation-implementation.md) §4 (eval runner placement)  
**Related:** RD-173–RD-178; F32/F36; GitHub #116

## Context

Operators need a unified Admin Jobs experience for all long-running work (ingest, retag, eval,
future types). Eval historically ran on DigitalOcean FastAPI `BackgroundTasks` (ADR-033), while
ingest/retag used Modal. That split prevented a single job lifecycle and complicated monitoring.

## Decision

1. **Modal owns job lifecycle** for all long-running admin jobs, including **eval**
   (`job_type=eval`), using Modal’s async/job-queue patterns
   ([Modal job queue](https://modal.com/docs/guide/job-queue)). Admin Jobs list/detail/CRUD and
   SSE events are served from the Modal data-management jobs API.
2. **DO Postgres** remains the **source of truth for durable storage**, including eval metrics
   and per-row results (`eval_runs`, `eval_run_items`, corpus, etc.).
3. **Supabase** is used for **authentication only** (operator identity/JWT) — not job state or
   metrics storage.
4. **Admin Jobs UI** reads Modal `GET /jobs` as the primary unified list (extensible `job_type`).
   Eval drill-down continues to load metrics from DO via existing internal-write eval APIs.
5. Job status transport: **SSE on Modal jobs and internal-write eval progress** (02-verify M2),
   with **4s poll fallback** and SSE retry backoff (RD-173). Jobs **list** remains Modal-primary.
6. **Admin-only** full job CRUD (cancel/retry/delete); viewer read-only (RD-176).
7. Eval **trigger**: `POST /internal/v1/eval/runs` on DO creates the metrics row and **enqueues**
   Modal `job_type=eval` via `DataManagementJobsClient.enqueue_eval` (02-verify M3, TP-S013-06).
8. **Postgres `jobs` table** is not the job-lifecycle SoT (02-verify M1); DO Postgres stores
   corpus + eval metrics/results only.
9. **JobStore backend:** keep `DictJobStore` + `modal.Dict` for operator-visible lifecycle;
   Modal `.spawn` for work (TP-S013-02). Do not dual-write a Postgres jobs table.
10. **Cancel:** set JobStore `cancelled` and best-effort `FunctionCall.cancel()` when
    `modal_call_id` is known; runners check cancelled before continuing (TP-S013-07).
11. **Delete:** remove Modal JobStore record; when `job_type=eval`, soft-delete linked
    `eval_runs` with `deleted_at` (TP-S013-03/05).
12. **SSE paths:** Modal `GET /jobs/events` for Jobs list; DO
    `GET /internal/v1/eval/runs/{run_id}/events` for Evaluation progress (TP-S013-01/04).

## Consequences

- Amend ADR-033: eval execution moves from DO BackgroundTasks to Modal; persistence of results
  stays on DO Postgres.
- Internal-write may still **trigger** eval (create run row + enqueue Modal job) but must not be
  the async runner of record.
- OpenAPI: extend `openapi/data-management.yaml` for events, cancel/retry/delete, retag
  `document_id`, log metadata; keep eval metrics routes on internal-write.
- Prior S013-D8 “FE merge two job lists” is superseded by Modal-primary list + DO metrics.

## Alternatives considered

| Option | Why not |
|--------|---------|
| Keep eval on DO BackgroundTasks | Blocks unified Modal lifecycle (#116) |
| Postgres as job lifecycle SoT | Conflicts with Modal-primary direction; dual writers |
| FE federation of Modal + eval-run lists | Extra complexity; replaced by Modal `job_type=eval` |
