# Security static analysis

Hard-fail suite for SAST, secrets, IaC, SBOM, and vulnerability scanning.

## Commands

```bash
make security-scan-install   # once (or after SEC_FORCE=1)
make security-scan           # hard-fail; also on husky pre-push + make ci / ci-push
```

Reports land in `.security-reports/` (gitignored). Binaries in `.tools/security/` (gitignored).

## Tools

| Tool | Role | Fail threshold (strictest hard-block) |
|------|------|----------------------------------------|
| OpenGrep | SAST | ERROR (`--error --severity=ERROR`) |
| 2ms | Secrets | any finding in tracked paths |
| KICS | IaC / OpenAPI | medium, high, critical (`SEC_KICS_FAIL_ON`) |
| SBOM Tool | SPDX SBOM | must generate |
| Grype | Vulns (SBOM or dir) | high (`SEC_GRYPE_FAIL_ON`) |
| Supabase advisors | DB security/perf | WARN + ERROR (`SEC_SUPABASE_ADVISOR_FAIL_ON=warn`) |

These are pinned by `make security-scan` and the CI `security` job. Loosening requires an
explicit env override (not recommended). OpenGrep WARNING findings are fixed when practical
(pinned Actions SHAs, etc.) but WARNING is not a hard-fail threshold. KICS LOW/INFO remain
non-blocking; justified MEDIUM OpenAPI noise excludes live in
`config/security/kics-exclude-queries.txt`.

Config: `config/security/` (KICS query excludes, Grype ignores, OpenGrep notes).
2ms ignores gitignored local secret files (`.env`, `prod.env`, operator `*-spec.yaml`
exports); secrets in tracked files still hard-fail. Complementary: gitleaks in `ci-guards`.

## Pre-push + `.env`

Husky `scripts/ci/pre_push.sh` runs `make security-scan`. Before deciding whether to skip
Supabase advisors, it loads credentials via
`scripts/security/load_supabase_credentials.sh` (parse-only from `.env` / `prod.env`, plus
`supabase/config.toml` `project_id`). Set `SUPABASE_ACCESS_TOKEN` in `.env` (and optionally
`SUPABASE_PROJECT_REF`) so local pushes hard-fail on advisor WARN/ERROR the same way CI does.

Waive with `SEC_SKIP_SUPABASE_ADVISORS=1` only when intentionally offline.

## Supabase advisors

Requires `SUPABASE_ACCESS_TOKEN` (`sbp_...`) and project ref (`SUPABASE_PROJECT_REF` /
`SUPABASE_PROJECT_ID` / `supabase/config.toml` `project_id`).

CI runs `scripts/security/remediate-supabase-advisors.sh` before the scan (drops
exposed `rls_auto_enable`, enables TOTP MFA + percentage Auth DB pool), then hard-fails
on advisor **WARN** and **ERROR** (`SEC_SUPABASE_ADVISOR_FAIL_ON=warn`).

Auth `db_max_pool_size_unit=percent` is **not** expressible in `config.toml` (CLI gap).
It is pinned by the remediator and by `scripts/supabase/apply_auth_config_from_toml.sh`
(see comment in `supabase/config.toml`).

Waive only with `SEC_SKIP_SUPABASE_ADVISORS=1` (not for production CI when secrets exist).

## OpenGrep GHA metavariable noise

Community rules `curl-eval` / `gha-curl-pipe-shell` emit **parse errors** (not findings) on
some `.github/workflows/*.yml` lines that embed `${{ ... }}` inside bash snippets. Those
lines are not fully covered by those rules; do not treat the parse errors as scan failures.
Prefer env-block interpolation (already used in hardened workflows) when editing Actions.

## KICS MEDIUM / LOW backlog

Fail-on is **medium,high,critical**. Remaining LOW/INFO volume is dominated by OpenAPI
schema shape (optional fields, INFO-level style). Justified MEDIUM excludes for
non-actionable OpenAPI pattern/response-$ref queries live in
`config/security/kics-exclude-queries.txt`. Re-triage when touching IaC/OpenAPI.

## Related

- `.gitleaks.toml` — complementary secret scan in `ci-guards`
- `docs/security/gitleaks-resolution.md`
