# Routing plan — S019-retrieval-quality (Standard)

| Stage | Required | Status | Notes |
|-------|----------|--------|-------|
| 00-context | yes | completed | Session open 2026-07-31; S019-D1–D5 |
| 16-evolve | orchestrator | in_progress | EV-016 Phase 0 — investigation-first |
| 01-requirements | yes | completed | F42 delta specs accepted (S019-D37) |
| 02-verify-plan | yes | completed | F42 audit pass; S019-D42 M1–M3 |
| 04-tech-plan | yes | completed | Phase 21 M91–M93 + ADR-041 |
| 07-build | yes | pending | At most one shipped change |
| 08-verify-build | yes | pending | |
| 09-qa | yes | pending | |
| 10-e2e | yes | pending | API + UI journeys for shipped change |
| 11-verify-impl | yes | pending | |
| 12-verify-deploy | yes | pending | |
| 13-deploy-smoke | yes | pending | |
| 15-service-health | no | pending | Optional at close |

## Skipped

| Stage | Rationale |
|-------|-----------|
| 03-plan-tooling | No new tooling |
| 05-verify-tech | Fold into 02 / 08 |
| 06-tech-tooling | N/A |

## Preset

**Standard** = Lean (`01 → 02 → 10 → 13`) + `04 → 07 → 08 → 09 → 11 → 12`.

## Shape note

**Investigation before Fn allocation** (S019-D4): F36 spike + hybrid sweep done;
`feature_ids`: **F42** = H7+P1 (S019-D31). Enter Phase A after `phase0_approved`.
F43 cache / es relevancy later; LangGraph needs ADR-006 amend (deferred D27).
