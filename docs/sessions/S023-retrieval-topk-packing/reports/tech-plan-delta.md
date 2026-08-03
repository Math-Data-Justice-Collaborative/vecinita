# 04-tech-plan delta — EV-020 / F50–F51

> **Session:** S023 · **Cycle:** EV-020 · **Date:** 2026-08-03  
> **Status:** approved — Gate B→C PASS (S023-D12); 07-build in progress

## Proposed TP1–TP6 (recommended)

| ID | Topic | Choice |
|----|-------|--------|
| TP1 | Phase / milestones | **Phase 25**: M105 (F50) → M106 (F51) → M107 (UJ-063 e2e) |
| TP2 | ADR | **None new** — reuse ADR-041 |
| TP3 | Config / DO | `VECINITA_TOP_K=8`; `VECINITA_RAG_PACKER=p3`; EvalConfig default 8 |
| TP4 | Tests | Unit TC-193/194; API e2e UJ-063 (TC-195); no Playwright |
| TP5 | Deploy / deps | Staging Path A ChatRAG; no dep inventory change |
| TP6 | Connectivity | No new CORS/UI — API e2e + staging H1–H5 at 13 |

## Artifacts

| Artifact | Path |
|----------|------|
| Execution plan Phase 25 | `docs/sessions/S000-internal-docs-archive/execution-plan.md` |
| This report | `docs/sessions/S023-retrieval-topk-packing/reports/tech-plan-delta.md` |

## Milestones

| M | Focus | Fn |
|---|-------|-----|
| M105 | Promote `top_k` / `DEFAULT_TOP_K` / DO `VECINITA_TOP_K` → **8** | F50 |
| M106 | Default packer **`p3`** (code + DO) | F51 |
| M107 | UJ-063 e2e + phase-gate docs + issue closeout notes | F50–F51 |

## Locked product defaults (carry from Phase 0)

| ID | Value |
|----|--------|
| top_k (RD-230) | **8** |
| Sources UX (RD-231) | = retrieve count |
| Packer (RD-232) | **p3**; max_chars **3500** |
| Order (TP1) | M105 → M106 → M107 |
| Deploy (RD-234) | Path A ChatRAG |

## Next (after Gate B→C)

`07-build` (05/06 skipped) @ T105.1 — F50 top_k default tests.
