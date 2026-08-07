---
session_id: S029-security-install-tools-flake
type: hotfix
status: in_progress
branch: fix/S029-security-install-tools-flake
started_at: 2026-08-06
intent: "Harden flaky scripts/security/install-tools.sh GitHub API version fetch (#227 / S027-FLAKY-SECURITY-INSTALL / RA-020)"
orchestrator: 14-hotfix
github_issue: 227
context_briefs: []
standing_docs_touched:
  - docs/security/static-analysis.md
  - docs/bug-reports/BUG-2026-08-06-security-install-tools-flake.md
---

# Session S029 — Security install-tools flake (#227)

## Intent

Surgical hotfix for intermittent failures in `scripts/security/install-tools.sh` when
resolving tool versions via the GitHub Releases API (rate limits, empty “latest”,
transient network). Queued from S027 / RET-002 as `S027-FLAKY-SECURITY-INSTALL` (RA-020).

[Corpus: WAIVED — no Fn yet; reason: tooling CI flake from RET-002; decided: 2026-08-06 issue triage / S029]
[Spec: docs/security/static-analysis.md]
[Spec: docs/sessions/S027-multilingual-embeddings/reports/qa-remediation.md]

## Scope

**In**

- Retries with backoff on GitHub API + download in `install-tools.sh`
- Optional `GH_TOKEN` documentation for higher API quota (no secrets committed)
- Repro test under `tests/bugs/`
- Bug report + close #227

**Out**

- Soft-fail / silent skip of security scans
- Product feature work / Modal or DO deploy
- Full actions/cache mirror (defer unless retries insufficient)

## Remediation path

Land on `main` ASAP via PR; merge only with explicit user approval (Step 0.3 option b).
