# BUG-2026-09-08-staging-supabase-crosswire

> Status: fixed in code, live staging remediation pending
> Severity: high
> Surface: staging admin auth (`/internal/v1/*`, `/jobs*`)
> Spec conformance: [Corpus: staging], [Corpus: feature-list.md §F34], [Spec: docs/api-contract.md §Authentication]

## Error description

Staging admin frontend reuses a valid signed-in admin browser session, but protected admin data routes return `401 Unauthorized`. The admin shell loads, then dashboard, corpus, and jobs fail to load data.

## Error logs

```text
Dashboard: Stats summary failed (401)
Corpus: {"detail":"Unauthorized"}
Jobs: stuck on Loading...
Browser token: localStorage key sb-camkatfbjguwvymfgdme-auth-token present
Decoded token: app_metadata.role=admin, now < exp
GET staging write /internal/v1/stats/summary with stored bearer token -> 401 {"detail":"Unauthorized"}
GET staging modal /jobs with stored bearer token -> 401 {"detail":"Unauthorized"}
Local .env: SUPABASE_URL=https://cfuvghdsuwactfeamtym.supabase.co
Browser auth storage key/project: camkatfbjguwvymfgdme
```

## Investigation

### Timeline

| Time | Note |
|------|------|
| 2026-09-08 | Live staging plunge found admin dashboard/corpus/jobs auth failures while public chat stayed healthy |
| 2026-09-08 | Verified stored browser token is valid and carries `app_metadata.role=admin` |
| 2026-09-08 | Confirmed repo auth code already verifies ES256 via JWKS, so current source is not hard-wired to old HS256 secrets |
| 2026-09-08 | Found local `.env` still points `SUPABASE_URL` at prod (`cfuvghdsuwactfeamtym`) |
| 2026-09-08 | Found staging frontend clearly uses distinct staging Supabase (`camkatfbjguwvymfgdme`) |
| 2026-09-08 | Hypothesis: staging secret sync from a shell sourced with `.env` cross-wired staging backend auth to prod Supabase |

### Hypotheses

| Hypothesis | Status | Evidence |
|-----------|--------|----------|
| Browser stored token expired | rejected | `now < exp` |
| Wrong role in JWT | rejected | `app_metadata.role=admin` |
| Source code cannot verify ES256 tokens | rejected | `packages/shared-schemas/vecinita_shared_schemas/auth.py` already uses JWKS + `algorithms=["ES256"]` |
| Staging backend auth config points at prod Supabase | likely | local `.env` uses prod `SUPABASE_URL`; staging FE uses staging Supabase; sync scripts push plain `SUPABASE_URL` into target envs |

## Repro test

- Path: `tests/bugs/test_bug_2026_09_08_staging_supabase_crosswire.py`
- Intent: fail closed when a staging secret sync tries to use the known prod Supabase URL.
- Status: red before fix (`ImportError`: guard missing), green after fix

## Interview record

- Intent: investigate, fix, and prepare deploy/verification path
- Repro environment: live staging for symptom, local tests for fix validation
- Root cause: user approved proceeding on the staging/prod Supabase cross-wire hypothesis

## Fix

Implemented:

1. Added `validate_supabase_url_for_target()` in `scripts/deploy/do_apps.py` and call it before staging write-api/admin auth secret sync.
2. Added an early guard in `scripts/deploy/sync_modal_secret.sh` so `MODAL_ENVIRONMENT=staging` refuses the known prod Supabase URL before any Modal secret push.
3. Added focused tests:
   - `tests/bugs/test_bug_2026_09_08_staging_supabase_crosswire.py`
   - `tests/smoke/test_modal_dm_secret_contract.py::test_sync_modal_secret_blocks_prod_supabase_url_in_staging`

## Verification

Passed:

```text
uv run pytest tests/bugs/test_bug_2026_09_08_staging_supabase_crosswire.py \
  tests/smoke/test_modal_dm_secret_contract.py \
  tests/unit/scripts/test_do_apps_env.py -q
..............
```

## Live remediation path

This code fix prevents recurrence, but the current staging environment likely still has the bad auth wiring. To repair live staging:

1. Create or resolve the canonical Supabase project's long-lived `staging` branch URL and staging-scoped keys.
2. Load that branch URL and its publishable/admin secrets into the shell, not the prod root values and not retired `camkatfbjguwvymfgdme`.
3. Re-sync the staging Modal DM secret and staging DO app secrets.
4. Redeploy staging Modal + DO admin surfaces.
5. Re-run staging admin browser checks and `tests/smoke/test_staging_ev002_admin.py` once the internal API key is available locally.

### Standalone staging project retirement

After the branch-backed staging path is green:

1. Verify no staging DO/Modal/GitHub secret still references `camkatfbjguwvymfgdme`.
2. Verify invite/reset URLs and admin login succeed against the branch-backed staging auth target.
3. Pause the standalone `vecinita-staging` Supabase project and keep it disabled through one more staging deploy/smoke cycle.
4. If no rollback is needed, close out the standalone project permanently.

## Prevention & countermeasures

- Fail closed on staging secret sync when auth points at the canonical prod project or the retired standalone staging project.
- Keep staging frontend and staging backends on the same branch-backed Supabase auth target before deploy validation.
- Keep one persistent `staging` branch and tear down extra preview branches promptly.
