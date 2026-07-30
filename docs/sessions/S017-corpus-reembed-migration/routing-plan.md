# Routing plan — S017-corpus-reembed-migration (Standard+build)

| Stage | Required | Status | Notes |
|-------|----------|--------|-------|
| 00-context | yes | completed | Session open; Standard+build approved |
| 16-evolve | yes | in_progress | Orchestrator — EV-015 Phase A |
| 01-requirements | yes | completed | F41 delta specs + ADR-040 |
| 02-verify-plan | yes | completed | Gate A→B PASS 2026-07-30; M1–M6 |
| 04-tech-plan | yes | completed | TP-S017-01–09; Phase 20; Gate B→C PASS |
| 07-build | yes | in_progress | Phase 20 M86 done → M87 |
| 08-verify-build | yes | pending | verification-report.md |
| 09-qa | yes | pending | Standard includes QA |
| 10-e2e | yes | pending | API (+ UI if admin trigger) |
| 11-verify-impl | yes | pending | Per-AC sign-off |
| 12-verify-deploy | yes | pending | Staging deploy verify |
| 13-deploy-smoke | yes | pending | Staging smoke → prod cutover policy |

## Skipped

| Stage | Rationale |
|-------|-----------|
| 03-plan-tooling | No new tooling beyond existing Modal / admin / internal-write patterns |
| 05-verify-tech | Fold into 02 / 08 |
| 06-tech-tooling | N/A |

## Preset

**Standard+build** = Lean (`01 → 02 → 10 → 13`) + `04 → 07 → 08 → 09 → 11 → 12`.

## Scope note

User chose option 3 at session open: implement rebuild now (expands #167 beyond
investigation-only acceptance). Phase 0 still confirms rebuild modes and operator UX.
