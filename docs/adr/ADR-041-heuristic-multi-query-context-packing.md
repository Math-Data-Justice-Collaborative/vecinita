# ADR-041: Heuristic multi-query fan-out + Source/URL context packing

**Status:** Accepted (EV-016 / S019 / F42 / #165)  
**Date:** 2026-08-01  
**Context:** F42 — H7+P1 on E0; S019-D31/D37/D42

## Context

Staging hybrid sweeps showed packing alone (P1) lifts answer relevancy modestly, and a
**thin multi-query fan-out (H7)** reaches Hy1 (~0.31 relevancy / 0.91 faith) without a
faithfulness tradeoff. Full LangGraph workflows (ADR-006) and LLM-generated rewrites add
cost and complexity that the spike did not require. Multilingual embed swap (#159 / E1)
regressed EN relevancy and is out of F42.

## Decision

### 1. P1 packing (default)

- Format each retrieved chunk as:
  `Source: {title}\nURL: {url}\n{text}`
- Shared helper in `packages/rag`; ChatRAG `_build_prompt` and F36 eval sandbox **must**
  call the same helper (no parallel prompt assembly).
- Optional **P3** (document_id dedupe + char budget) is config-gated via
  `VECINITA_RAG_PACKER=p3` + `VECINITA_RAG_CONTEXT_MAX_CHARS` (default 3500); **not** the
  prod default.

### 2. H7 multi-query = cheap heuristics (not LLM)

- Generate 2–3 **locale-aware string variants** of the user query (same family as spike
  `hybrid_rewrites`), not LLM paraphrase calls.
- Retrieve per variant → merge/dedupe by chunk id / score → keep `top_k`.
- Defaults: `VECINITA_RAG_MULTI_QUERY=true`, `VECINITA_RAG_MULTI_QUERY_COUNT=3`.
- Spanish-aware variants when query locale is `es`.

### 3. No LangGraph / ADR-006 amend this cycle

- Implement fan-out as a **thin helper** in `packages/rag` (plain functions / small module).
- Revisit ADR-006 only if multi-turn supervisor / graph orchestration becomes necessary
  (deferred; F43 cache / harness separately).

### 4. Embed pin unchanged

- Prod remains **E0** `BAAI/bge-small-en-v1.5` (384-d). E1/#159 stays open outside F42.

## Consequences

- Slightly higher retrieve latency/cost from N rewrite queries; p95 target remains &lt;15s
  (measure on staging; no new latency AC).
- Ship gate: staging Hy1 relevancy ≥ 0.28 / faith ≥ 0.91 (AC-RQ6); CI floors ≥ 0.60.
- ISS-008 write-api deploy remains a promote-smoke prereq (staging golden fixture path).

## Alternatives considered

| Option | Why not |
|--------|---------|
| LLM query rewrites | Extra LLM round-trips; spike win used heuristics |
| LangGraph S7 workflow | ADR-006 amend deferred; thin helper sufficient |
| R1 cheap rerank | Faith tradeoff (0.82); rejected for F42 default |
| E1 multilingual embed | EN relevancy regression (S019-D37) |

## References

- feature-list F42; spec.md ChatRAG algorithm; config-spec `VECINITA_RAG_*`
- AC-RQ1–RQ7; TC-170–175; UJ-055/056
- Spike: `spike-hybrid-plan.md`, `20260801T002819Z_hybrid-sweep.json`
- ADR-006 (LlamaIndex; no amend); ADR-008 (embed dim)
