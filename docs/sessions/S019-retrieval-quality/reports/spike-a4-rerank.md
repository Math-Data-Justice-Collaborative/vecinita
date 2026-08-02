# EV-016 spike A4 — cheap rerank (#161)

> **Session:** S019 · **Cycle:** EV-016 · **Decision:** S019-D12  
> **Date:** 2026-07-31  
> **Artifact:** `spike-a4-rerank.json`

## Setup

- Staging golden (`qa_pairs_staging.json`), keep_k=5, pool N=20, min_score=0.2
- R0 dense top-5 · R1 title-overlap × dense + doc diversity · R2 lexical overlap
- Packing: P0 concat vs P1 title/URL (best A2)

## Results (single run)

| Cell | retrieval | faith | **relevancy** | p95_ms |
|------|-----------|-------|---------------|--------|
| R0+P0 | 1.00 | 0.91 | 0.15 | 5071 |
| R1+P0 | 1.00 | 0.82 ↓ | 0.15 | 4485 |
| R2+P0 | **0.82** ↓ | 0.91 | **0.08** ↓ | 4283 |
| R0+P1 | 1.00 | 0.91 | 0.23 | 4522 |
| **R1+P1** | 1.00 | 0.82 ↓ | **0.31** | 4249 |
| R2+P1 | **0.82** ↓ | 0.91 | **0.08** ↓ | 4618 |

## Interpretation

1. **R2 (lexical) is harmful** — drops retrieval to 0.82 and relevancy to 0.08. Do not ship.
2. **R1 alone (with P0) does not help relevancy**; with **P1** it reaches **0.31** (best so far) but **faith drops** 0.91 → 0.82.
3. **Safest quality lift remains R0+P1** (headers only): relevancy 0.23, faith held.
4. Overall relevancy is still low (<0.35). Further options: A3 language, cross-encoder (R3), or ship a small packing (+ optional R1) and keep #83 open for CE.

## Spike scoreboard (best cells so far)

| Approach | relevancy | faith | notes |
|----------|-----------|-------|-------|
| A0 dense k=5 | ~0.08–0.15 | 0.91 | run noise |
| A1 k=8 | 0.19 | 0.91 | retrieval saturated |
| A2 P1 packing | 0.23 | 0.91 | best safe packing |
| A4 R1+P1 | **0.31** | 0.82 | best relevancy; faith tradeoff |
| A4 R2 | 0.08 | 0.91 | reject |

## Next (AskQuestion)

Continue A3 / CE, or lock a ship candidate (P1 ± R1) despite modest absolute scores.
