# HANDOFF — S030-corpus-automations

**Updated:** 2026-08-12  
**Session:** S030-corpus-automations (`feature`)  
**Cycle:** EV-027 · F75 F76 F77  
**Branch:** `evolve/EV-027-corpus-automations`  
**Issues:** #73 · #72 · #219  

## Position

- Phase C **07-build** in progress — **M129 F77** in progress
- Done: **T129.1** @`67ac92b` · **T129.2** @`0fff625` · **T129.3** scaffold `finetune_app.py`
- **Active:** **T129.4** — `job_type=finetune_train` + `POST /jobs/{id}/approve`
- PR [#238](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/238) open

## Key locks

- FT pins: `infra/modal/finetune_pins.py` (S030-D33)
- FT app: `infra/modal/finetune_app.py` / `vecinita-llm-finetune` / `llm-finetune-adapters` (T129.3)
- Not `src/finetune/` (F8)

## Next

**T129.4** — wire `job_type=finetune_train` + admin JWT `POST /jobs/{id}/approve` (TP6 / api-contract). Leave PR #238 open.
