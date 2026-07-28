# S013 routing plan — Lean+build (S013-D22)

| Stage | Required | Status | Notes |
|-------|----------|--------|-------|
| 00-context | yes | completed | Session open; Phase 0 intake done |
| 16-evolve | yes | in_progress | Orchestrator; Phase 1 impact → then child stages |
| 01-requirements | yes | pending | Delta F32/F36 + #116 ACs |
| 02-verify-plan | yes | pending | Consistency pass on touched specs |
| 04-tech-plan | yes | pending | SSE, federation, Postgres/cancel/logs |
| 07-build | yes | pending | Admin FE + Modal DM + internal-write |
| 08-verify-build | yes | pending | Local verify after build |
| 10-e2e | yes | pending | API e2e + Admin Vitest; extend UJ-023 |
| 13-deploy-smoke | yes | pending | After user-approved deploy |

## Skipped

| Stage | Rationale |
|-------|-----------|
| 03-plan-tooling | No new guardrails expected |
| 05-verify-tech | Lean+build — fold checks into 04/08 |
| 06-tech-tooling | No new deps/hooks expected (confirm in 04) |
| 09-qa | Lean+build — rely on 08 + 10 |
| 11-verify-impl | Lean+build — user sign-off via 10/13 + checkpoints on request |
| 12-verify-deploy | Lean+build — 13-deploy-smoke covers staging smoke |

## Preset

**Lean+build** = Lean (`01 → 02 → 10 → 13`) + `04` + `07` + `08`.
