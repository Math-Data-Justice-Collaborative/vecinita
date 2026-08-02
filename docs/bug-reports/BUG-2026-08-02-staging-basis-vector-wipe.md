# BUG-2026-08-02 — Staging embeddings wiped with test `basis_vector` one-hots

> Status: **resolved** (guard shipped; Path B E0 promote restored staging pools)  
> Feature: **F46** / corpus data integrity  
> Component: `tests/unit/rag/conftest.py` `attach_embeddings`, DO Managed Postgres staging  
> Related: BUG-2026-07-02 (TRUNCATE path); S021-D20–D22

## Error description

Staging ChatRAG retrieve pools were empty at default `min_retrieval_score=0.2` for all
golden fixture queries (UJ-061 / F46). Cosine between live stored embeddings and current
Modal E0 (`BAAI/bge-small-en-v1.5`) was ≈ 0 / negative. Live vectors were one-hot
`basis_vector` rows (`nonzero_count=1`, `max_abs=1.0` at index 1) — the deterministic test
embedding helper — not FastEmbed output.

## Error logs / evidence

Probe (read-only): `docs/sessions/S021-retrieval-follow-on/reports/probe-retrieve-pools.json`  
Promote history: `docs/sessions/S021-retrieval-follow-on/reports/promote-history-investigation.md`

| Check | Result |
|-------|--------|
| Pool @ `min_score=0.2` | 8/8 empty |
| Live ↔ Modal E0 cosine (same chunk text) | ≈ −0.05 |
| Live vector shape | one-hot basis (test helper) |
| Shadow E0 ↔ Modal E0 | 1.000 |
| Wipe timestamp | **2026-08-02 02:45 UTC** (all 213 embeddings) |
| Jobs / audit at wipe time | none → bypassed normal ingest/rebuild APIs |

## Investigation

| When (UTC) | Event |
|------------|--------|
| 2026-07-30 | E0 shadow rebuild `e3a78965` promoted for **2/49** docs only |
| 2026-08-01 | E1 shadow rebuild completed, not promoted |
| 2026-08-02 02:45 | Live embeddings overwritten with test one-hots |
| 2026-08-02 | S021 T99.2 diagnose + promote-history (S021-D20/D21) |
| 2026-08-02 | S021-D22 Path B + BUG/guard approved |

**Root cause:** `attach_embeddings()` / raw `DELETE FROM embeddings` lacked
`assert_corpus_reset_allowed()`. BUG-2026-07-02 guarded TRUNCATE only; UPSERT of synthetic
vectors still reached staging when `DATABASE_URL` pointed at `.ondigitalocean.com`.

**Secondary:** Prior E0 promote never covered golden fixture URLs (2/49 docs) — full Path B
re-embed still required after guard.

## Repro test

| Field | Value |
|-------|--------|
| Path | `tests/bugs/test_bug_2026_08_02_staging_basis_vector_wipe.py` |
| Assertion | `attach_embeddings` / `clear_embeddings` raise `RuntimeError` matching `managed Postgres` on DO hosts |
| Red | 2026-08-02 — connected / auth-failed instead of refusing |
| Green | 2026-08-02 — guard in `_attach_embeddings_impl` + `clear_embeddings` |

## Fix

| Layer | Change |
|-------|--------|
| Code | `assert_corpus_reset_allowed()` in `_attach_embeddings_impl`; new `clear_embeddings()` |
| Call sites | e2e/unit helpers use `clear_embeddings` instead of raw DELETE |
| CI | `scripts/check_corpus_reset_guard.sh` checks attach + clear helpers |
| Docs | Guard docstring updated for UPSERT class |

## Recovery (Path B — T99.3) — done 2026-08-02

| Field | Value |
|-------|--------|
| Script | `docs/sessions/S021-retrieval-follow-on/scripts/path_b_e0_full_reembed.py` |
| `rebuild_run_id` | `a0e8f32d-7e2e-4012-960c-2e956ceeba87` |
| Promote | 49 docs / 213 chunks |
| Probe | empty@0.2 = **0/8**; rifreeclinic live↔Modal cosine **1.0**; one-hot count **0** |

Note: store-backed F41 alone blocked on 40/49 missing `body_text`; ops re-embedded live chunk texts.

## Interview record

| Gate | Answer |
|------|--------|
| Intake / Path B | User: proceed Path B full E0 rebuild + BUG/guard (S021-D22) |
| Root cause | Agreed via S021-D21 promote-history (basis_vector wipe; not failed promote) |
| AskQuestion MCP | Unavailable this turn; approval via chat |

## Prevention & countermeasures

| Layer | Action |
|-------|--------|
| Automated | Guard on attach + clear; CI script coverage |
| Process | Keep corpus-db-safety skill; never source staging `DATABASE_URL` into pytest shells |
| Follow-up | Path B restore; optional rule note that UPSERT is as destructive as TRUNCATE |

## Cursor rule

Existing `.cursor/rules/corpus-db-safety.mdc` + skill already cover TRUNCATE. Update skill text
to mention `attach_embeddings` / `clear_embeddings` (same override tokens).
