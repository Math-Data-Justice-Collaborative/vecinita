# Security static analysis remediation (2026-07-28)

## Baseline (portable suite)

| Scanner | Result |
|---------|--------|
| OpenGrep | 9 ERROR |
| 2ms | 29 secrets (mostly `__pycache__` / false positives) |
| KICS | 16 HIGH |
| SBOM | OK |
| Grype | 14 High (npm) |
| Supabase advisors | skipped locally (no `SUPABASE_ACCESS_TOKEN`); CI runs when secret present |

## Remediations

- Wired `scripts/security/` + `config/security/` + `make security-scan` into CI, `make ci`/`ci-push`, and husky pre-push
- GitHub Actions shell-injection hardening (`publish-wiki.yml` env interpolation)
- OpenAPI global security + public `/health` documentation
- npm overrides / lockfile refresh: `react-router(-dom) 7.18.1`, `postcss`, `undici`, `js-yaml`, `brace-expansion`
- Removed stale per-app `package-lock.json` (SBOM noise)
- Bound-parameter `sqlalchemy.text` nosemgrep suppressions; demo JWT split; test URL construction
- Justified KICS / Grype ignores documented in `config/security/`

## Post-fix

`make security-scan` (with `SEC_SKIP_SUPABASE_ADVISORS=1` locally) → **PASS**
