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
| KICS | IaC / OpenAPI | high, critical (`SEC_KICS_FAIL_ON`) |
| SBOM Tool | SPDX SBOM | must generate |
| Grype | Vulns (SBOM or dir) | high (`SEC_GRYPE_FAIL_ON`) |
| Supabase advisors | DB security/perf | WARN + ERROR (`SEC_SUPABASE_ADVISOR_FAIL_ON=warn`) |

These are pinned by `make security-scan` and the CI `security` job. Loosening requires an
explicit env override (not recommended). OpenGrep WARNING and KICS medium/low/info are
reported in tool output but are not hard-fail thresholds (noise floor: hundreds of
OpenAPI/IaC INFO–MEDIUM hits).

Config: `config/security/` (KICS query excludes, Grype ignores, OpenGrep notes).
2ms ignores gitignored local secret files (`.env`, `prod.env`, operator `*-spec.yaml`
exports); secrets in tracked files still hard-fail. Complementary: gitleaks in `ci-guards`.

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
