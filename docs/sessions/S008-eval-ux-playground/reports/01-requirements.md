# 01-requirements report — S008-eval-ux-playground

**Session:** S008-eval-ux-playground  
**Evolve cycle:** EV-009  
**Date:** 2026-07-02  
**Stage:** 01-requirements (delta)  
**Features:** F36 follow-ons (M65–M67) + **F37** (M68–M70)

## Summary

Requirements interview completed for four evaluation-page improvements from staging feedback.
User confirmed evolve-lite path (not hotfix), build order **1→2→3→4**, and new **F37** for
playground + super-admin runtime promote.

## Interview resolutions

| Item | Decision | RD |
|------|----------|-----|
| 1 Run list refresh | Optimistic prepend + poll; no manual refresh | RD-115 |
| 2 Jobs tab | Unified `GET /jobs` with `job_type=eval` | RD-116 |
| 3 Dashboard charts | FE presets (1D/7D/10D/1M/1Y/custom) + scatter | RD-117 |
| 4 Playground tab | Golden + ad-hoc; versioned presets; share-read | RD-118–RD-121 |
| 4 RAG params | Full v1 set (top_k, scores, prompt, tokens, temp, corpus) | RD-122 |
| 4 Model | Modal LLM hyperparams only | RD-123 |
| 4 Judge | Criteria from existing tab + judge temperature | RD-124 |
| 4 Guardrails | System rules text in `system_prompt` | RD-125 |
| 4 Isolation | Sandbox until super-admin promote (runtime DB switch) | RD-126–RD-127 |
| 4 Compare | Side-by-side two runs in v1 | RD-130 |
| Run button | Opens Playground with last preset | RD-129 |

## Documents updated

| Document | Changes |
|----------|---------|
| `docs/feature-list.md` | F37 entry; F36 S008 follow-on note |
| `docs/user-journeys.md` | UJ-039/041 deltas; UJ-044–047 new |
| `docs/test-plan.md` | TC-123–TC-133; journey mapping |
| `docs/api-contract.md` | §EV-009 presets, extended eval run, promote |
| `docs/config-spec.md` | Super-admin email + RAG config fallback env vars |
| `docs/decisions.md` | RD-114–RD-130 |
| `docs/sessions/S000-internal-docs-archive/context/eval-ux-playground.md` | Gaps closed → 04-tech-plan |

## Milestones (for 04-tech-plan)

| Milestone | Scope |
|-----------|-------|
| M65 | Optimistic eval run list + poll UX |
| M66 | Unified jobs API + Jobs tab `eval` |
| M67 | Dashboard scatter + time-range presets + custom picker |
| M68 | Config schema + preset API + DB tables |
| M69 | Playground UI (golden + ad-hoc + compare) |
| M70 | Super-admin promote + ChatRAG active config reader |

## Test requirements (by layer)

| Layer | New artifacts |
|-------|----------------|
| API E2E | `test_uj044_eval_jobs_tab.py`, `test_uj045_eval_playground.py`, `test_uj047_eval_promote_config.py` |
| Integration | `test_eval_config_presets.py`, `test_rag_production_config.py` |
| Vitest | `test_evaluation_playground.test.tsx`, `test_evaluation_compare.test.tsx`; dashboard/page updates |
| Playwright T0-ui | `uj044-eval-jobs-tab.spec.ts`, `uj045-eval-playground.spec.ts` |

## Open for 04-tech-plan

- ADR for `super-admin` role + `rag_production_config` schema
- Validation bounds for config fields
- Eval runner job registration contract with DM backend
- ChatRAG config read path (DB vs internal API)

## Next step

**04-tech-plan** (delta) — ADR + execution-plan milestones M65–M70
