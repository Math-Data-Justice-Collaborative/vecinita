# 01-requirements — S023 / EV-020 (top_k + P3 packing)

**Date:** 2026-08-02  
**Mode:** delta  
**Features:** F50 (#158), F51 (#165)

## Phase 0C / Phase 0 answers

| Q | Answer | Decision |
|---|--------|----------|
| Locked L1–L5 | Approved via S023-D1–D5 | Session/routing/issues/predecessor/branch |
| Phase 0 option | **1** | F50 `top_k=8` + F51 default P3; close #158/#165 after ship |
| Sources UX | Recommended | Sources shown = retrieve `top_k` (S023-D7) |
| Deploy surface | Recommended | Code defaults + DO `VECINITA_TOP_K` / `VECINITA_RAG_PACKER` |

## Document manifest checklist

| Document | Status |
|----------|--------|
| `docs/feature-list.md` | F50–F51 details; F1 `top_k=8`; F42 follow-on note |
| `docs/spec.md` | Ask algorithm P3 default + top_k=8; changelog row |
| `docs/config-spec.md` | Defaults `TOP_K=8`, `RAG_PACKER=p3` |
| `infra/vecinita.yaml` | `top_k: 8`, `rag_packer: p3` |
| `docs/user-journeys.md` | UJ-055 note + **UJ-063** |
| `docs/test-plan.md` | TC-193–195 |
| `docs/acceptance-criteria.md` | AC-RQ8–RQ10; AC-RQ4 note |
| `docs/decisions.md` | RD-229–RD-236 |
| `docs/decisions/evolve-decisions.md` | EV-020 cycle section |
| `docs/api-contract.md` | N/A — response shape unchanged |
| `docs/dependency-inventory.md` | N/A — no new deps |
| ADR | None new — reuse ADR-041 |

## Out of scope (held)

Adaptive top_k · FE-only source truncation · CE flag flip · token-accurate budget · Path B rechunk · #159 embeds

## Next

`@.cursor/skills/02-verify-plan/SKILL.md` — delta consistency + statement audit
