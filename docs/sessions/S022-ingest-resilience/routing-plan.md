# Routing plan — S022-ingest-resilience (Standard)

| Stage | Required | Status | Mode | Notes |
|-------|----------|--------|------|-------|
| 00-context | yes | completed | scoped | Session open 2026-08-02; S022-D1–D7 |
| 16-evolve | orchestrator | in_progress | — | EV-019; F47–F49 |
| 01-requirements | yes | pending | delta | Load [checkpoints/01-requirements-seed.md](./checkpoints/01-requirements-seed.md) |
| 02-verify-plan | yes | pending | delta | Consistency + changed-section audit |
| 04-tech-plan | yes | pending | delta | Tasks / milestone(s) on shared write/embed path |
| 07-build | yes | pending | — | Investigate→ship per Fn |
| 08-verify-build | yes | pending | — | Milestone gate |
| 09-qa | yes | pending | — | Full QA |
| 10-e2e | yes | pending | — | API + admin ingest journeys |
| 11-verify-impl | yes | pending | — | Per-Fn AC sign-off |
| 12-verify-deploy | yes | pending | — | Deploy checklist |
| 13-deploy-smoke | yes | pending | — | H1–H5 + ingest smokes |

## Skipped

| Stage | Rationale |
|-------|-----------|
| 03-plan-tooling | No new Cursor rules/hooks expected at open |
| 05-verify-tech | Fold into 02 / 08 unless tech plan adds ambiguity |
| 06-tech-tooling | No new tooling install expected |
| 15-service-health | Optional at close |

## Preset

**Standard** = Lean (`01 → 02 → 10 → 13`) + `04 → 07 → 08 → 09 → 11 → 12`.

## Approved

User answers **2026-08-02**: Q1–Q4 = `1, 1, 1, 1`
(Standard · include #160 · investigate→ship · continue with recommended).

## Next stage after 00

**16-evolve Phase 0/1** (Fn + EV-019) → then
`@.cursor/skills/01-requirements/SKILL.md` — load
[checkpoints/01-requirements-seed.md](./checkpoints/01-requirements-seed.md) first.

## Ship targets (session open — refine in Phase 0 / 01)

| Track | Target |
|-------|--------|
| **F47 content_hash skip** | Unchanged URL hash → skip chunk delete + re-embed; `force` path for operators |
| **F48 embed resilience** | Sub-batch + retry on transient embed failures; clear fail/partial policy |
| **F49 chunk overlap** | Configured overlap (+ sizing clarity); document re-ingest if required |
