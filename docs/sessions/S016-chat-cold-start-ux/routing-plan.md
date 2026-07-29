# Routing plan — S016-chat-cold-start-ux (Lean+build)

| Stage | Required | Status | Notes |
|-------|----------|--------|-------|
| 00-context | yes | completed | Session open; EV-014 stub; Lean+build approved |
| 16-evolve | yes | in_progress | Orchestrator — Phase A specs written |
| 01-requirements | yes | completed | F40; UJ-052; TC-156–160; AC-CS1–8; ADR-039; RD-183–187 |
| 02-verify-plan | yes | completed | Gate A→B passed (M1–M3 A) |
| 07-build | yes | completed | ChatRAG FE cold-start UX (F40) |
| 08-verify-build | yes | completed | verification-report.md PASS |
| 10-e2e | yes | completed | e2e-report.md PASS (chat Playwright 8/8) |
| 13-deploy-smoke | yes | pending | |

## Skipped

| Stage | Rationale |
|-------|-----------|
| 03-plan-tooling | no new tooling |
| 04-tech-plan | reuse existing FE cold-start patterns (ChatPanel statusMessage) |
| 05-verify-tech | fold into 02/08 |
| 06-tech-tooling | N/A |
| 09-qa | Lean — rely on 08 + 10 |
| 11-verify-impl | Lean — sign-off via 10/13 |
| 12-verify-deploy | Lean — 13-deploy-smoke |

## Preset

**Lean+build** = Lean (`01 → 02 → 10 → 13`) + `07` + `08` (no `04`).
