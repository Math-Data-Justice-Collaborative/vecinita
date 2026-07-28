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
5. Job status transport: **SSE** with **4s poll fallback** and SSE retry backoff (RD-173).
6. **Admin-only** full job CRUD (cancel/retry/delete); viewer read-only (RD-176).

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
