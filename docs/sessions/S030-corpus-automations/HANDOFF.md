# HANDOFF — S030-corpus-automations

**Updated:** 2026-08-12  
**Session:** S030-corpus-automations (`feature`)  
**Cycle:** EV-027 · F75 F76 F77  
**Branch:** `evolve/EV-027-corpus-automations`  
**Tip:** `7b1aa87` (local; not pushed)  
**Issues:** #73 · #72 · #219  

## Position

- Phase C **07-build** in progress — **M128 F76** (freshness)
- Done: **M127 F75** (T127.1–T127.10) — PR [#238](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/238) open (leave open; no merge)
- Done: **T128.1** — F76 freshness policy helpers + unit tests (TC-256–259) `@92912be`
- Done: **T128.2** — Alembic `documents.refresh_enabled` + `last_checked_at` (reuse `content_hash`) `@7b1aa87`
- Now: **T128.3 in progress** — write-API PATCH/list stale fields; Refresh now → enqueue

## Key locks

- F75 catch-up policy + `enqueue_catchup_targets`: shared-schemas automations
- Write-API: config/runs + CRUD hook after batch upsert
- Modal DM: `automation_catchup` worker + job-completion triggers
- Shared schedule: `daily_corpus_automations` with `schedule=modal.Period(days=1)`
  (catch-up + freshness; F76 fills freshness in M128)
- FT pins locked (S030-D33) for M129: `infra/modal/finetune_pins.py`
- PR #238 CI last green at origin tip `@87cf4d2`; local tip `@7b1aa87` ahead (not pushed)

## Next

Continue **07-build** **T128.3** (write-API PATCH/list stale fields; Refresh now → enqueue for F76/M128). Leave PR #238 open; do not push unless asked.
