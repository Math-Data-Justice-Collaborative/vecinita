# Security static analysis remediation (2026-07-28)

## Baseline (portable suite)

| Scanner | Result |
|---------|--------|
| OpenGrep | 9 ERROR |
| 2ms | 29 secrets (mostly `__pycache__` / false positives) |
| KICS | 16 HIGH |
| SBOM | OK |
| Grype | 14 High (npm) |
| Supabase advisors | empty after remediations (MFA + percent pool + `rls_auto_enable` revoke) |

## Remediations

- Wired `scripts/security/` + `config/security/` + `make security-scan` into CI, `make ci`/`ci-push`, and husky pre-push
- GitHub Actions shell-injection hardening (`publish-wiki.yml` env interpolation)
- OpenAPI global security + public `/health` documentation
- npm overrides / lockfile refresh: `react-router(-dom) 7.18.1`, `postcss`, `undici`, `js-yaml`, `brace-expansion`
- Removed stale per-app `package-lock.json` (SBOM noise)
- Bound-parameter `sqlalchemy.text` nosemgrep suppressions; demo JWT split; test URL construction
- Justified KICS / Grype ignores documented in `config/security/`
- Migration `20260728180000_revoke_rls_auto_enable_execute` + live Auth MFA / pool pins

## Gap follow-ups (same day)

- Pre-push loads `SUPABASE_ACCESS_TOKEN` / project ref from `.env` via
  `scripts/security/load_supabase_credentials.sh` (no longer soft-skips when only process env is empty)
- `apply_auth_config_from_toml.sh` also pins MFA + `db_max_pool_size_unit=percent`
- Docs: OpenGrep GHA parse-noise + KICS MEDIUM stance; `SUPABASE_PROJECT_REF` in `supabase/.env.example`

## Post-fix

`make security-scan` (with token in `.env` or CI secrets) → **PASS** (advisors fail_on=warn, 0 lints)
