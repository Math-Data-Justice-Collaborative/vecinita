# Security static analysis

Hard-fail suite for SAST, secrets, IaC, SBOM, and vulnerability scanning.

## Commands

```bash
make security-scan-install   # once (or after SEC_FORCE=1)
make security-scan           # hard-fail; also on husky pre-push + make ci / ci-push
```

Reports land in `.security-reports/` (gitignored). Binaries in `.tools/security/` (gitignored).

## Tools

| Tool | Role | Fail threshold |
|------|------|----------------|
| OpenGrep | SAST | ERROR |
| 2ms | Secrets | any finding |
| KICS | IaC / OpenAPI | high, critical |
| SBOM Tool | SPDX SBOM | must generate |
| Grype | Vulns (SBOM or dir) | high |
| Supabase advisors | DB security/perf | ERROR (when Supabase configured) |

Config: `config/security/` (KICS query excludes, Grype ignores, OpenGrep notes).

## Supabase advisors

Requires `SUPABASE_ACCESS_TOKEN` (`sbp_...`) and project ref (`SUPABASE_PROJECT_REF` /
`SUPABASE_PROJECT_ID` / `supabase/config.toml` `project_id`).

CI runs `scripts/security/remediate-supabase-advisors.sh` before the scan (drops
exposed `rls_auto_enable`, enables TOTP MFA + percentage Auth DB pool), then hard-fails
on advisor **WARN** and **ERROR** (`SEC_SUPABASE_ADVISOR_FAIL_ON=warn`).

Waive only with `SEC_SKIP_SUPABASE_ADVISORS=1` (not for production CI when secrets exist).

## Related

- `.gitleaks.toml` — complementary secret scan in `ci-guards`
- `docs/security/gitleaks-resolution.md`
