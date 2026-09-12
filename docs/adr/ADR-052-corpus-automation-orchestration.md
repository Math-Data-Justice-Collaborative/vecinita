# ADR-052: Corpus automation orchestration (triggers + schedule)

**Status:** Accepted (04-tech-plan — S030/EV-027; TP2–TP3); **amended EV-038** (hardening)  
**Date:** 2026-08-07 (amendment 2026-09-11)  
**Related:** F78, F79 (product IDs; legacy docs may say F75/F76 for the same behaviors),
RD-325–329, RD-334–337; GitHub #73 #219; TP-S030-01–03; EV-038  
**Corpus:** [Corpus: feature-list.md §F78] [Corpus: feature-list.md §F79] [Corpus: adr]

## Context

Corpus changes and freshness today require manual follow-up. Issue #73 needs
downstream automation on change; #219 needs scheduled source refresh. We need one
orchestration model that is idempotent, cost-capped, and observable in the DM UI.

## Decision

1. **Triggers (F78):** (a) job completion (ingest/crawl/retag), (b) document
   add/edit/delete hooks that **enqueue** async Modal jobs (idempotent key =
   `document_id` + `revision`), (c) cron catch-up for failed/partial/missing-embed
   work — **not** re-embed when already complete (S030-D16).
2. **Schedule:** **One** scheduled function on Modal app **`vecinita-data-management`**
   via `@app.function(schedule=modal.Period(days=1))` (daily; calendar-aware —
   preferred over `hours=24`), dispatching **two job types** — F78
   `automation_catchup` and F79 `freshness_refresh` (S030-D18 / TP2 / S030-D31 M2).
   Distinct enable flags still apply.
3. **F79 freshness:** Re-fetch/re-crawl registered URL sources; default stale
   threshold **30 days** (S030-D19); respect `content_hash` skip; bump
   `last_checked_at` even when unchanged; document fields `refresh_enabled`,
   `last_checked_at` (TP7); operator enable/disable + “Refresh now”.
4. **Guardrails:** Global kill-switch + F78 concurrency caps (S030-D11 / RD-328).
5. **Observability:** Automation run history in Postgres table **`automation_runs`**
   via write-API (S030-D23 / TP3); DM UI shows status, last run, errors +
   enable/disable (S030-D8).
6. **Out of scope:** #192 full dashboard widgets; auto F41 rebuild on every change.

### Amendment EV-038 — reliability hardening (2026-09-11)

Keep Decision 1–6. Close implementation gaps that inflate failure rates without
changing product intent:

| Slice | Requirement |
|-------|-------------|
| **A — Residual cron** | Daily `automation_catchup` tick **scans** residual embed states (`missing` / `partial` / `failed`) and enqueues catch-up work subject to caps — not history-only (`record_scheduled_catchup_tick` alone is insufficient vs Decision 1c / AC-AU4). |
| **B — Enqueue-time gates** | Job-completion and CRUD enqueue paths must pass **real** `seen_keys` and `running_count` into `decide_catchup_enqueue` (not empty/`0` defaults that bypass idempotency and concurrency). |
| **C — Freshness caps + WAF quarantine** | Scheduled freshness enqueue is **batched/capped** (`VECINITA_FRESHNESS_MAX_ENQUEUE_PER_TICK`, default **25**). Persistent scrape `host_waf_blocked` / hard 403 → **quarantine** (skip + record; no unbounded retry storm). |
| **D — Failures visible** | Failed self-enqueue or `automation_runs` persist must surface as job/`automation_runs` status or metrics — not warn-only silence that looks like a green tick. |
| **E — Transient auto-retry** | Bounded job-level auto-retry for **transient** embed/transport errors only (`VECINITA_AUTOMATION_JOB_MAX_RETRIES`, default **2**). Do **not** auto-retry hard WAF/quarantine or kill-switch blocks. Manual `POST /jobs/{id}/retry` remains. |

**Success evidence:** Staging before/after failure rates from `automation_runs` + job
statuses (≥7d window when available); quarantined WAF counted separately from transient
failures (AC-AU8–AU12, AC-FR8–FR9; TC-341–346).

**Prod:** Live prod knobs / enable flips still AskQuestion-gated
([Corpus: no-live-prod-corpus-push]).

## Consequences

- Shared schedule reduces Modal cron sprawl; job-type dispatch must be explicit.
- Write-API schema for `automation_runs` is required for DM UI.
- Catch-up-only residual work avoids duplicate embed cost on healthy ingest.
- **Implemented** in Phase 30 / S030 07-build (M127–M128 + M130 OpenAPI/secrets);
  live prod enable remains AskQuestion-gated (TP9 / 13).
- **EV-038:** Residual cron + enqueue gates + freshness caps close the gap between
  Decision 1c and the history-only tick; quarantine reduces false failure rate from WAF hosts.

## Alternatives considered

| Option | Why rejected |
|--------|----------------|
| Sync CRUD in write API | Blocks request path; harder retries |
| Two Modal schedules | More ops surface; duplicate enable flags |
| Cron-only (no live hooks) | Stale lag for operator edits |
| Sub-daily period | Cost; daily `Period(days=1)` sufficient with 30d stale default |
| `@modal.periodic` / `Period(hours=24)` | Prefer documented SDK form `schedule=modal.Period(days=1)` (S030-D31 M2) |
| Unlimited freshness enqueue per tick | Amplifies WAF/403 failure storms (EV-038) |
| Auto-retry all failures including WAF | Burns quota; quarantine is correct for hard blocks (EV-038) |
