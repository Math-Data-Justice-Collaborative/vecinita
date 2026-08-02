# Context brief — S020 / EV-017 (scoped, continues S019)

> **Mode:** delta / evolve — no paper or greenfield repo scan. Priors from S019 spikes.

## Topology (unchanged)

Browser Admin + ChatRAG frontends → DO App Platform APIs → Modal LLM (`vecinita-llm` prod,
`vecinita-llm-playground` eval) + Supabase/Postgres corpus. F42 packing + H7 live on main.

## Batch B priors

| Track | Evidence | Implication |
|-------|----------|-------------|
| F43 cache | H1/H9 warm: quality≈H0, cache_hit≈1, $/row→0 | **Ship candidate** without LangGraph |
| #83/#161 CE | R3 relevancy 0.08–0.15 vs R0+P1 0.23 | Spike again only with new hypothesis/gate |
| #162 soft lang | L1/L2 unused on golden | Empty-hit fixture or #54-class; config-gated |

## Constraints carried forward

- ADR-004: no identity-keyed chat history / cache keys
- ADR-006: LlamaIndex ChatRAG; LangGraph amend deferred (S019-D27)
- ADR-009 / ADR-037: prod synthesizer pin `qwen2.5:1.5b-instruct`
- ADR-041: H7+P1 packing already shipped (F42)

## Sources

- `docs/sessions/S019-retrieval-quality/reports/spike-harness-cache.md`
- `docs/sessions/S019-retrieval-quality/reports/spike-a4-r3-cross-encoder.md`
- `docs/sessions/S019-retrieval-quality/reports/spike-a3-language.md`
- `docs/sessions/S019-retrieval-quality/reports/spike-recommendation.md`
- `docs/evolve-report-EV-016.md`
