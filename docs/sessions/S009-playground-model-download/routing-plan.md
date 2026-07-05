# Routing plan — S009-playground-model-download

| Stage | Required | Mode | Skip rationale |
|-------|----------|------|----------------|
| 00-context | yes | scoped | This session — F38 model download interview |
| 01-requirements | yes | delta | F38 feature definition + UJ/TC/AC |
| 04-tech-plan | yes | delta | Auth change, UI wire-up, test matrix |
| 07-build | yes | delta | API auth + playground download UI + tests |
| 08-verify-build | yes | full | Milestone verify |
| 09-qa | yes | full | CI parity |
| 10-e2e | yes | full | UJ + Playwright for download flow |
| 11-verify-impl | yes | full | Impl signoff |
| 12-verify-deploy | yes | full | Pre-deploy checklist |
| 13-deploy-smoke | yes | full | Staging smoke |
| 02-verify-plan | no | — | evolve-lite — user approved 2026-07-05 |
| 03-plan-tooling | no | — | evolve-lite |
| 05-verify-tech | no | — | evolve-lite |
| 06-tech-tooling | no | — | evolve-lite |

## Build order (proposed milestones)

1. M71 — API auth: super-admin-only pull; admin denied on pull; list unchanged
2. M72 — Playground download UI + poll-until-available
3. M73 — Full-stack tests (integration, Vitest, e2e, Playwright)

## Handoff from S008

S008 **parked** at 09-qa with open coverage gate (internal-write-api). Branch
`feat/S008-eval-ux-playground` remains for follow-up PR; S009 branches from `main` (or current
deploy baseline — confirm at 07-build).

## Approved

User approval recorded: 2026-07-05 (routing_plan_s009 = evolve_lite)
