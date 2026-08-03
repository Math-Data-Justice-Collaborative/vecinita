# Routing plan — S025-ci-release-automation (Lean+build)

| Stage | Required | Status | Notes |
|-------|----------|--------|-------|
| 00-context | yes | completed | Session open; EV-023 stub; Lean+build approved |
| 16-evolve | yes | in_progress | Orchestrator — Phase 0 intake |
| 01-requirements | yes | pending | Delta: Fnn for #182 + #103; LOCAL_DEV / AC |
| 02-verify-plan | yes | pending | Consistency on hook + release docs |
| 07-build | yes | pending | Husky scripts + release workflow |
| 08-verify-build | yes | pending | verification-report.md |
| 10-e2e | yes | pending | Hook script smoke / workflow dry-run tests |
| 13-deploy-smoke | yes | pending | Merge to main; confirm CD + tag behavior |

## Skipped

| Stage | Rationale |
|-------|-----------|
| 03-plan-tooling | no new product tooling |
| 04-tech-plan | reuse existing CI/CD patterns; decisions in Phase 0 + RD log |
| 05-verify-tech | fold into 02/08 |
| 06-tech-tooling | N/A |
| 09-qa | Lean — rely on 08 + 10 |
| 11-verify-impl | Lean — sign-off via 10/13 |
| 12-verify-deploy | Lean — 13-deploy-smoke |
| 15-service-health | not product deploy health |

## Preset

**Lean+build** = Lean (`01 → 02 → 10 → 13`) + `07` + `08` (no `04`).

User intent: minimal changes, lean. Lean+build required to ship hook + workflow code.
