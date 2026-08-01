# EV-016 spike baseline — A0

> **Session:** S019-retrieval-quality · **Cycle:** EV-016  
> **Date:** 2026-07-31  
> **Status:** Partial — code path mapped; **live F36 numbers blocked** (no local Postgres / Docker daemon)

## Environment attempt (S019-D7)

| Check | Result |
|-------|--------|
| `postgres_is_ready()` | False |
| `docker` CLI | Present under Docker.app Resources |
| Docker daemon | **Down** — `unix:///var/run/docker.sock` missing after ~90s wait |
| `pytest tests/eval/test_eval_retrieval_relevance.py` | **2 skipped** (Postgres not available) |

**Unblock:** Start Docker Desktop (or otherwise provide local Postgres on `localhost:5432`), then:

```bash
export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"
export DATABASE_URL=postgresql+psycopg://vecinita:vecinita@localhost:5432/vecinita
docker compose -f infra/docker-compose.yml up -d postgres
cd apps/database && uv run alembic upgrade head
uv run pytest tests/eval/test_eval_retrieval_relevance.py -v
uv run python scripts/spike_ev016_retrieval_ablations.py  # once added
```

## Prod / eval path map (confirmed in code)

### Retrieval

- `CorpusPgvectorRetriever.retrieve_chunks` — dense cosine distance, `LIMIT :top_k`
- Optional filters: `d.language = :language`, tag EXISTS clauses, `score_threshold` post-filter
- Default top_k = **5** (`DEFAULT_TOP_K`)

### ChatRAG ask

- Language: `detect_query_language` → strict language filter (ADR-013) — soft fallback = #162
- Prompt: `_build_prompt` joins `chunk.text` with `"\n\n"` only — **no title/url/dedupe/budget** (#165)
- Sources: all retrieved chunks above threshold returned to FE (top_k = sources count unless FE truncates)

### F36 harness

- Fixture: `data/fixtures/eval/qa_pairs.json` (`fixture://` URLs)
- Aggregate ≥80% over **hit + any_of** only (TC-111)
- Runner context for judges: same naive `"\n\n".join(chunk.text)`
- CI embed: deterministic `eval_embed_fn` + `seed_eval_corpus` basis vectors (not live Modal embeds)

## Fixture inventory (local golden)

| Stat | Value |
|------|-------|
| Total locale rows | **14** |
| Scored (hit + any_of) | **12** |
| hit | 11 |
| any_of | 1 |
| abstain | 1 |
| empty | 1 |

Scored ids: community-food-pantry (en/es), community-library-wifi (en/es), community-story-time (en/es), community-vecinita-intro (en/es), edge-ambiguous-housing (en), housing-eviction-notice (en), legal-aid-benefits (en), legal-aid-housing (en).

## A0 metrics (pending live run)

| Metric | Value | Notes |
|--------|-------|-------|
| retrieval_relevance | *TBD* | Expect ≥0.80 on seeded fixture (TC-111) |
| faithfulness | *TBD* | Needs LLM/judge; optional for A1 retrieval-only |
| answer_relevancy | *TBD* | Same |
| latency_p95_ms | *TBD* | |

## Implications for ablations

Until Docker/Postgres is up:

1. **Packing (#165)** prototypes can proceed as **pure unit tests** (no DB) — transform `RetrievedChunk` lists → prompt string; assert titles/dedupe/budget.
2. **top_k / rerank / language** need seeded corpus → blocked on Postgres (or staging per S019-D7 if local stays unavailable).
3. Promote-path smoke (S019-D6) remains a **ship gate**, not A0.

## Next

Ask operator: start Docker locally vs waive to staging F36 for A0/A1 vs continue packing unit prototypes in parallel.
