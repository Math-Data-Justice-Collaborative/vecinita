# Promote history investigation — why live ≠ E0

> **Session:** S021 · **Cycle:** EV-018 · **Date:** 2026-08-02  
> **Follows:** `diagnose-f46-empty-retrieve.md` (user chose investigate before Path B)

## Verdict

**F41 promote is not the smoking gun for today’s empty pools.**  
Live vectors were **overwritten after promote** with **synthetic one-hot test embeddings** (`basis_vector`).  
E0 shadow embeddings still match current Modal E0 (cosine **1.0**).

## Timeline

| When (UTC) | Event |
|------------|--------|
| 2026-07-30 22:56 | Rebuild run `e3a78965-…` created — model `BAAI/bge-small-en-v1.5` |
| 2026-07-30 23:39 | Run marked **promoted**; **60** chunks written for **2** PMC docs only |
| 2026-08-01 01:39 | Ingest job added 7 ES `vecina.wrwc.org` docs (normal) |
| 2026-08-01 02:11 | E1 shadow rebuild `1fa1dec9-…` (`multilingual-e5-small`) **completed, not promoted** |
| **2026-08-02 02:45** | **All 213 live embeddings rewritten** (same minute); almost no chunk churn |

No `jobs` / `audit_log` rows at 2026-08-02 02:45 → bypassed normal ingest/rebuild APIs.

## Evidence

### 1. Promote coverage was tiny

| Metric | Value |
|--------|-------|
| Live docs | 49 |
| E0 shadow docs | **2** (PMC11688187, PMC4201531) |
| E0 shadow embeddings | 60 |
| Live docs **not** in E0 shadow | **47** |
| Document revisions for E0 | 2 |

Promote only ever replaced retrieval for those two PMC URLs. Golden staging fixtures (rifreeclinic, wrwc, …) were **never** in that promote set.

### 2. Shadow E0 still correct; live is not

For promoted PMC chunks (identical text md5):

| Pair | Cosine |
|------|--------|
| shadow_e0 ↔ Modal E0 now | **1.000** |
| shadow_e0 ↔ live stored | **≈ 0** |
| live stored ↔ Modal E0 now | **≈ 0** |

`exact_match` shadow↔live: **0 / 60**.

### 3. Live vectors are test `basis_vector` one-hots

Sampled live embeddings:

- `nonzero_count = 1`
- `max_abs = 1.0` at index **1**

That matches `tests/unit/rag/conftest.py` `basis_vector(index)` used by `attach_embeddings()`, not FastEmbed output.

### 4. Promote code path itself looks sound

`rebuild_promote.py` deletes scoped live chunks (CASCADE embeddings), copies shadow chunks/embeddings, writes revisions. Unit tests cover copy. Staging symptom is **post-promote overwrite**, not a failed shadow→live copy of bad vectors (shadow is good).

## Root-cause class (refined)

| Layer | Finding |
|-------|---------|
| Primary (current outage) | **Staging corpus contaminated by test `attach_embeddings` / one-hot vectors** on 2026-08-02 02:45 UTC |
| Secondary (pre-existing) | **E0 promote never covered full corpus** (2/49 docs) — Path B full re-embed still required for golden URLs |
| Guard gap | `attach_embeddings()` does **not** call `assert_corpus_reset_allowed()`; several e2e helpers `DELETE FROM embeddings` without the DO host guard |

Same incident class as BUG-2026-07-02 (pytest/helpers against `.ondigitalocean.com`).

## Implications for T99.3

1. **Do not** “re-promote” `e3a78965` alone — only restores 2 PMC docs; golden set still broken.  
2. **Do** full **Path B**: F41 re-embed **all** live docs with E0 + promote (or equivalent ops re-embed).  
3. **Should** file `BUG-2026-08-02-staging-basis-vector-wipe` + harden `attach_embeddings` / DELETE helpers with corpus DB guard (can be same cycle or nested hotfix).  
4. Optional fast partial: copy shadow→live for the 2 PMC docs only (does not unblock UJ-061 golden).

## Recommended next

Approve Path B full E0 rebuild **and** open BUG + guard fix so this cannot recur.
