# 01-requirements — EV-018 Retrieval follow-on (S021)

> **Status:** completed (delta) · **Date:** 2026-08-02  
> **Features:** F46, F45 (re-gate) · **Decisions:** S021-D9–D16 · **RD:** RD-209–RD-218

## Seed

Loaded `checkpoints/01-requirements-seed.md`. Locked L1–L14 approved (D16). Open Q1–Q4
resolved (D13–D15); Q5 ordering already D9.

## Document manifest (written)

| Document | Delta |
|----------|-------|
| `docs/feature-list.md` | F46 Planned; F45 EV-018 re-gate note (Phase 0 + confirm) |
| `docs/spec.md` | F46 retrieve reliability + F45 re-gate prereq; changelog |
| `docs/config-spec.md` | **No change** — knobs may adjust in 04/07 without new env at 01 |
| `docs/api-contract.md` | **No change** — no new endpoints at 01 |
| `docs/user-journeys.md` | UJ-061; UJ-060 preconditions require F46 |
| `docs/test-plan.md` | TC-185–186; UJ map; thresholds; TC-184 prereq |
| `docs/acceptance-criteria.md` | AC-FO1–FO5; AC-BB9 prereq note |
| `docs/decisions.md` | RD-209–RD-218 |
| `docs/decisions/evolve-decisions.md` | §EV-018 D13–D16 |

**No new ADR** this stage — diagnose/fix may amend config or add BUG under 07 without
architecture change. OpenAPI unchanged.

## Fn summary

| Fn | Ship intent |
|----|-------------|
| F46 | Restore non-empty staging retrieve pools / ask sources |
| F45 | Re-run CE ship gate after F46; prod CE only if AC-BB9 |

## Test requirements (for 07-build)

| Layer | Artifact |
|-------|----------|
| API e2e | `tests/e2e/test_uj061_retrieve_nonempty.py` (TC-185/186) |
| Unit | Retrieve helpers / knobs as root cause dictates |
| Staging | UJ-061 evidence in session report before UJ-060 |
| UI e2e | None (no browser journey change) |
| Bug | Optional `BUG-*-empty-retrieve` only if code repro in 07 |

## Next

**02-verify-plan** — consistency + statement audit on changed sections.
