# T99.2 — Diagnose F46 empty retrieve

> **Session:** S021 · **Cycle:** EV-018 · **Date:** 2026-08-02  
> **Status:** completed · **Root-cause class:** staging test-vector wipe + incomplete E0 promote  
> **Promote follow-up:** `promote-history-investigation.md`

## Probe (read-only staging)

Script: `docs/sessions/S021-retrieval-follow-on/scripts/probe_retrieve_pools.py`  
JSON: `docs/sessions/S021-retrieval-follow-on/reports/probe-retrieve-pools.json`

| Check | Result |
|-------|--------|
| Host | `*.ondigitalocean.com` staging |
| Corpus | 49 docs / 213 chunks / 213 embeddings |
| Dim | corpus **384** = live Modal embed **384** (`dim_match=true`) |
| Golden URLs | **0 missing** in sample (fixture URLs present) |
| Pool @ `min_score=0.2` | **8/8 empty** |
| Pool @ `min_score=0.0` | **0/8 empty**, but top scores **~0.03–0.07** (noise) |

## Smoking gun

Same rifreeclinic chunk text:

| Pair | Cosine |
|------|--------|
| Stored live embedding ↔ live Modal E0 embed | **≈ -0.05** (uncorrelated) |
| Live Modal embed ↔ itself (repeat) | **1.00** |

Self-retrieve of that chunk’s text returns unrelated fixture rows at ~0.03.

→ Not a language filter bug; not missing golden URLs; not “threshold slightly high.”
Live `embeddings` are **not in the current E0 (`BAAI/bge-small-en-v1.5`) space**.

## Rebuild history (staging)

| Run | Model | Status | Notes |
|-----|-------|--------|-------|
| `e3a78965-…` | `BAAI/bge-small-en-v1.5` | promoted | shadow count only **60** (partial) |
| `1fa1dec9-…` | `intfloat/multilingual-e5-small` | completed (not promoted) | E1 spike; shadow **211** |

Modal embed app still pins `BAAI/bge-small-en-v1.5` (`infra/modal/embedding_app.py`).

## TP3 outcome

| Step | Verdict |
|------|---------|
| 1. Embed ↔ corpus pin | **ROOT CAUSE** |
| 2. Fixture URLs | Pass (present) |
| 3. `min_retrieval_score` | Symptom amplifier only — lowering cannot recover correct neighbors |
| 4. Code bug | Unlikely for universal empty; ask-sources wire OK (TC-186) |

## Recommended fix (T99.3)

**Path B:** F41 re-embed + promote **full** live corpus with **E0** `BAAI/bge-small-en-v1.5`, then
re-run pool probe (expect pool@0.2 > 0 and same-text cosine ≫ 0.2).

Also: BUG + harden `attach_embeddings` / e2e `DELETE FROM embeddings` with corpus DB guard
(promote history shows live vectors are one-hot `basis_vector`s written 2026-08-02 02:45 UTC).

Do **not** ship a permanent `min_retrieval_score` drop as the fix.  
Do **not** re-promote `e3a78965` alone (only 2/49 docs).

## CI

- TC-186 PASS (stub)
- TC-185 needs local/CI Postgres (skipped when Docker down)
