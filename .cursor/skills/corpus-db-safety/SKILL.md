---
name: corpus-db-safety
description: >
  Prevent accidental corpus wipes on DO Managed Postgres when running pytest, seeds, or
  eval fixtures. Use before any test run, seed_eval_corpus, load_corpus, or when sourcing
  prod.env with DATABASE_URL. Blocks TRUNCATE against .ondigitalocean.com hosts unless
  explicit operator override is set.
---

# Corpus DB safety (staging Postgres)

The **corpus lives on DO Managed Postgres** (`vecinita-staging`), not Supabase.
Test helpers that `TRUNCATE` corpus tables must **never** run against staging unless
the operator explicitly opts in.

**Incident:** July 2026 — `seed_eval_corpus()` wiped ~40 ingested documents when pytest
ran with `prod.env` sourced (`DATABASE_URL` → `.ondigitalocean.com`).

## Rules for agents

| Do | Don't |
|----|-------|
| Run `pytest` / `make test-py` with **local** Postgres (`localhost`, `127.0.0.1`, `postgres`) | Source `prod.env` then run unit/integration tests that reset corpus |
| Use `VECINITA_ALLOW_CORPUS_RESET=1` + ack only for **intentional** staging maintenance | Call `seed_eval_corpus()` or `reset_corpus_tables()` against staging |
| Check `DATABASE_URL` host before any corpus TRUNCATE | Assume CI guard alone protects staging — env in shell matters |

## Guard implementation

| Artifact | Role |
|----------|------|
| `tests/helpers/corpus_db_guard.py` | `assert_corpus_reset_allowed()` — blocks `.ondigitalocean.com` / `.supabase.co` |
| `tests/unit/rag/conftest.py` | Calls guard before corpus reset |
| `scripts/check_corpus_reset_guard.sh` | CI guard (`make ci-guards`) |

## Operator override (destructive)

```bash
export VECINITA_ALLOW_CORPUS_RESET=1
export VECINITA_CORPUS_RESET_ACK=staging-wipe-confirmed
# then run the maintenance command only
```

## Safe patterns

**Local tests (recommended):**

```bash
export DATABASE_URL='postgresql://postgres:postgres@localhost:5432/vecinita_test'
make test-py
```

**Staging health (read-only):**

```bash
set -a && source prod.env && set +a
bash scripts/infra/do_verify_required_secrets.sh
bash scripts/deploy/staging_smoke.sh
# H2 uses SELECT 1 / alembic — does not TRUNCATE corpus
```

**Separate shells:** use one shell for `prod.env` + DO deploy, another for pytest.

## Recovery

Daily DO backups — see `docs/staging-runbook.md` §Corpus protection and
`scripts/infra/do_verify_staging_backups.sh`.

## Related

- [do-secrets-sync](../do-secrets-sync/SKILL.md) — same `prod.env` file, different risk
- [data-management](../data-management/SKILL.md) — migrations + seed policy
- [15-service-health](../15-service-health/SKILL.md) — staging checks without corpus reset
