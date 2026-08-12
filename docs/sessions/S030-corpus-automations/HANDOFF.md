# HANDOFF — S030-corpus-automations

**Updated:** 2026-08-07  
**Session:** S030-corpus-automations (`feature`)  
**Cycle:** EV-027 · F75 F76 F77  
**Branch:** `evolve/EV-027-corpus-automations`  
**Issues:** #73 · #72 · #219  

## Position

- Phase C **07-build** in progress — M127 F75
- Done: **T127.1–T127.4** (`d355f29` … `2172d2e`)
- Next: **T127.5** Modal DM `job_type=automation_catchup` worker + concurrency/kill-switch

## Key locks

- F75 catch-up policy: `packages/shared-schemas/.../automations.py`
- Write-API: `GET/PATCH /internal/v1/automations/config`, `GET /internal/v1/automations/runs`
- Alembic `20260807_0015`: `automation_runs` + singleton `automation_settings`
- FT pins locked (S030-D33) for M129: `infra/modal/finetune_pins.py`

## Artifacts

- `tests/unit/shared_schemas/test_automations.py`
- `tests/unit/shared_schemas/test_automations_api_schemas.py`
- `tests/unit/internal_write_api/test_automations_routes.py`
- ADR-052 / ADR-053 · tech-plan-delta · Phase 30 execution-plan

## Open decision

Phase A/B docs/rules/pins still uncommitted on branch — awaiting user choice
(commit as one chore / leave / split).

## Next AskQuestion / stage

Continue **07-build** T127.5 (Modal catch-up worker).
