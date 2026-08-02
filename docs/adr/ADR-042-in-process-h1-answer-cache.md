# ADR-042: In-process H1 answer / retrieval cache cascade

**Status:** Accepted (EV-017 / S020 / F43)  
**Date:** 2026-08-02  
**Context:** F43 — H1 cascade; S020-D4/D10/D14/D15; RD-197–201; TP1–TP7

## Context

Harness cells H1/H9 showed that caching exact (and near-exact) answers plus retrieve
results cuts LLM cost/latency on repeat asks. Durability via Modal volume or Redis would
add ops surface without proven need at pilot traffic. Identity- or session-keyed caches
conflict with ADR-004 (zero personal data on ChatRAG). Semantic false hits are the main
quality risk.

## Decision

### 1. Full H1 cascade (default when `VECINITA_RAG_CACHE=true`)

Order on ask/stream:

1. **Exact** answer cache — key = content-hash of normalized query + locale  
2. **Semantic** answer cache — cosine ≥ `VECINITA_RAG_CACHE_SEMANTIC_THRESHOLD` (default **0.92**);
   miss → continue (never invent a hit)  
3. **Retrieve-result** cache — same key family; skip dense retrieve on hit  
4. **Generate** — synth + store answer (+ retrieve) for future hits  

Observability: `cache_hit` ∈ {`none`, `exact`, `semantic`, `retrieve`} on `/ask` and stream
`done` (OpenAPI update in 07-build per S020-D15/M4).

### 2. In-process only this cycle

- Process-local LRU: TTL = `VECINITA_RAG_CACHE_TTL_S` (default **3600**),
  `max_entries` = `VECINITA_RAG_CACHE_MAX_ENTRIES` (default **1024**).
- **No** Redis, **no** Modal volume durable cache in EV-017 (RD-207).
- Bust on corpus / version stamp changes and F41 rebuild promote (ADR-040).

### 3. Keys and embeddings

- Content-hash keys only — **no** identity/session keys (ADR-004).
- Semantic tier reuses the **existing query embed** path (same Modal embed as retrieve;
  no second embed stack).

### 4. Shared helper; no LangGraph

- Cascade helpers live in `packages/rag`; ChatRAG + F36 harness call the same API.
- No ADR-006 amend / LangGraph this cycle (S019-D27 / RD-207).

## Consequences

- Multi-replica ChatRAG instances do **not** share cache — acceptable at pilot scale;
  revisit Redis/volume only with evidence.
- Conservative 0.92 threshold favors misses over wrong answers; warm quality must stay ≥ H0
  (AC-BB2).
- OpenAPI / contract yaml for `cache_hit` lands with implementation (07-build).

## Alternatives considered

| Option | Why not |
|--------|---------|
| Redis / shared cache | Ops + cost; not required for H1/H9 win |
| Modal volume durable cache | Explicitly out of scope (RD-207) |
| Identity-keyed cache | Violates ADR-004 |
| LangGraph cache node | ADR-006 amend deferred |
| Lower semantic threshold | Higher false-hit risk; rejected (S020-D10/D15) |

## References

- feature-list F43; config-spec `VECINITA_RAG_CACHE*`; api-contract `cache_hit`
- AC-BB1–BB4, AC-BB10; TC-176–179; UJ-057
- ADR-004, ADR-006, ADR-040, ADR-041
- S019 `spike-harness-cache.md`; RD-197–201, RD-207
