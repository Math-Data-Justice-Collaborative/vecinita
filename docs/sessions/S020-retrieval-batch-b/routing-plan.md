# Routing plan — S020-retrieval-batch-b (Standard)

| Stage | Required | Status | Notes |
|-------|----------|--------|-------|
| 00-context | yes | completed | Session open 2026-08-02; S020-D1–D3 |
| 16-evolve | orchestrator | in_progress | EV-017 Phase B — Gate B→C then 07-build |
| 01-requirements | yes | completed | Delta specs F43–F45; RD-197–208; report `01-requirements-batch-b.md` |
| 02-verify-plan | yes | completed | Consistency clean; M1–M4 via S020-D15 |
| 04-tech-plan | yes | completed | Phase 22 M94–M98 + ADR-042; Gate B→C (S020-D18) |
| 07-build | yes | completed | Phase 22 M94–M98 @ `59edd12` / state sync `ccc82df` |
| 08-verify-build | yes | completed | PASS scoped — `reports/verification-report.md` |
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
