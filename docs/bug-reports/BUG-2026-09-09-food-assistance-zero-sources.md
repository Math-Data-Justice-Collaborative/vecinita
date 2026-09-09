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
2. Retrieval / embedding / min-score / packer for this query class still fails.
3. XSS-prefixed pantry asks previously returned sources — phrasing sensitivity.

## Repro / regression test

Pending dedicated retrieval unit once root cause isolated; live matrix in
`EV-staging-responsive-plunge` `evidence/api/` + `reports/findings.md`.

## Fix

Open — retrieval quality (not FE). Do not weaken empty-corpus UX.

## Status

**open** — tracked for follow-on RAG evolve; not blocked by this UX PR
