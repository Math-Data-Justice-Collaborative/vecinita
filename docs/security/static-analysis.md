# Security static analysis

Hard-fail suite for SAST, secrets, IaC, SBOM, and vulnerability scanning.

## Commands

```bash
make security-scan-install   # once (or after SEC_FORCE=1)
make security-scan           # hard-fail; also on husky pre-commit + make ci / ci-push
```

Reports land in `.security-reports/` (gitignored). Binaries in `.tools/security/` (gitignored).

## Tool install retries (#227)

`scripts/security/install-tools.sh` retries GitHub API and asset downloads on transient
failures (rate limit / empty latest / network). Hard-fail after N attempts — do not skip
scans.

| Env | Default | Role |
|-----|---------|------|
| `SEC_GITHUB_API_RETRIES` | `5` | Max attempts for API + downloads |
| `SEC_GITHUB_API_RETRY_DELAY` | `2` | Seconds between attempts (`0` in tests) |
| `GH_TOKEN` / `GITHUB_TOKEN` | unset | Optional Bearer auth for `api.github.com` (higher quota). **Never commit tokens.** |

CI already exposes `GITHUB_TOKEN` to Actions; local commits may set `GH_TOKEN` from `gh auth token` when rate-limited.

## Tool version pins (#227 Phase 5)

`config/security/tool-pins.conf` pins GitHub release tags for **2ms**, **KICS**, and
**sbom-tool** so installs use `…/releases/download/<tag>/…` instead of `/latest` or empty
draft “latest” releases. Bump pins after verifying assets exist on the tag.

| Env | Default | Role |
|-----|---------|------|
| `SEC_PIN_2MS_TAG` | from `tool-pins.conf` | 2ms release tag |
| `SEC_PIN_KICS_TAG` | from `tool-pins.conf` | KICS release tag (must include platform tarballs) |
| `SEC_PIN_SBOM_TOOL_TAG` | from `tool-pins.conf` | sbom-tool release tag |
| `SEC_TOOLS_UNPIN` | `0` | `1` = ignore pins; use API / `/latest` (tests + emergency) |
| `SEC_TOOLS_PINS_FILE` | `config/security/tool-pins.conf` | Alternate pins file path |

OpenGrep and Grype still use vendor installers (not tag-pinned here).

## Tools

| Tool | Role | Fail threshold (strictest hard-block) |
|------|------|----------------------------------------|
| OpenGrep | SAST | ERROR (`--error --severity=ERROR`) |
| 2ms | Secrets | any finding in tracked paths |
| KICS | IaC / OpenAPI | medium, high, critical (`SEC_KICS_FAIL_ON`) |
| SBOM Tool | SPDX SBOM (+ licenses via ClearlyDefined) | must generate |
| Grype | Vulns (SBOM or dir) | high (`SEC_GRYPE_FAIL_ON`) |
| Supabase advisors | DB security/perf | WARN + ERROR (`SEC_SUPABASE_ADVISOR_FAIL_ON=warn`) |

These are pinned by `make security-scan` and the CI `security` job. Loosening requires an
explicit env override (not recommended). OpenGrep WARNING findings are fixed when practical
(pinned Actions SHAs, etc.) but WARNING is not a hard-fail threshold. KICS LOW/INFO remain
non-blocking; justified MEDIUM OpenAPI noise excludes live in
`config/security/kics-exclude-queries.txt`.

Config: `config/security/` (KICS query excludes, Grype ignores, OpenGrep notes).
2ms ignores gitignored local secret files (`.env`, `.env.staging`, `prod.env`,
`.staging-db-url.local`, `.staging-supabase-db-pass.local`,
`.staging-supabase-ref.local`, `.staging-supabase-keys.local`, operator
`*-spec.yaml` exports); secrets in tracked files still hard-fail. Complementary:
gitleaks in `ci-guards`.

## SBOM licenses

`sbom-tool` discovers packages via Microsoft Component Detection but does **not** fill
`licenseDeclared` / `licenseConcluded` unless you opt in. By default every field is
`NOASSERTION` (known Microsoft behavior when `-li`/`-pm` are omitted).

Our suite enables:

| Step | Env | Effect |
|------|-----|--------|
| `-li true` | `SEC_SBOM_FETCH_LICENSES=1` (default) | Fetch from [ClearlyDefined](https://clearlydefined.io) (often fails with HTTP 524 on bulk) |
| `-pm true` | same | Parse package metadata when the detector supports it (limited for npm/uv) |
| `-lto` | `SEC_SBOM_LICENSE_TIMEOUT_SEC` (default `30`) | ClearlyDefined timeout |
| `enrich_sbom_licenses.py` | `SEC_SBOM_ENRICH_LICENSES=1` (default) | Post-pass: resolve licenses from npm/PyPI registries into the SPDX JSON; also write `sbom/python-licenses.json` from `uv.lock` |

**Python gap:** Component Detection’s UvLock detector finds packages, but `sbom-tool` currently
emits an npm-only SPDX package list. Use `python-licenses.json` (or `audit-licenses`) for
PyPI commercial/OSS review until upstream includes UvLock in the SPDX document.

The default timeout is intentionally short so transient ClearlyDefined stalls do
not make local `make security-scan` / `make ci-push` appear hung for minutes at
a time. Set `SEC_SBOM_LICENSE_TIMEOUT_SEC` higher only when you intentionally
want to wait longer for the remote license service.

Set `SEC_SBOM_FETCH_LICENSES=0` / `SEC_SBOM_ENRICH_LICENSES=0` only when offline.

## Pre-commit + `.env` (F62)

Husky `scripts/ci/pre_commit.sh` runs `make security-scan` (moved off lean pre-push).
Before deciding whether to skip Supabase advisors, it loads credentials via
`scripts/security/load_supabase_credentials.sh` (parse-only from `.env` / `prod.env`, plus
`supabase/config.toml` `project_id`). Set `SUPABASE_ACCESS_TOKEN` in `.env` (and optionally
`SUPABASE_PROJECT_REF`) so local commits hard-fail on advisor WARN/ERROR the same way CI does.

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
`config/security/kics-exclude-queries.txt`. The exclude list also carries the
local Docker Desktop Postgres bootstrap exception: the dev `pgvector` container
must keep its stock init privileges so `with_local_postgres.sh` can boot on
macOS Docker Desktop. Re-triage when touching IaC/OpenAPI or local compose.

## Related

- `.gitleaks.toml` — complementary secret scan in `ci-guards`
- `docs/security/gitleaks-resolution.md`
