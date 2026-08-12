# ADR-052: Corpus automation orchestration (triggers + schedule)

**Status:** Accepted (04-tech-plan — S030/EV-027; TP2–TP3)  
**Date:** 2026-08-07  
**Related:** F75, F76, RD-325–329, RD-334–337; GitHub #73 #219; TP-S030-01–03  
**Corpus:** [Corpus: feature-list.md §F75] [Corpus: feature-list.md §F76] [Corpus: adr]

## Context

Corpus changes and freshness today require manual follow-up. Issue #73 needs
downstream automation on change; #219 needs scheduled source refresh. We need one
orchestration model that is idempotent, cost-capped, and observable in the DM UI.

## Decision

1. **Triggers (F75):** (a) job completion (ingest/crawl/retag), (b) document
   add/edit/delete hooks that **enqueue** async Modal jobs (idempotent key =
   `document_id` + `revision`), (c) cron catch-up for failed/partial/missing-embed
   work — **not** re-embed when already complete (S030-D16).
2. **Schedule:** **One** scheduled function on Modal app **`vecinita-data-management`**
   via `@app.function(schedule=modal.Period(days=1))` (daily; calendar-aware —
   preferred over `hours=24`), dispatching **two job types** — F75
   `automation_catchup` and F76 `freshness_refresh` (S030-D18 / TP2 / S030-D31 M2).
   Distinct enable flags still apply.
3. **F76 freshness:** Re-fetch/re-crawl registered URL sources; default stale
   threshold **30 days** (S030-D19); respect `content_hash` skip; bump
   `last_checked_at` even when unchanged; document fields `refresh_enabled`,
   `last_checked_at` (TP7); operator enable/disable + “Refresh now”.
4. **Guardrails:** Global kill-switch + F75 concurrency caps (S030-D11 / RD-328).
5. **Observability:** Automation run history in Postgres table **`automation_runs`**
   via write-API (S030-D23 / TP3); DM UI shows status, last run, errors +
   enable/disable (S030-D8).
6. **Out of scope:** #192 full dashboard widgets; auto F41 rebuild on every change.

## Consequences

- Shared schedule reduces Modal cron sprawl; job-type dispatch must be explicit.
- Write-API schema for `automation_runs` is required for DM UI.
- Catch-up-only residual work avoids duplicate embed cost on healthy ingest.

## Alternatives considered

| Option | Why rejected |
|--------|----------------|
| Sync CRUD in write API | Blocks request path; harder retries |
| Two Modal schedules | More ops surface; duplicate enable flags |
| Cron-only (no live hooks) | Stale lag for operator edits |
| Sub-daily period | Cost; daily `Period(days=1)` sufficient with 30d stale default |
| `@modal.periodic` / `Period(hours=24)` | Prefer documented SDK form `schedule=modal.Period(days=1)` (S030-D31 M2) |
