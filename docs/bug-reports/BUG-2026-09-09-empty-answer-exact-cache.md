# BUG-2026-09-09-empty-answer-exact-cache

> Status: fixed (merged to `stage` via #368)  
> Severity: high (staging ChatRAG quality)  
> Surface: `POST /api/v1/ask` exact-answer cache  
> Spec: [Corpus: staging] [Corpus: api] [Spec: docs/api-contract.md §POST /api/v1/ask]

## Error description

Staging ChatRAG returns the empty-corpus refusal for a canonical food question and
sets `cache_hit: "exact"`. Retries immediately return the same empty answer from
cache even though the corpus has food/pantry documents and other asks (unicode food,
XSS+food variants earlier in the same session) sometimes retrieve sources.

## Error logs

```text
POST https://vecinita-staging-chat-api-tobwu.ondigitalocean.app/api/v1/ask
{"question":"Where can I get food assistance in Providence?"}
→ HTTP 200
{"answer":"I don't have enough community corpus context to answer that question.",
 "sources":[],"cache_hit":"exact","answer_path":"rag_llm"}

Retries 1–3: identical cache_hit=exact, sources=[]
```

Session evidence:
`~/.cursor/workflow/.../EV-staging-adversarial-plunge/evidence/pass2/h3-retry-*.json`

Related: hybrid jailbreak/XSS prefixes also empty-corpus (F3) — may seed the bad cache.

## Investigation

| Time (EDT) | Note |
|------------|------|
| 2026-09-09 ~07:41 | Pass-2 plunge: H3 food empty + exact cache |
| 2026-09-09 ~07:45 | 50-way stress: 35/50 with sources, 15 empty — food canonical remains exact-cached empty |
| 2026-09-09 | Corpus browse still 95 docs with food tags; Spanish food ask in chat UI had sources |

**Hypothesis:** Exact-cache keys on normalized question text and stores no-context
refusals, poisoning subsequent asks until TTL/eviction. Do **not** cache empty /
no-source refusals (or treat them as negative cache with short TTL / never).

## Repro test

`tests/bugs/test_bug_2026_09_09_empty_answer_exact_cache.py` — empty
`store_answer` / `store_retrieve` no-ops; cascade empty generate does not
exact-hit on retry.

## Fix

`AnswerCache.store_answer` / `store_retrieve` skip empty payloads so no-context
refusals cannot poison exact/retrieve tiers. Stream path no longer calls
`store_answer` for empty chunk lists (redundant with cache guard).

**Code merged to `stage` via #368 (2026-09-09).** Live staging ChatRAG still
served `cache_hit: exact` empty answers for the canonical food question during
EV-staging-adversarial-ux (process had not recycled / DO app not yet redeployed).
Paraphrases returned sources. **Action:** redeploy staging ChatRAG from current
`stage` tip, then re-verify the canonical food ask.

## Interview record

Found during EV-staging-adversarial-plunge pass 2 (operator-approved staging plunge).
Reconfirmed EV-staging-adversarial-ux Build band 2026-09-09.