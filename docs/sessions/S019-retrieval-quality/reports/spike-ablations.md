# EV-016 spike ablations — A0/A1 staging

> **Session:** S019-retrieval-quality · **Cycle:** EV-016  
> **Date:** 2026-07-31  
> **Decision:** S019-D10 — staging F36 escape hatch

## Environment

| Item | Value |
|------|-------|
| Corpus | DO Managed Postgres (read-only; no reset) |
| Embed / LLM | Modal `vecinita-embedding` + `vecinita-llm` (`qwen2.5:1.5b-instruct`) |
| Golden | `data/fixtures/eval/qa_pairs_staging.json` (13 rows, 11 scored) |
| Operator env | `.env` (not `prod.env`); `VECINITA_MODAL_OLLAMA_URL` unset |

## A0 — Baseline (top_k=5, min_score=0.2)

| Source | retrieval | faithfulness | answer_relevancy | latency_p95_ms |
|--------|-----------|--------------|------------------|----------------|
| Staging LLM sweep (correct fixture) | **1.00** | **0.91** | **0.08** | 6547 |
| Admin F36 golden `corpus_profile=staging` | 0.00* | 0.25* | 0.11* | 5125 |

\*Admin run scored against **CI `qa_pairs.json` (`fixture://` URLs)** while retrieving live `https://` docs — metrics invalid. See §Admin fixture bug.

Artifacts:
- `spike-a0-staging-llm-baseline.json` / `.log`
- `spike-a0-admin-golden.json` (invalid scoring — retained as evidence)
- `spike-a0-a1-staging-retrieval.json`

## A1 — top_k (#158)

### Retrieval-only (cached embeds)

| top_k | retrieval_relevance | notes |
|-------|---------------------|-------|
| 3 | 1.00 (11/11) | Expected URL always in top-3 |
| 5 | 1.00 | Baseline |
| 8 | 1.00 | |
| 10 | 1.00 | |

Rank of expected URL @ top_k=5: **7× rank1, 3× rank2, 1× rank3**.  
**10/11** scored rows return **duplicate document URLs** in top_k (same doc, multiple chunks).

### LLM answer metrics (single run)

| top_k | retrieval | faith | relevancy | p95_ms |
|-------|-----------|-------|-----------|--------|
| 3 | 1.00 | 0.91 | 0.12 | 6095 |
| 5 | 1.00 | 0.91 | 0.08 | 6547 |
| 8 | 1.00 | 0.91 | **0.19** | 6693 |

Artifact: `spike-a1-staging-llm-topk.json`

### Interpretation

- **Retrieval is saturated** on the staging golden set — #158 alone cannot improve hit rate.
- **Answer relevancy** is the weak metric (~0.08–0.19); one-run noise, but top_k=8 looks better than 5.
- **Duplicate URLs** waste context window → strong signal for **#165 packing (dedupe + titles + budget)**.
- Changing default top_k without packing is a weak ship candidate.

## A2 — Context packing (#165)

See **`spike-a2-packing.md`**. Summary @ top_k=5:

| Variant | relevancy | mean chars |
|---------|-----------|------------|
| P0 concat | 0.15 | 7257 |
| P1 title/URL | **0.23** | 7711 |
| P2 + dedupe | 0.19 | 4867 |
| P3 + budget | 0.19 | 3468 |

**Lean:** F42 deferred (S019-D12). A4 complete — see `spike-a4-rerank.md`. Best relevancy
**R1+P1 = 0.31** (faith 0.82); safest **R0+P1 = 0.23** (faith 0.91). R2 rejected.

## A3 — Soft language filter (#162)

See **`spike-a3-language.md`**. Summary @ top_k=5, P0 packing:

| Cell | retrieval | relevancy | fallback fired |
|------|-----------|-----------|----------------|
| L_none (prior spike path) | 1.00 | 0.15 | n/a |
| L0 / L1 / L2 | 0.91 | 0.19 | **0** (identical) |

Soft fallbacks never trigger on staging golden. #162 not a ship candidate from this fixture
(S019-D13). Note: A0–A4 used **L_none**; prod is L0.

## A4-R3 — Cross-encoder on Modal (#161 → #83)

See **`spike-a4-r3-cross-encoder.md`**. Same-run grid @ N=20→5, `bge-reranker-base` T4:

| Cell | relevancy | faith |
|------|-----------|-------|
| R0+P1 | 0.23 | 0.91 |
| R1+P1 | **0.31** | 0.82 |
| R3+P1 | **0.15** ↓ | 0.91 |
| R3+P0 | **0.08** ↓ | 0.82 |

**Reject R3** — no F36 lift (S019-D8 not met). CE wall ~34s / ~$0.006 rough T4.

## Admin staging golden fixture bug (blocking promote-path smoke)

`eval_service.execute_eval_run`:

```python
fixture_path = _fixture_path() if loaded.corpus_profile == "fixture" else None
# None → load_golden_rows defaults to qa_pairs.json (fixture://)
```

When `corpus_profile=staging`, Admin should load `qa_pairs_staging.json`. Today it does not
(defaults to CI `qa_pairs.json`). **S019-D6 promote-path smoke cannot pass honestly until fixed.**

**Fix in progress (S019-D33 / ISS-008):** `eval_service._fixture_path(corpus_profile=…)` maps
`staging` → `qa_pairs_staging.json`; unit tests updated. Deploy write-api before promote smoke.

## Next (post A0–A4 + A3)

A0/A1/A2/A3/A4(+R3) complete. **R3 rejected.** Remaining: **lock ship**
(P1 packing ± optional R1). #162 deferred; #83 stays open for future CE work.

## Tentative ship lean

**#165 richer context packing (P1/P3)** as safest F42; optional **R1** if faith tradeoff accepted;
leave #83 for CE (R3 did not clear lift bar this spike); #158 no retrieval lift; #162 not proven.
