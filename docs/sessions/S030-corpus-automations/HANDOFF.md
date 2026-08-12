# HANDOFF — S030-corpus-automations

**Updated:** 2026-08-12  
**Session:** S030-corpus-automations (`feature`)  
**Cycle:** EV-027 · F75 F76 F77  
**Branch:** `evolve/EV-027-corpus-automations`  
**Issues:** #73 · #72 · #219  

## Position

- Phase C **07-build** in progress — M127 F75
- Done: **T127.1–T127.5** (Phase A/B docs `3cadd8b`; T127.5 next tip)
- Next: **T127.6** triggers — job completion + doc CRUD enqueue (async only)

## Key locks

- F75 catch-up policy: `packages/shared-schemas/.../automations.py`
- Write-API: `GET/PATCH /internal/v1/automations/config`, `GET /internal/v1/automations/runs`
- Alembic `20260807_0015`: `automation_runs` + singleton `automation_settings`
- Modal DM worker: `job_type=automation_catchup` → `run_automation_catchup_job`
  (kill-switch + `VECINITA_AUTOMATIONS_MAX_CONCURRENT`; catch-up-only skips complete)
- FT pins locked (S030-D33) for M129: `infra/modal/finetune_pins.py`

## Artifacts

- `tests/unit/shared_schemas/test_automations.py`
- `tests/unit/shared_schemas/test_automations_api_schemas.py`
- `tests/unit/internal_write_api/test_automations_routes.py`
- `tests/unit/data_management/test_automation_catchup.py`
- `apps/data-management-backend/.../automation_catchup.py`
- ADR-052 / ADR-053 · tech-plan-delta · Phase 30 execution-plan

## Next AskQuestion / stage

Continue **07-build** T127.6 (enqueue triggers).
