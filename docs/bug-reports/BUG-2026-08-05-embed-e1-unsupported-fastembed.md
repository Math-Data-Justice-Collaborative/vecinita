# BUG-2026-08-05 — Embed E1 pin unsupported by FastEmbed (H3 ask hang)

> Status: **fixed_deployed** (ops + code) — S027-D54 / S027-D55  
> Feature: **F70** / H3 smoke (blocks F71 cutover until corpus re-embed)  
> Component: Modal `vecinita-embedding` (`infra/modal/embedding_app.py`)  
> Related: BUG-2026-08-05-chatrag-ask-blocks-health (UH **fixed** via PR #220 — separate)

[Corpus: feature-list.md §F70]  
[Spec: docs/adr/ADR-048-multilingual-384-embeddings.md]  
[Spec: docs/config-spec.md §VECINITA_EMBED_RUNTIME]  
[Spec: docs/decisions/evolve-decisions.md §S027-D12]

## Error description

Staging H3 (`POST /api/v1/ask`) hangs ≥120–240s with **0 response bytes** even after
ChatRAG `/api/v1/warm` and a direct Modal LLM `/warm` (~44s) + `/generate` (~2s OK).
`/health` stays **ok** (UH fix verified). Root failure is **query embedding**, not LLM.

## Error logs

```text
# Modal EmbeddingService @modal.enter
ValueError: Model intfloat/multilingual-e5-small is not supported in TextEmbedding.

# Volume embedding-models (pre-fix)
models--qdrant--bge-small-en-v1.5-onnx-q   # legacy only
```

## Root cause

F70 default pin E1 + default `VECINITA_EMBED_RUNTIME=fastembed`. FastEmbed rejects E1
(S019 spike). S027-D12 ST fallback was not implemented. `/health` does not load the model.

## Fix (S027-D55: ops then code)

1. **Ops (Modal CLI):**
   - `modal secret create vecinita-embedding VECINITA_EMBED_RUNTIME=sentence_transformers VECINITA_EMBEDDING_MODEL_ID=intfloat/multilingual-e5-small --force`
   - Wire secret on stage / `EmbeddingService` / ASGI
   - `modal run …::stage_embedding_weights` → volume has `models--intfloat--multilingual-e5-small`
   - `modal deploy infra/modal/embedding_app.py`
2. **Code:** `_load_backend` catches FastEmbed `ValueError` → ST fallback (S027-D12)

## Verification (2026-08-05)

| Probe | Result |
|-------|--------|
| Embed `/health` | `runtime=sentence_transformers`, E1 pin |
| Embed `/embed` | 384-d ~0.4s |
| H3 `POST /api/v1/ask` | **200 ~2.6s** (no hang); answer returned; `sources=[]` until F71 re-embed |

## Repro test

| Field | Value |
|-------|--------|
| Path | `tests/bugs/test_bug_2026_08_05_embed_e1_unsupported_fastembed.py` |
| Assert | FastEmbed rejects E1 → ST backend; supported FastEmbed pin stays FastEmbed |
| Red → green | 2026-08-05 |

## Interview record

| Gate | Decision |
|------|----------|
| S027-D54 | Investigate H3 hang |
| S027-D55 | **2 then 1** — ops ST + stage, then code fallback |
