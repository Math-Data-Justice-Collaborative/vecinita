# Routing plan — S028-chat-source-ux (feature preset)

Approved: **S028-D1** (1a / 2a). Prod-careful: **S028-D2**.

| Stage | Required | Status | Notes |
|-------|----------|--------|-------|
| 00-context | yes | completed | Phase 0 session open 2026-08-06 |
| 01-requirements | yes | completed | delta; RD-309–321; report set |
| 02-verify-plan | yes | completed | S028-D20; Gate A→B pass |
| 04-tech-plan | yes | completed | S028-D23 Phase 29 approved |
| 05-verify-tech | yes | completed | S028-D24 M1/M2/L1; Gate B→C AskQ |
| 07-build | yes | completed | M123–M126; ADR-051 Accepted |
| 08-verify-build | yes | completed | verification-report.md PASS |
| 09-qa | yes | completed | qa-report.md — pass_with_advisories |
| 10-e2e | yes | pending | e2e-report.md |
| 11-verify-impl | yes | pending | AC sign-off |
| 12-verify-deploy | yes | pending | **AskQuestion before prod** (S028-D2) |
| 13-deploy-smoke | yes | pending | **AskQuestion before prod** (S028-D2) |

## Orchestrator

| Stage | Required | Status | Notes |
|-------|----------|--------|-------|
| 16-evolve | yes | in_progress | EV-026; Phase C build done → Gate C→D / 08 |

## Skipped

| Stage | Rationale |
|-------|-----------|
| 03-plan-tooling | no new guardrails expected (reconfirm Phase 1 / RD-319) |
| 06-tech-tooling | no new deps (T126.2 inventory confirm) |

## Preset

**Feature** = `00 → 01 → 02 → 04 → 05 → 07 → 08 → 09 → 10 → 11 → 12 → 13` with 03/06 skipped.
Orchestrator: **16-evolve**.

## Next

**08-verify-build** (Gate C→D). H4–H5 live smoke only at 13 after AskQuestion (S028-D2).
