# Routing plan — S023-retrieval-topk-packing (Standard)

| Stage | Required | Status | Mode | Notes |
|-------|----------|--------|------|-------|
| 00-context | yes | completed | scoped | Session open 2026-08-02; S022 closed first |
| 16-evolve | orchestrator | in_progress | — | EV-020 — 13-deploy-smoke Path A |
| 01-requirements | yes | completed | delta | Report: [01-requirements-topk-packing.md](./reports/01-requirements-topk-packing.md) |
| 02-verify-plan | yes | completed | delta | Gate A→B PASS (S023-D10) |
| 04-tech-plan | yes | completed | delta | Gate B→C PASS (S023-D12) |
| 07-build | yes | completed | — | M105–M107 done 2026-08-03 |
| 08-verify-build | yes | completed | — | Milestone/phase verification report |
| 09-qa | yes | completed | — | Advisories cleared S023-D17 |
| 10-e2e | yes | completed | — | T0 PASS; T2 deferred to 13 |
| 11-verify-impl | yes | completed | — | S023-D19/D20; [verify-impl.md](./reports/verify-impl.md) |
| 12-verify-deploy | yes | completed | delta | S023-D21; [deploy-checklist.md](./reports/deploy-checklist.md) |
| 13-deploy-smoke | yes | in_progress | — | H1–H5 + DO `VECINITA_TOP_K` / packer |

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
