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
2. **H7 rewrite gap (partial):** EN wasted rewrite slot on duplicate Providence; lacked
   `food assistance` → pantry lexicon. Fixed in #385 (`multi_query.py`).
3. **CE wipe (root cause after #385 deploy):** Staging has CE rerank on. Multi-query
   recovered pantry chunks, but CE scored them against the raw “food assistance”
   question below `min_retrieval_score` → empty set. Direct ask of the pantry synonym
   returned 8 sources. Fix: fail-open to pre-CE candidates when CE empties a non-empty
   set; short `food pantry Providence` synonym for Providence phrasings.

## Repro / regression test

- `tests/bugs/test_bug_2026_09_09_food_assistance_zero_sources.py`
- `tests/unit/rag/test_multi_query.py`
- `tests/unit/rag/test_chat_retrieve.py::test_retrieve_chat_chunks_ce_failopen_when_threshold_empties_candidates`

## Fix

1. H7 EN synonyms + skip duplicate Providence (#385)
2. CE fail-open in `retrieve_chat_chunks` when threshold empties candidates
3. Short `food pantry Providence` synonym for Providence + food assistance

## Status

**fixed** — pending stage redeploy + live re-smoke
