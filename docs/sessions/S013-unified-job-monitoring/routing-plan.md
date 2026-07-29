# S013 routing plan — Lean+build (S013-D22)

| Stage | Required | Status | Notes |
|-------|----------|--------|-------|
| 00-context | yes | completed | Session open; Phase 0 intake done |
| 16-evolve | yes | in_progress | Orchestrator |
| 01-requirements | yes | completed | RD-173–178; ADR-038 |
| 02-verify-plan | yes | completed | Gate A→B; M1–M3 |
| 04-tech-plan | yes | in_progress | TP-S013-01–08; Phase 19 draft awaiting review |
| 07-build | yes | pending | M82–M85 after 04 approval |
| 08-verify-build | yes | pending | Local verify after build |
| 10-e2e | yes | pending | API e2e + Admin Vitest + Playwright |
| 13-deploy-smoke | yes | pending | After user-approved deploy |

## Skipped

| Stage | Rationale |
|-------|-----------|
| 03-plan-tooling | No new guardrails |
| 05-verify-tech | Lean+build — fold checks into 04/08 |
| 06-tech-tooling | No new runtime deps; Playwright already present |
| 09-qa | Lean+build — rely on 08 + 10 |
| 11-verify-impl | Lean+build — sign-off via 10/13 |
| 12-verify-deploy | Lean+build — 13-deploy-smoke |

## Preset

**Lean+build** = Lean (`01 → 02 → 10 → 13`) + `04` + `07` + `08`.
