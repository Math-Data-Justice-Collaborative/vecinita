# BUG-2026-08-06 — Security install-tools GitHub API flake

> Status: **fixed** (local; pending PR / merge)  
> Feature: tooling / CI (no Fn — [Corpus: WAIVED — no Fn yet; reason: tooling CI flake from RET-002; decided: 2026-08-06 issue triage])  
> Component: `scripts/security/install-tools.sh` · Husky pre-commit · `.github/workflows/ci.yml` `security` job  
> GitHub: [#227](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/227) · `S027-FLAKY-SECURITY-INSTALL` / RA-020  
> Session: S029-security-install-tools-flake

## Error description

`scripts/security/install-tools.sh` intermittently fails while resolving tool versions via
the GitHub Releases API (2ms / KICS / related). Transient 403/rate-limit, empty “latest”,
or network timeouts mark CI or local `make security-scan` red without a product defect.
Rerun usually succeeds.

## Error logs

```text
# S027 verification-report (main @ de1355c era) — paraphrased failure mode
[security] installing → …/bin (linux/amd64)
… Failed to fetch available versions from GitHub. …
# First security job failed at install-tools.sh; rerun of failed jobs passed.
```

| Field | Value |
|-------|--------|
| Failure modes | API 403 / rate limit · empty latest release · timeout |
| Observed | Flaky once on main; rerun OK |
| Spec | [Spec: docs/security/static-analysis.md] · [Spec: docs/sessions/S027-multilingual-embeddings/reports/qa-remediation.md] |

## Interview record (Phase 0)

| Gate | Answer |
|------|--------|
| Intent | New issue from #227 |
| symptom_type | Wrong output (install/CI red) |
| where_seen | Multiple — CI + local |
| when_started | Intermittent since S027 (~D41 / `de1355c`) |
| repro_frequency | Intermittent (rerun usually succeeds) |
| repro_environment | Both CI and local |
| user_severity | Critical / merges blocked |
| evidence_available | Partial (#227 + S027 reports) |
| already_tried | Nothing beyond rerun |
| remediation_path | Land on `main` ASAP (merge still needs approval) |
| success_criterion | Install survives simulated API 403/empty/timeout via retries; repro green |
| verification_checks | Full main CI parity (local) + gh watch PR/`main` |
| monitoring_followup | Watch `main` CI security path; user monitors flakes |

## Remediation path

**deploy-live equivalent for CI tooling:** PR → merge to `main` ASAP after approval.
No Modal/DO product deploy.

## Verification plan

| Check | Criterion |
|-------|-----------|
| Repro test | `tests/bugs/test_bug_2026_08_06_security_install_tools_flake.py` red → green |
| Local parity | `make ci-push` (or equivalent CI steps) on fix branch |
| Remote | `bash scripts/ci/watch_github_ci.sh` on PR branch; after merge on `main` |
| Policy | Hard-fail after N retries — do not silently skip scans |

## Investigation

### Timeline

| When | Event |
|------|--------|
| S027 (~D41) | Main CI security install flake noted; advisory QA-S027-004 |
| RET-002 | Queued as RA-020 / `S027-FLAKY-SECURITY-INSTALL` |
| 2026-08-06 | Issue #227 opened; S029 hotfix Phase 0 |

### Hypotheses

| # | Hypothesis | Status |
|---|------------|--------|
| H1 | `curl -fsSL` / `urllib` to `api.github.com` has no retries → single transient failure aborts install | **Confirmed** |
| H2 | Empty/draft “latest” release for KICS without fallback → hard fail | Mitigated separately (release walk); retries added for network |
| H3 | Unauthenticated rate limit; `GH_TOKEN` would raise quota | Documented optional token |

### Root cause

**Confirmed:** No retry/backoff on GitHub Releases API or asset downloads in
`install-tools.sh`. Transient API failures (exit 22 / “Failed to fetch available versions
from GitHub.”) abort the script under `set -e`.

## Repro test

| Test | Path | Status |
|------|------|--------|
| Transient GitHub API then success | `tests/bugs/test_bug_2026_08_06_security_install_tools_flake.py` | red → **green** |

## Fix

| File | Change |
|------|--------|
| `scripts/security/install-tools.sh` | `_curl_retry` + `_github_api_get`; optional `GH_TOKEN`/`GITHUB_TOKEN`; KICS Python retries; env `SEC_GITHUB_API_RETRIES` / `SEC_GITHUB_API_RETRY_DELAY` |
| `docs/security/static-analysis.md` | Document retry env + optional token |

## Prevention & countermeasures

| Gate | Answer |
|------|--------|
| recurrence_risk | Possible on similar unauthenticated GitHub fetches; unlikely for this script once fixed |
| detect_earlier | Main CI `security` job on PR |
| automated | Bug repro test only (done) |
| code_hardening | Pin known-good release tags (`config/security/tool-pins.conf`) — shipped same session |
| process | None — `static-analysis.md` updated |
| when / who | Now / agent |

### Planned actions

| Action | Status |
|--------|--------|
| Retries + repro test | Done (`a215220` / #233) |
| Pin 2ms / KICS / sbom-tool tags | Done (`config/security/tool-pins.conf` + install-tools) |
| Cursor rule | Pending Phase 5.1 AskQuestion |
