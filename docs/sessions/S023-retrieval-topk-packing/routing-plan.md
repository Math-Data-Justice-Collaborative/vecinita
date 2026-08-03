# Routing plan — S023-retrieval-topk-packing (Standard)

| Stage | Required | Status | Mode | Notes |
|-------|----------|--------|------|-------|
| 00-context | yes | completed | scoped | Session open 2026-08-02; S022 closed first |
| 16-evolve | orchestrator | pending | — | EV-020 Phase 0 → Fn allocate |
| 01-requirements | yes | completed | delta | Report: [01-requirements-topk-packing.md](./reports/01-requirements-topk-packing.md) |
| 02-verify-plan | yes | pending | delta | Gate A→B |
| 04-tech-plan | yes | completed | delta | Gate B→C PASS (S023-D12) |
| 07-build | yes | in_progress | — | T105.1 · Phase 25 M105–M107 |
| 08-verify-build | yes | pending | — | Milestone gate |
| 09-qa | yes | pending | — | Full QA |
| 10-e2e | yes | pending | — | ChatRAG retrieve/ask journeys |
| 11-verify-impl | yes | pending | — | Per-Fn AC |
| 12-verify-deploy | yes | pending | — | Deploy checklist |
| 13-deploy-smoke | yes | pending | — | H1–H5 + DO `VECINITA_TOP_K` / packer |

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

User answers **2026-08-02**: residual ship option **1** · Standard routing option **1** · S022 Path A + waive Path B option **1**.

## Next stage after 00

**16-evolve Phase 0** (scope + Fn) → then
`@.cursor/skills/01-requirements/SKILL.md` — load
[checkpoints/01-requirements-seed.md](./checkpoints/01-requirements-seed.md) first.
