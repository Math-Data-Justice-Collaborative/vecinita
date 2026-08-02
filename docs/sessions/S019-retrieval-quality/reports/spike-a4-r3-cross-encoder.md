# EV-016 spike A4-R3 — cross-encoder on Modal (#161 → #83)

> **Session:** S019 · **Cycle:** EV-016 · **Decision:** S019-D14  
> **Date:** 2026-07-31  
> **Artifact:** `spike-a4-r3-cross-encoder.json`  
> **Scripts:** `spike_a4_r3_cross_encoder.py`, `spike_a4_r3_ce_modal.py`

## Setup

- Staging golden, retrieve N=20 (L_none), keep_k=5, min_score=0.2
- CE: **`BAAI/bge-reranker-base`** on Modal **T4** (ephemeral app `vecinita-spike-r3-rerank`)
- Passage cap 1500 chars (title + text) for CE pairs
- Same-run controls: R0 dense, R1 heuristic (A4), × P0/P1 packing

## Results (single run)

| Cell | retrieval | faith | **relevancy** | p95_ms |
|------|-----------|-------|---------------|--------|
| R0+P0 | 1.00 | 0.91 | 0.15 | 5175 |
| R1+P0 | 1.00 | 0.82 | 0.15 | 4239 |
| **R3+P0** | 1.00 | 0.82 | **0.08** ↓ | 4270 |
| R0+P1 | 1.00 | 0.91 | 0.23 | 4759 |
| **R1+P1** | 1.00 | 0.82 | **0.31** | 4231 |
| R3+P1 | 1.00 | **0.91** | **0.15** ↓ | 4697 |

## Cost (S019-D8)

| Item | Value |
|------|-------|
| CE wall-clock (score 13×20) | **34.3 s** |
| Rough T4 on-demand estimate | **~$0.006** (scoring phase only; excludes cold start / image build) |
| Lift clear? | **No** — relevancy worse than R0+P1 and R1+P1 |

## Interpretation

1. **R3 does not clear the S019-D8 bar** — no F36 relevancy lift; with P0 it is the worst cell (0.08).
2. **R3+P1** preserves faith (0.91) but **drops relevancy vs packing alone** (0.15 vs R0+P1 0.23).
3. **Same-run R1+P1** again tops relevancy (0.31) with the known faith tradeoff (0.82) — matches prior A4.
4. Leave full **#83** open; do **not** ship CE this cycle. Prefer packing (P1) ± optional R1.

## Spike scoreboard (best cells)

| Approach | relevancy | faith | notes |
|----------|-----------|-------|-------|
| A2 / R0+P1 packing | 0.23 | 0.91 | safest ship lean |
| A4 R1+P1 | **0.31** | 0.82 | best relevancy; faith tradeoff |
| A4-R3 CE | 0.08–0.15 | 0.82–0.91 | **reject** — no lift vs cost |
| A3 soft language | 0.19 | 0.91 | fallbacks unused; defer #162 |

## Next (AskQuestion)

Lock F42 ship candidate now that cheap + CE paths are measured.
