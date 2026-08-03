# Session brief — S023-retrieval-topk-packing

| Field | Value |
|-------|--------|
| **id** | `S023-retrieval-topk-packing` |
| **type** | `feature` |
| **orchestrator** | `16-evolve` |
| **evolve_cycle** | `EV-020` |
| **branch** | `evolve/EV-020-retrieval-topk-packing` |
| **opened** | 2026-08-02 |
| **github_issues** | [#158](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/158), [#165](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/165) |
| **predecessor** | S022 / EV-019 (Path A ship; Path B rechunk waived) |

## Intent

Residual **retrieval ship** after EV-016 F42 (P1 packing + H7) and S019 spikes:

1. **#158** — Tune / promote prod `top_k` (still default **5** on ChatRAG / `VECINITA_TOP_K`).
2. **#165** — Default **P3** packer (doc dedupe + char budget) — code exists behind `VECINITA_RAG_PACKER=p3`; prod still **`p1`**.

Not a full re-investigation: reuse S019 A1/A2 evidence; ship config/default changes + tests + close or retarget issues.

## Out of scope (unless Phase 0 expands)

- CE enablement / #83 (`VECINITA_RAG_RERANK_CE` stays false)
- Multilingual embed swap / #159
- EV-019 Path B corpus rechunk (waived follow-up)
- Adaptive top_k policy (unless 01 unlocks)

## Routing

**Standard** — see [routing-plan.md](./routing-plan.md). User-approved 2026-08-02.
