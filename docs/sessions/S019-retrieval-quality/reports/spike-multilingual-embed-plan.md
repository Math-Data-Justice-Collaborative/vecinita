# EV-016 spike — multilingual embeddings (#159)

> **Session:** S019 · **Cycle:** EV-016 · **Decision:** S019-D33 (workstream 4)  
> **Status:** plan — not run yet  
> **Depends on:** ISS-008 fix · expanded ES golden (workstream 3) · F41 shadow rebuild (EV-015)

## Why

Prod embedder is **English-only** `BAAI/bge-small-en-v1.5` (384-d FastEmbed,
`infra/modal/embedding_app.py`, ADR-008). ADR-013 assumes multilingual embeddings;
Spanish chunks are structurally under-served. Hybrid Hy1 still shows `es_rel=0`
(n=2) with `lang_match=1` — retrieval/judge gap, not just packing.

## Constraint

Prefer **stay on `vector(384)`** so F41 shadow re-embed does not need a dim
dual-write migration. Dim change → separate ADR-008 successor + Alembic.

## Candidate shortlist (FastEmbed / self-hosted)

| ID | Model | Dim | Notes |
|----|-------|-----|-------|
| **E0** | `BAAI/bge-small-en-v1.5` | 384 | Control (prod) |
| **E1** | `intfloat/multilingual-e5-small` | 384 | Strong multilingual; may need `query:` / `passage:` prefixes |
| **E2** | `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` | 384 | FastEmbed-common; lighter quality |
| **E3** | `BAAI/bge-small-zh-v1.5` | 384 | **Out** — not EN/ES |
| **E4** | `BAAI/bge-m3` | 1024 | **Defer** — dim migration |

**Locked (S019-D34):** measure **E0 + E1 + E2** (all 384-d).

Runners: `scripts/spike_embed_models_modal.py` + `scripts/spike_embed_retrieval.py`
(offline dense hit@5 on staging chunk texts — no prod pin flip until F36 lift).

**Note:** FastEmbed 0.4–0.6 does **not** ship `multilingual-e5-small`. Spike embeds via
**sentence-transformers** on Modal (E1 uses `query:` / `passage:` prefixes). Prod remains
FastEmbed until a ship decision + F41 shadow re-embed.

## Protocol

1. Expand staging golden ES coverage (workstream 3) — target ≥6 scored `es` rows.
2. Fix ISS-008 so Admin `corpus_profile=staging` loads `qa_pairs_staging.json`.
3. Stage candidate weights on Modal volume `embedding-models` (playground/spike
   path — do not flip prod pin until F36 lift clear).
4. F41 **shadow** re-embed staging corpus with candidate `embedding_model_id`.
5. Run fixed RAG cell: Hy1 (H7+P1) + control 1.5B; report EN/ES breakdown.
6. Gate: ES relevancy lift + EN not regressed vs E0 Hy1 (0.36 en_rel / 0.31 overall).

## Out of scope (this spike)

- Prod promote of new embed model
- Dim ≠ 384 migration
- Shipping without F36 evidence

## Artifacts (TBD)

- `reports/eval-experiments/*_embed-sweep.json`
- `reports/spike-multilingual-embed.md` (results + ship/no-ship)
