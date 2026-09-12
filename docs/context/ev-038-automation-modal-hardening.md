# Context — EV-038 automation / Modal job hardening

**Session:** `EV-038-automation-modal-hardening`  
**Date:** 2026-09-11  
**Mode:** scoped evolve  
**Local session:** `~/.cursor/workflow/Math-Data-Justice-Collaborative/vecinita/sessions/EV-038-automation-modal-hardening`

## Problem

F78/F79 automations are live (EV-031) but job failure rates remain higher than desired.
Guardrails (kill-switch, enable flags, residual-only catch-up, hash skip) are solid at
decision time; resilience gaps sit in schedule/enqueue scale, residual cron, weak enqueue
dedupe/caps, swallowed enqueue failures, and no job-level auto-retry beyond embed/scrape.

## Prior art (do not redo)

| Artifact | Outcome |
|----------|---------|
| EV-027 + ADR-052 | Shared daily Modal schedule; catch-up + freshness job types; `automation_runs` |
| EV-031 | Live enable F78/F79 on staging/prod (ops) |
| F48 | Embed sub-batch + retry (already on embed path) |
| #249 / scrape WAF | 403 / `host_waf_blocked` — documented staging pain |
| BUG-2026-08-28 | `hash_decision` metrics schema forbid → GET /jobs 500 |
| BUG-2026-09-09 | Stuck pending jobs after Modal spawn/enqueue failure |
| BUG-2026-05-22 | Modal DM container crash → 504 |

## Reliability findings (context scan)

1. Freshness daily tick can enqueue many stale docs with no freshness concurrency cap; WAF/403s amplify failure rate.
2. Scheduled catch-up tick records history only — does **not** scan residuals (`record_scheduled_catchup_tick`).
3. Enqueue hooks often pass empty `seen_keys` / `running_count=0` → duplicate/over-cap bursts.
4. Best-effort enqueue + history persist can fail silently (warn-only).
5. No automatic job retry for failed F78/F79 jobs (manual `POST /jobs/{id}/retry` only).

## Code anchors

- `infra/modal/data_management_app.py` — `daily_corpus_automations`, `process_dm_job`
- `apps/data-management-backend/.../automation_catchup.py`, `freshness_refresh.py`, `schedule_catchup.py`, `catchup_triggers.py`
- `packages/shared-schemas/.../automations.py`, `freshness.py`
- `packages/embedding-client/.../client.py` — embed retries
- `packages/ingest/.../scrape.py` — WAF/TLS
- Admin: `AutomationsPage.tsx` (history; not primary change target)

## Must-not-break

- Catch-up-only residual policy (no re-embed when complete) — ADR-052
- One shared schedule with distinct `job_type`s
- Kill-switch + cost/concurrency caps
- `DATABASE_URL` only on DO backends (not Modal)
- No live prod corpus mutate without AskQuestion
- Stage-before-main for any shippable PR

## Cross-project memory (F107)

Peer RAG hits (chunking / golden eval) are **waive** for this cycle — not reliability-shaped.
Keep-local: Vecinita bug reports + ADR-052 findings above.

## Next Spec step

`spec-development/requirements` — lock hardening slices (priority order + AC).

## Cites

[Corpus: feature-list.md §F78–F79]
[Spec: docs/adr/ADR-052-corpus-automation-orchestration.md]
[Corpus: staging] [Corpus: config]
