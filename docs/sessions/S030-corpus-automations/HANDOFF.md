# HANDOFF — S030-corpus-automations

**Updated:** 2026-08-12  
**Session:** S030-corpus-automations (`feature`)  
**Cycle:** EV-027 · F75 F76 F77  
**Branch:** `evolve/EV-027-corpus-automations`  
**Issues:** #73 · #72 · #219  

## Position

- Phase C **07-build** in progress — M127 F75
- Done: **T127.1–T127.7**
- Next: **T127.8** DM Automations UI — enable/disable + run history

## Key locks

- F75 catch-up policy + `enqueue_catchup_targets`: shared-schemas automations
- Write-API: config/runs + CRUD hook after batch upsert
- Modal DM: `automation_catchup` worker + job-completion triggers
- Shared schedule: `daily_corpus_automations` with `schedule=modal.Period(days=1)`
  (catch-up + freshness stub; F76 fills freshness in M128)
- FT pins locked (S030-D33) for M129: `infra/modal/finetune_pins.py`

## Next

Continue **07-build** T127.8 (DM Automations UI).
