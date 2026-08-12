# HANDOFF — S030-corpus-automations

**Updated:** 2026-08-12  
**Session:** S030-corpus-automations (`feature`)  
**Cycle:** EV-027 · F75 F76 F77  
**Branch:** `evolve/EV-027-corpus-automations`  
**Tip:** `fdf68af` (pushed to origin) — T128.5 done; **T128.6 in progress**; watching PR #238 CI  
**Issues:** #73 · #72 · #219  

## Position

- Phase C **07-build** in progress — **M128 F76** (freshness)
- Done: **M127 F75** (T127.1–T127.10) — PR [#238](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/238) open (leave open; no merge)
- Done: **T128.1** — F76 freshness policy helpers + unit tests (TC-256–259)
- Done: **T128.2** — Alembic `documents.refresh_enabled` + `last_checked_at` (reuse `content_hash`) `@7b1aa87`
- Done: **T128.3** — write-API PATCH/list stale fields; Refresh now → enqueue `@e86290e`
- Done: **T128.4** — Modal `freshness_refresh` worker + schedule `@ac8fca7`; coverage/typecheck follow-up `@2bf2dca`
- Done: **T128.5** — ingest/hash-aware re-fetch for URL sources `@fdf68af` (pushed; CI watching)
- **In progress: T128.6** — DM freshness UI (stale list, enable, Refresh now)

## Key locks

- F75 catch-up policy + `enqueue_catchup_targets`: shared-schemas automations
- Write-API: config/runs + CRUD hook after batch upsert; mark-checked bump
- Modal DM: `automation_catchup` + `freshness_refresh` workers; job-completion triggers
- Shared schedule: `daily_corpus_automations` with `schedule=modal.Period(days=1)`
  (catch-up tick + real freshness enqueue for stale `refresh_enabled` docs)
- Hash-aware freshness re-fetch: `packages/ingest` + `freshness_refresh` / `rechunk_and_upsert_scraped_url`
- FT pins locked (S030-D33) for M129: `infra/modal/finetune_pins.py`
- PR #238 open; tip `fdf68af` pushed — keep CI green

## Next

Continue **07-build** **T128.6** (DM freshness UI — stale list, enable, Refresh now). Leave PR #238 open; do not merge without approval.
