# EV-016 spike A2 — context packing (#165)

> **Session:** S019 · **Cycle:** EV-016 · **Decision:** S019-D11  
> **Date:** 2026-07-31  
> **Artifact:** `spike-a2-packing.json` · script `scripts/spike_a2_packing.py`

## Setup

- Staging corpus (read-only) + `qa_pairs_staging.json`
- Retrieve once @ top_k=5, min_score=0.2; same chunks for all packers
- LLM/judge: `qwen2.5:1.5b-instruct` @ temp 0, max_tokens 128
- P3 budget = `DEFAULT_SYNTHESIS_CONTEXT_MAX_CHARS` (3500)

## Results (single run)

| Variant | Description | retrieval | faith | **relevancy** | p95_ms | mean context chars |
|---------|-------------|-----------|-------|---------------|--------|--------------------|
| P0 | concat texts | 1.00 | 0.91 | 0.15 | 5066 | 7257 |
| **P1** | + title/URL headers | 1.00 | 0.91 | **0.23** | 4671 | 7711 |
| P2 | P1 + dedupe by `document_id` | 1.00 | 0.91 | 0.19 | 5120 | 4867 |
| P3 | P2 + 3500-char budget | 1.00 | 0.91 | 0.19 | 5115 | 3468 |

Retrieval unchanged (same chunks). Faithfulness flat. **Answer relevancy: P1 > P2 ≈ P3 > P0.**

Dedupe cut mean context ~33% (P0→P2); budget caps near 3500 (avoids max_model_len blowups — BUG-2026-07-31).

## Interpretation

1. **Metadata headers (#165 P1) are the clearest relevancy lift** on this golden set.
2. **Dedupe + budget** do not hurt faith and reduce context waste (10/11 rows had duplicate URLs @k=5).
3. Recommended production packer = **P3** (headers + dedupe + budget): best operational hygiene with near-P1 relevancy. Optionally expose budget via config.
4. Combined with A1: optional **default top_k → 8** is secondary; packing first.

## F42 lean (pre-approval)

**Ship F42 = richer context packing** in `packages/rag` (+ ChatRAG `_build_prompt` / eval sandbox join):

- Format: `Source: {title}\nURL: {url}\n{text}` per chunk  
- Dedupe by `document_id` (keep highest score)  
- Truncate packed context to existing sandbox budget (wire shared helper)

**Prereq (ISS-008):** Admin `corpus_profile=staging` must load `qa_pairs_staging.json` so promote-path smoke (S019-D6) is valid.

**Out this cycle:** full #83 rerank, #162 language, #82/#84/#76.

## Next gate

AskQuestion: allocate **F42** on this scope and enter Phase A (01-requirements)?
