# Routing plan — S028-chat-source-ux (feature preset)

Approved: **S028-D1** (1a / 2a). Prod-careful: **S028-D2**.

| Stage | Required | Status | Notes |
|-------|----------|--------|-------|
| 00-context | yes | completed | Phase 0 session open 2026-08-06 |
| 01-requirements | yes | completed | delta; RD-309–321; report set |
| 02-verify-plan | yes | completed | S028-D20; Gate A→B pass |
| 04-tech-plan | yes | completed | S028-D23 Phase 29 approved |
| 05-verify-tech | yes | completed | S028-D24 M1/M2/L1; Gate B→C AskQ |
| 07-build | yes | pending | |
| 08-verify-build | yes | pending | verification-report.md |
| 09-qa | yes | pending | qa-report.md |
| 10-e2e | yes | pending | e2e-report.md |
| 11-verify-impl | yes | pending | AC sign-off |
| 12-verify-deploy | yes | pending | **AskQuestion before prod** (S028-D2) |
| 13-deploy-smoke | yes | pending | **AskQuestion before prod** (S028-D2) |

## Orchestrator

| Stage | Required | Status | Notes |
|-------|----------|--------|-------|
| 16-evolve | yes | in_progress | EV-026; Phase A done → Phase B |

## Skipped

| Stage | Rationale |
|-------|-----------|
| 03-plan-tooling | no new guardrails expected (reconfirm Phase 1 / RD-319) |
| 06-tech-tooling | no new deps expected (reconfirm Phase 1) |

## Preset

**Feature** = `00 → 01 → 02 → 04 → 05 → 07 → 08 → 09 → 10 → 11 → 12 → 13` with 03/06 skipped.
Orchestrator: **16-evolve**.

## Next

**Gate B→C** AskQuestion → **07-build** (06 skipped). First task **T123.1**.
