# 01-requirements seed — S023 / EV-020

> Loaded first by 01-requirements Phase 0C. Locked decisions below; interview only unlocked deltas.

## Locked (from 00 / user)

| ID | Decision |
|----|----------|
| S023-D1 | Session type `feature`; orchestrator 16-evolve; cycle **EV-020** |
| S023-D2 | Routing **Standard** (skip 03/05/06/15) |
| S023-D3 | Issues **#158** + **#165** residual **ship** (not full re-investigation) |
| S023-D4 | Predecessor S022 closed: Path A PASS @ `bd6bb00`; Path B rechunk waived |
| S023-D5 | Branch `evolve/EV-020-retrieval-topk-packing` from `main` |

## Proposed Fn (pending Phase 0 approval)

| Fn | Issue | Working title | Notes |
|----|-------|---------------|-------|
| **F50** | #158 | Promote tuned prod `top_k` | Default still 5; spike lean optional → 8; confirm value in Phase 0 |
| **F51** | #165 | Default P3 context packing | Flip `VECINITA_RAG_PACKER` default `p1`→`p3`; keep `CONTEXT_MAX_CHARS` (3500) unless retuned |

## Evidence to reuse (do not re-spike unless blocked)

| Artifact | Relevance |
|----------|-----------|
| S019 `spike-a1-*` / golden top_k cells | #158 |
| S019 `spike-a2-packing.md` | #165 — P3 recommended operational hygiene |
| F42 / ADR-041 / `packages/rag/packing.py` | P1 shipped; P3 implemented, non-default |
| ChatRAG `VECINITA_RAG_PACKER` / `VECINITA_TOP_K` | Config surface |

## Open for Phase 0 / 01

1. Exact prod `top_k` target (keep 5 / 8 / other / retrieve-N-show-K).  
2. Whether FE sources list should cap independently of retrieve `top_k`.  
3. DO env promote vs code default change for packer/`top_k`.  
4. Issue closeout text for #158/#165 after ship.
