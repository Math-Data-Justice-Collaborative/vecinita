# EV-016 spike plan — Batch A retrieval quality

> **Session:** S019-retrieval-quality  
> **Cycle:** EV-016  
> **Date:** 2026-07-31  
> **Decisions:** S019-D1–D9

## Goal

Measure which lever improves F36 metrics enough to ship **one** change as **F42**.
Investigation set: #158 top_k, #161 rerank→#83, #165 packing, #162 soft language filter.

## Success bar (S019-D6)

| Gate | Criterion |
|------|-----------|
| Primary | F36 golden metrics lift vs dense-only baseline (retrieval relevance; faithfulness / answer relevancy when LLM wired) |
| Ship gate | Same lift holds on chosen winner + **Admin playground promote-path smoke** |
| Guardrails | No major latency regression; Modal cost justified if new model (S019-D8) |

## Environment (S019-D7)

1. **Local first** — seeded fixture corpus (`tests/eval/`, `data/fixtures/eval/qa_pairs.json`) + deterministic/basis embeds where possible.
2. **Staging F36 Admin job** only if local lift is unclear or promote-path smoke requires live corpus.
3. Never point pytest corpus reset at Managed Postgres without corpus-db-safety acks.

## Current prod surface (baseline map)

| Piece | Location | Behavior today |
|-------|----------|----------------|
| Retrieval | `packages/rag/vecinita_rag/retriever.py` | Dense `ORDER BY <=> LIMIT top_k`; optional `language`, tags, `score_threshold` |
| Default top_k | `DEFAULT_TOP_K` / ChatRAG settings / `VECINITA_TOP_K` | **5** |
| Min score | `VECINITA_MIN_RETRIEVAL_SCORE` | **0.2** (ChatRAG) |
| Language | ChatRAG ask path | Strict `d.language = detect_query_language` (ADR-013) |
| Prompt pack | `apps/chat-rag-backend/.../service.py` `_build_prompt` | `"\n\n".join(chunk.text)` — **no titles/URLs/dedupe/budget** |
| Eval runner | `packages/eval/vecinita_eval/runner.py` | Same dense retrieve; context join mirrors prod for synthesis |
| Golden fixture | `data/fixtures/eval/qa_pairs.json` | hit/any_of aggregate ≥80% (TC-111) |

## Ablation matrix

Run in order; stop expanding a branch if no lift.

### A0 — Baseline

- top_k=5, min_score=0.2 (eval may use runner defaults), no language filter in CI harness (confirm), naive concat packing, no rerank.
- Record: retrieval_relevance, per-row hit/miss, latency_p95 if available.

### A1 — top_k (#158)

| Cell | top_k | Notes |
|------|-------|-------|
| A1.a | 3 | Fewer sources |
| A1.b | 5 | Baseline |
| A1.c | 8 | |
| A1.d | 10 | |

Metric focus: retrieval relevance first (does expected URL enter top-k?). Secondary: faithfulness when LLM on (more context vs noise).

### A2 — Context packing (#165)

Prototype packers (local / unit-testable, no Modal):

| Variant | Behavior |
|---------|----------|
| P0 | Baseline concat texts |
| P1 | Prefix each chunk with `title` + `url` |
| P2 | P1 + dedupe by `document_id` (keep highest score) |
| P3 | P2 + token budget truncate (cap context chars/tokens) |

Measure answer metrics when LLM available; retrieval unchanged unless retrieve-N-pack-K.

### A3 — Soft language filter (#162)

| Variant | Behavior |
|---------|----------|
| L0 | Strict same-language (prod) |
| L1 | Same-lang first; if empty or all below min_score → retry without language |
| L2 | Same-lang first; fallback to opposite language only |

Need bilingual miss cases (fixture or synthetic). CI golden may not stress this — flag for staging if local fixtures lack coverage.

### A4 — Rerank (#161 → #83)

| Variant | Approach | Cost (S019-D8) |
|---------|----------|----------------|
| R0 | Dense-only | — |
| R1 | Heuristic: score × doc diversity / title match | Cheap; prefer first |
| R2 | Retrieve N=20 → keep k=5 via simple lexical overlap with question | Cheap |
| R3 | Cross-encoder on Modal (self-hosted) | Allowed if lift clear + cost in report |

Ship rule: if R3 wins → **cheap slice only** this cycle; full #83 stays parent (S019-D5).

## Recommended ship shapes (pick one after spike)

1. **Packing + top_k default** — config/prompt change, no new models  
2. **Cheap rerank (R1/R2)** — code in `packages/rag`, leave #83 for CE  
3. **Soft language fallback** — only if empty-hit rate is the dominant failure  
4. **Cross-encoder slice** — only if F36 lift clear and Modal cost acceptable  

Out: #82, #84, full #76, full #83.

## Execution checklist

- [x] A0 baseline numbers (staging F36 — S019-D10)
- [x] A1 top_k sweep (staging)
- [x] A2 packing prototypes + metrics
- [x] A3 language fallback (staging golden — no soft-filter lift; S019-D13)
- [x] A4 cheap rerank (R1/R2); CE tried (R3) — **no lift, reject** (S019-D14)
- [x] Model sweep closed — keep 1.5B (S019-D21)
- [x] Allocate F42 = P1 packing (S019-D22); recommendation memo still to write
- [ ] Recommendation memo → F42 packing scope + ISS-008
- [ ] Promote-path smoke before ship sign-off (S019-D6)
- [ ] Harness spike H0–H9 (`spike-harness-cache.md`) — Phase 0 parallel (S019-D28)

## Artifacts

| Path | Role |
|------|------|
| This file | Spike plan |
| `reports/spike-baseline.md` | A0 numbers + path map |
| `reports/spike-ablations.md` | A1–A4 results (follow-on) |
| `reports/spike-recommendation.md` | Winner + F42 scope (follow-on) |
| `reports/spike-harness-cache.md` | Cache / LangGraph harness matrix (H0–H6) |
| `reports/model-sweep-tracker.md` | Model sweep (closed) |
