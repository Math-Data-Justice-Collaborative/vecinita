# EV-016 #159 multilingual embed spike — results

> **Decisions:** S019-D34 / S019-D35 · **Artifact:** `eval-experiments/20260801T020331Z_embed-sweep.json`  
> **Method:** Offline dense hit@5 — re-embed staging chunk texts + golden queries on Modal
> (sentence-transformers; FastEmbed 0.4–0.6 lacks `multilingual-e5-small`)

## Cells

| Cell | Model | Dim |
|------|-------|-----|
| E0 | `BAAI/bge-small-en-v1.5` (control / prod) | 384 |
| E1 | `intfloat/multilingual-e5-small` (+ query/passage prefixes) | 384 |
| E2 | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | 384 |

Corpus: 211 chunks · Golden hits: 15 (8 en / 7 es) after A+B ES ingest + golden expand.

## Results

### hit@5 URL match

| Cell | hit_rate | en_hit | es_hit | notes |
|------|----------|--------|--------|-------|
| **E0** | **1.00** | 1.00 | 1.00 | Saturated |
| **E1** | **1.00** | 1.00 | 1.00 | Tied with E0 |
| E2 | 0.87 | 0.875 | 0.86 | **Worse** — drop |

### Finer rank signal (expected URL position among top-5)

| Cell | mean_rank (when hit) | rank@1 rate | es rank@1 |
|------|----------------------|-------------|-----------|
| E0 | 1.67 | 0.60 | 3 / 7 |
| **E1** | **1.33** | **0.73** | **4 / 7** |
| E2 | 1.92 | 0.40 | 1 / 7 |

## Interpretation

1. After A+B corpus expansion, **E0 already hits expected ES URLs @5** — prior `es_rel=0`
   was mainly **answer relevancy / judge / thin ES corpus**, not pure miss.
2. **E1 improves ranking** (better mean_rank / rank@1) while matching hit@5 — promising but
   not enough alone to ship without F36 LLM relevancy on a shadow revision.
3. **E2 underperforms** — reject.
4. FastEmbed 0.4–0.6 cannot load E1; ship path needs FastEmbed upgrade / custom ONNX or
   sentence-transformers embedding service (ADR-008 successor).

## Recommendation

| Action | Verdict |
|--------|---------|
| Expand ES corpus + golden (A+B) | **Done — keep** |
| Ship embed swap inside F42 now | **No** — keep prod E0 for F42=H7+P1 |
| E1 follow-on (#159) | **Yes, optional** — F41 shadow + Hy1 F36 LLM (rank edge warrants it) |
| E2 | **Reject** |

F42 ship candidate stays **H7+P1** on current embedder; #159 remains open for E1.
