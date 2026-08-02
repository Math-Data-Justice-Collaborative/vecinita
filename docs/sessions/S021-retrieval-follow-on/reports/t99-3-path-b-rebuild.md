# T99.3 — Path B full E0 rebuild + BUG/guard

> **Session:** S021 · **Cycle:** EV-018 · **Date:** 2026-08-02  
> **Decision:** S021-D22  
> **Status:** completed

## Scope executed

1. **BUG** — `docs/bug-reports/BUG-2026-08-02-staging-basis-vector-wipe.md`  
2. **Guard** — `assert_corpus_reset_allowed` in `_attach_embeddings_impl`; `clear_embeddings()`; CI script + corpus-db-safety skill  
3. **Path B ops** — re-embed all 49 live docs / 213 chunks with E0 + promote  

## Why not store-backed F41 job alone

Staging `body_text` filled for **9/49** docs only. Store-backed `mode=reembed` would raise
`missing store body`. Ops script re-embeds **existing live chunk texts** (same pattern as
S019 E1 shadow spike), then promote.

Script: `docs/sessions/S021-retrieval-follow-on/scripts/path_b_e0_full_reembed.py`  
Report JSON: `docs/sessions/S021-retrieval-follow-on/reports/path-b-e0-rebuild.json`

| Field | Value |
|-------|--------|
| `rebuild_run_id` | `a0e8f32d-7e2e-4012-960c-2e956ceeba87` |
| Model | `BAAI/bge-small-en-v1.5` |
| Shadow | 47 http via write API + 2 `fixture://` via SQL (API rejects non-http URL scheme) |
| Promote | `promoted=True` docs=49 chunks=213 |

Aborted prior run `424e4d5f-…` marked `failed` (422 on fixture URLs).

## Post-promote probe

| Check | Before (T99.2) | After Path B |
|-------|----------------|--------------|
| empty@0.2 | 8/8 | **0/8** |
| top scores | ~0.03–0.07 | **~0.68–0.83** |
| one-hot live vectors | ~213 | **0** |
| rifreeclinic live↔Modal cosine | ≈ −0.05 | **1.0** |

Artifact: `probe-retrieve-pools.json` (rewritten).

## Code / test artifacts

| Artifact | Path |
|----------|------|
| Bug report | `docs/bug-reports/BUG-2026-08-02-staging-basis-vector-wipe.md` |
| Repro tests | `tests/bugs/test_bug_2026_08_02_staging_basis_vector_wipe.py` |
| Guard | `tests/helpers/corpus_db_guard.py`, `tests/unit/rag/conftest.py` |
| Call sites | e2e UJ-061/UJ-012 + unit tag-filtered use `clear_embeddings` |
| CI | `scripts/check_corpus_reset_guard.sh` |

## Next

- **T99.4** — completed (S021-D23; see `t99-4-e2e-closeout.md`)  
- **T99.5** — completed (`t99-5-f46-closeout.md`)  
- **M100** — F45 CE re-gate (AC-BB9) now that AC-FO1 pools are non-empty  

