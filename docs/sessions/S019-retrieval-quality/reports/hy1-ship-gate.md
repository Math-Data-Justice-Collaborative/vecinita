# F42 Hy1 ship gate (TC-175 / AC-RQ6)

> **Session:** S019 · **Cycle:** EV-016 · **Feature:** F42 · **ADR:** ADR-041  
> **Date:** 2026-08-01

## Ship candidate

**Hy1 = H7 + P1 on E0** (`BAAI/bge-small-en-v1.5`)

| Knob | Default |
|------|---------|
| `VECINITA_RAG_MULTI_QUERY` | `true` |
| `VECINITA_RAG_MULTI_QUERY_COUNT` | `3` |
| `VECINITA_RAG_PACKER` | `p1` |
| Embed pin | E0 — do **not** promote E1/#159 |

## Preconditions

1. **ISS-008 write-api deploy** — Admin `corpus_profile=staging` must resolve
   `data/fixtures/eval/qa_pairs_staging.json` (code mapped; **deploy still required**
   before promote-path smoke).
2. ChatRAG + F36 sandbox share `packages/rag` `pack_chunks` + `multi_query_retrieve`.
3. Phase 21 M91–M93 tasks completed; UJ-055 / TC-170–174 green at T2.

## Staging gate (before promote smoke)

Run F36 / Admin staging golden with Hy1 knobs after ISS-008 is live:

| Metric | Floor |
|--------|-------|
| Answer relevancy | ≥ **0.28** |
| Faithfulness | ≥ **0.91** |

Record EN/ES breakdown when present. CI floors remain ≥ 0.60 / 0.60.

Evidence spike baseline: `20260801T002819Z_hybrid-sweep.json` (Hy1 ~0.31 / 0.91).

## Out of scope for this ship

- E1 multilingual embed promote
- R1 cheap rerank, CE/#83, #162 soft language filter
- LangGraph / ADR-006 amend
- F43 answer cache

## Checklist

- [x] ISS-008 deployed to staging write-api (evolve pin @ `5693422`)
- [x] Staging Hy1 F36 run meets relevancy ≥ 0.28 / faith ≥ 0.91 — `20260802T022836Z` (0.833 / 0.938)
- [x] Promote smoke uses staging golden path (not prod `qa_pairs.json` only) — 18-item staging run
- [x] Prod embed pin unchanged (E0)
