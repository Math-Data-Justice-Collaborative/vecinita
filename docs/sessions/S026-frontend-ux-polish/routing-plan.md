# Routing plan — S026-frontend-ux-polish (Standard)

| Stage | Required | Status | Notes |
|-------|----------|--------|-------|
| 00-context | yes | completed | Session open; intake locked; Standard approved |
| 16-evolve | yes | in_progress | Orchestrator — Phase 0 Fn allocation next |
| 01-requirements | yes | pending | Delta: Fnn × 6 issues; privacy for #186; energy heuristic AC |
| 02-verify-plan | yes | pending | Consistency across FE + API deltas |
| 04-tech-plan | yes | pending | Execution plan + milestones; PR-per-issue strategy |
| 05-verify-tech | yes | pending | Tech gate before build |
| 07-build | yes | pending | Six atomic PR streams on evolve branch |
| 08-verify-build | yes | pending | verification-report.md |
| 09-qa | yes | pending | qa-report.md |
| 10-e2e | yes | pending | API + UI e2e per e2e-coverage.mdc |
| 11-verify-impl | yes | pending | Per-Fn AC; UI preview AskQuestion |
| 12-verify-deploy | yes | pending | Deploy checklist |
| 13-deploy-smoke | yes | pending | Merge PRs; H0ci; H4–H5 |

## Skipped

| Stage | Rationale |
|-------|-----------|
| 03-plan-tooling | No new linters/CI frameworks; reuse existing FE stack |
| 06-tech-tooling | No new hooks/tooling beyond existing |
| 15-service-health | Optional after deploy; not in default Standard |

## Preset

**Standard** = Lean + `04 → 07 → 08 → 09 → 11 → 12` (plus `05` for tech gate).

Connectivity: browser UI → gates 01/04 delta, 07, 12–13 with H4–H5 when UI ships.
