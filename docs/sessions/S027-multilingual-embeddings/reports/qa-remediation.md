# QA Advisory Remediation — EV-025 / S027

> Generated: 2026-08-05  
> Trigger: user option **3** on continue-to-11 AskQuestion (S027-D43)  
> Source: `reports/qa-report.md` §Findings  
> Mode: advisory remediation pass (09-qa skill §Advisory remediation) — **not** a full 09 re-run  

[Corpus: feature-list.md §F70] [Corpus: feature-list.md §F71]  
[Spec: docs/decisions/evolve-decisions.md §S027-D35]  
[Spec: docs/decisions/evolve-decisions.md §S027-D43]  
[Corpus: WAIVED — compose DB suites locally; reason: Docker userns / daemon unavailable; decided: S027-D35]

## Environment re-check (2026-08-05)

| Check | Result |
|-------|--------|
| `docker info` | **FAIL** (exit 1) — daemon unavailable |
| `localhost:5432` | **down** |
| DM Vitest re-run | **PASS** — 91 files / 736 tests (41s) |

## Disposition table (recommended)

| ID | Finding | Recommended disposition | Evidence / next gate |
|----|---------|-------------------------|----------------------|
| QA-S027-001 | Local compose/DB suites unavailable | **Accept** S027-D35 — do not block Phase D; rely on main CI @ `de1355c` + staging/ops when Docker recovers | Docker still down this pass; UJ-076 compose remains WAIVED |
| QA-S027-002 | H4–H5 live cutover not run | **Carry to 13-deploy-smoke** — required live EN/ES ask + promote path | Staging FE URLs unset; connectivity-gates H4–H5 |
| QA-S027-003 | DM Vitest worker flake (once) | **Accept as flake** — monitor; no code change | Re-run green 736/736; prior QA 2nd run green; CI green |
| QA-S027-004 | Main CI security `install-tools` GitHub fetch flake | **Queue 17-retrospective** — document retry pattern; no CI change this cycle | `verification-report.md` §Flaky note |
| QA-S027-005 | User-reported prod bugs this cycle | **Queue 17-retrospective** after Phase D / deploy (do **not** start 17 now) | S027-D41 already queued |

## Blocking vs advisory

- **Blocking remediations needed now:** none  
- **Code/config changes this pass:** none  
- **Overall after remediation:** still `pass_with_advisories` with explicit dispositions (ready for 11 once user confirms package)

## 17-retrospective agenda seeds (004 + 005)

1. Flaky `scripts/security/install-tools.sh` GitHub version fetch on main — retries / mirror / cache.
2. User-reported production bugs observed during EV-025 — intake under 17, not 14-hotfix mid-cycle unless severity escalates.

## Next

AskQuestion disposition: **Accepted** (S027-D44 option 1) — proceed to **11-verify-impl**.
