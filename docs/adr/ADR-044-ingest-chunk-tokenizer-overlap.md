# ADR-044: Ingest HF tokenizer + default chunk overlap

**Status**: Accepted  
**Date**: 2026-08-02  
**Session**: S022 / EV-019 (F49, related F47–F48)  
**Decisions**: S022-D15, S022-D16; RD-223, RD-224

## Context

Ingest chunking (`packages/ingest`) packs paragraphs using `len(text.split())` as a
token estimate with **no overlap**. Config names this `chunk_size_tokens`, which is
misleading. Overlap at boundaries can improve retrieval recall; sizing should match a
real tokenizer for the pinned embed model.

Issue [#160](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/160)
asked for investigation first; EV-019 ships after Phase 0C chose HF tokenizer +
non-zero default overlap.

## Decision

1. **Tokenizer**: Size chunks with the HuggingFace tokenizer for the pinned embed model
   **`BAAI/bge-small-en-v1.5`** (same pin as ADR-008 / E0). Prefer `transformers`
   `AutoTokenizer` (already inventoried) or equivalent `tokenizers` API in
   `packages/ingest`; 04/07 may pin a lightweight load path for Modal workers.
2. **Overlap**: Introduce `chunk_overlap_tokens` / `VECINITA_CHUNK_OVERLAP_TOKENS` with
   **default 32**. Validate `0 ≤ overlap < chunk_size_tokens`.
3. **Corpus impact**: Changing default overlap / tokenizer vs prior word-split chunks
   means existing live chunks may diverge until rebuild (`job_type=rebuild` /
   `rechunk`). Document in config-spec + F41 notes; Path A may ship code with default
   32 for **new** ingest; operators rebuild when ready.
4. **Job options**: Allow per-job override of `chunk_size_tokens` and
   `chunk_overlap_tokens` on ingest (and rebuild rechunk).

## Consequences

- Slightly higher storage / embed cost vs overlap 0.
- Dependency: ingest path needs HF tokenizer available in Modal DM image (and tests).
- Word-count sizing becomes deprecated; keep a compatibility note in chunker docs.
- Complements F47 (hash skip) — overlap/tokenizer changes change `content_hash` only when
  **body** text changes; rechunk-without-rescrape is a rebuild concern, not hash skip.

## Alternatives considered

| Option | Why not |
|--------|---------|
| Keep word≈token + document only | Rejected in Phase 0C (Q4=2) |
| Default overlap 0 (opt-in) | Rejected in Phase 0C (Q3=2) |
| Separate tokenizer from embed model | Risk of size drift vs FastEmbed; stick to E0 id |
