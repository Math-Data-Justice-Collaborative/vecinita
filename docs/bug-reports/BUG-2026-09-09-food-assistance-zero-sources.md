# BUG-2026-09-09-food-assistance-zero-sources

[Corpus: staging] [Corpus: product] [Corpus: journeys]

## Error description

Staging ChatRAG returns **0 sources** and empty-corpus copy for the natural phrasing
“Where can I get food assistance in Providence Rhode Island?” while shorter food
queries retrieve 8 sources and answer well. Exact-cache is **not** poisoning
(`cache_hit=none`) after #368.

## Error logs

```
POST /api/v1/ask {"question":"Where can I get food assistance in Providence Rhode Island?","language":"en"}
→ sources=0 cache=none answer_path=rag_llm
answer: No matching sources were found in the community corpus…

Contrast:
"food pantry Providence" → sources=8
"Where is a food bank in Providence?" → sources=8
```

First attempt also timed out at 120s (cold start); retry after `/api/v1/warm` returned quickly with 0 sources.

## Investigation

1. #368 empty exact-cache: **PASS** on this phrasing.
2. **Root cause (EV-stage-prod-ux-validation):** H7 EN `heuristic_rewrites` wasted the
   rewrite slot appending `in Providence RI?` when Providence was already present, and
   did not map `food assistance` → corpus lexicon `food pantry` / `food bank`.
3. XSS-prefixed pantry asks previously returned sources — phrasing sensitivity.

## Repro / regression test

- `tests/bugs/test_bug_2026_09_09_food_assistance_zero_sources.py`
- `tests/unit/rag/test_multi_query.py`
  (`test_heuristic_rewrites_en_skips_location_when_providence_present`,
  `test_heuristic_rewrites_en_food_assistance_adds_pantry_synonym`,
  `test_multi_query_retrieve_food_assistance_providence_uses_synonym_hits`)

## Fix

**Fixed** in `packages/rag/vecinita_rag/multi_query.py`: EN location append skips when
Providence is present; `food assistance` adds a pantry synonym variant. Empty-corpus UX
copy unchanged; Chat FE adds Browse corpus CTA when sources are empty.

## Status

**fixed** — pending stage deploy validation after merge
