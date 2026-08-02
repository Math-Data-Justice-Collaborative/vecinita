# Routing plan — S021-retrieval-follow-on (Standard)

| Stage | Required | Status | Mode | Notes |
|-------|----------|--------|------|-------|
| 00-context | yes | completed | scoped | Session open 2026-08-02; S021-D1–D4 |
| 16-evolve | orchestrator | in_progress | — | EV-018; M99 done → M100 |
| 01-requirements | yes | completed | delta | RD-209–218; report `01-requirements-follow-on.md` |
| 02-verify-plan | yes | completed | delta | Gate A→B PASS (S021-D17); report `02-verify-plan-audit.md` |
| 04-tech-plan | yes | completed | delta | TP1–TP6 / S021-D18; Phase 23 M99–M100 |
| 07-build | yes | completed | — | M99–M100 done; AC-BB9 PASS (S021-D24); CE flag still off |
| 08-verify-build | yes | pending | — | next |
| 09-qa | yes | pending | — | |
| 10-e2e | yes | pending | — | |
| 11-verify-impl | yes | pending | — | |
| 12-verify-deploy | yes | pending | — | |
| 13-deploy-smoke | yes | pending | — | |

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

User approval recorded: **2026-08-02** (intake Q1–Q4 = 1,1,1,1).

## Next stage after 00

**16-evolve Phase 0** (Fn allocation + impact + EV-018 create) → then
`@.cursor/skills/01-requirements/SKILL.md` — load
[checkpoints/01-requirements-seed.md](./checkpoints/01-requirements-seed.md) first.

## Ship targets (session open — refine in Phase 0)

| Track | Target |
|-------|--------|
| **Empty retrieve** | Staging golden + sample ChatRAG asks return non-empty `sources` / pools |
| **CE re-gate** | Re-run AC-BB9 / UJ-060 / TC-184; ship #83 only if floors pass |
| **Prod CE flag** | Remain **off** until ship + Path A approval |
