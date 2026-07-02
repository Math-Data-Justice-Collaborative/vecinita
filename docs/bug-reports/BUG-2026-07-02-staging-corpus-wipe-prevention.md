# BUG-2026-07-02 — Staging corpus wiped by eval seed TRUNCATE

> Status: **resolved** (prevention shipped)  
> Feature: **F36** / corpus data integrity  
> Component: `tests/unit/rag/conftest.py`, DO Managed Postgres `vecinita-staging`

## Error description

Staging admin Corpus tab shows only 4 `fixture://corpus/...` documents. ~40 real ingested
URLs (June 27 ingest) are gone from `documents` / `chunks` / `embeddings`.

## Root cause

`seed_eval_corpus()` calls `_reset_corpus_tables_impl()`, which `TRUNCATE`s corpus tables
before loading fixtures. It was invoked with staging `DATABASE_URL` from `prod.env` during
eval debugging on **2026-07-01 23:31 UTC**. TRUNCATE bypasses audit logging — no
`document.deleted` rows for real URLs.

Corpus was on **DO Managed Postgres** (`vecinita-staging`), not Supabase. Supabase holds
auth only (ADR-026).

## Fix (prevention)

| Layer | Change |
|-------|--------|
| Code | `tests/helpers/corpus_db_guard.py` — block TRUNCATE on `.ondigitalocean.com` / Supabase hosts |
| Tests | `tests/unit/test_corpus_db_guard.py` |
| CI | `scripts/check_corpus_reset_guard.sh` in `make ci-guards` |
| DO ops | `scripts/infra/do_verify_staging_backups.sh` — verify daily backups via DO API |
| Docs | `docs/staging-runbook.md` §Corpus protection, `infra/do/README.md` |

Operator override (intentional wipe only):

```bash
export VECINITA_ALLOW_CORPUS_RESET=1
export VECINITA_CORPUS_RESET_ACK=staging-wipe-confirmed
```

## Recovery (not automated)

Fork `vecinita-staging` from a DO daily backup **before 2026-07-01 23:31 UTC** (e.g.
2026-07-01 16:41 UTC backup still contains June 27 corpus). See staging runbook §Corpus
protection.

**2026-07-02:** Restored via `scripts/infra/do_restore_staging_corpus.sh` — fork
`vecinita-staging-restored-20260701` (42 real documents); `DATABASE_URL` swapped on DO
backends + `prod.env`; Alembic upgraded to head.

Re-ingest alternative: ~40 URLs remain in `audit_log` where `event_type = 'document.created'`
and URL not like `fixture://%`.

## Timeline

| When | Event |
|------|-------|
| 2026-06-27 | ~40 real documents ingested (audit_log) |
| 2026-07-01 23:31 UTC | All documents replaced by 4 fixtures (TRUNCATE + seed) |
| 2026-07-02 | Guard + DO backup verification shipped |
