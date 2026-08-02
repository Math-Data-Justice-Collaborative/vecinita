# Routing plan — S020-retrieval-batch-b (Standard)

| Stage | Required | Status | Notes |
|-------|----------|--------|-------|
| 00-context | yes | completed | Session open 2026-08-02; S020-D1–D3 |
| 16-evolve | orchestrator | in_progress | EV-017 Phase 0 intake |
| 01-requirements | yes | pending | After Phase 0 scope lock; load seed |
| 02-verify-plan | yes | pending | |
| 04-tech-plan | yes | pending | |
| 07-build | yes | pending | |
| 08-verify-build | yes | pending | |
| 09-qa | yes | pending | |
| 10-e2e | yes | pending | |
| 11-verify-impl | yes | pending | |
| 12-verify-deploy | yes | pending | |
| 13-deploy-smoke | yes | pending | |

## Skipped

| Stage | Rationale |
|-------|-----------|
| 03-plan-tooling | No new tooling expected |
| 05-verify-tech | Fold into 02 / 08 |
| 06-tech-tooling | N/A |
| 15-service-health | Optional at close |

## Preset

**Standard** = Lean (`01 → 02 → 10 → 13`) + `04 → 07 → 08 → 09 → 11 → 12`.

## Next stage after 00

**16-evolve Phase 0** (intake / scope lock) → then
`@.cursor/skills/01-requirements/SKILL.md` — load
[checkpoints/01-requirements-seed.md](./checkpoints/01-requirements-seed.md) first.

## Ship targets (Phase 0 batch 1 — S020-D4–D7)

| Fn | Track | Target |
|----|-------|--------|
| **F43** | Cache | Full H1 cascade (exact → semantic → retrieve → generate) |
| **F44** | #162 | Config-gated L1 (default off) + empty-hit fixture |
| **F45** | #83/#161 | CE spike + ship gate (no prod unless gate passes) |
