# Verification Report

> Generated: 2026-08-05  
> Scope: Phase 28 / M122 gate closeout — F70–F71 (`EV-025` / S027) after PR #213 merge  
> Branch: `evolve/EV-025-multilingual-embeddings` (synced with `main` @ `de1355c`)  
> Corpus: [Corpus: feature-list.md §F70] [Corpus: feature-list.md §F71]  
> [Spec: docs/adr/ADR-048-multilingual-384-embeddings.md] [Spec: docs/test-plan.md §TC-232–241]  
> [Spec: docs/decisions/evolve-decisions.md §S027-D35 / S027-D40 / S027-D41]

## Summary

| Check | Status | Findings | Auto-Fixed | Tool |
|-------|--------|----------|------------|------|
| Lint | PASS | 0 errors (3 FE refresh warnings pre-existing) | 0 | `make check-fast` / ruff + eslint |
| Format | PASS | 526 files | 0 | `ruff format --check` |
| Typecheck | PASS | 0 errors (1 pre-existing missing-module warning) | — | basedpyright + tsc |
| Tests (F70/F71 scoped) | PASS | unit + stub e2e; compose skipped | — | pytest |
| Tests (CORS H0c) | PASS | `test_cors_policy.py` | — | pytest |
| Tests (compose e2e) | WAIVED | S027-D35 Docker userns | — | — |
| Security (secrets) | PASS | 0 high-confidence patterns | — | `check_secrets.sh` |
| Security (pip-audit) | ADVISORY | nltk 3.9.4 ×4 CVEs (CI python job green on main) | — | `pip-audit` |
| Connectivity H0c | PASS | CORS policy | — | pytest |
| Connectivity artifacts | PASS | `tests/smoke/test_staging_connectivity.py`; `scripts/deploy/verify_connectivity.sh` | — | ls |
| Performance | SKIPPED | No Phase 28 perf thresholds | — | — |
| Data | SKIPPED | No weight staging verify | — | — |
| Personas | ADVISORY | 0 🔴 / 1 🟡 | — | personas.md |
| Modal run smoke | SKIPPED | No GPU budget AskQuestion | — | ADR-004 |
| Main CI + preflight | PASS | @ `de1355c` (security install flaky once; rerun OK) | — | GitHub Actions |

**Overall:** **PASS** (conditional on S027-D35 compose waive). Phase 28 **07-build** verified; live cutover remains **13**.

## Merge evidence

| Item | Value |
|------|-------|
| PR-70 / #213 | MERGED @ `de1355c` |
| Main CI | [31041754477](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/31041754477) success |
| Deploy preflight | [31042366703](https://github.com/Math-Data-Justice-Collaborative/vecinita/actions/runs/31042366703) success |
| Decision | S027-D41 |

### Flaky note (for 17-retrospective)

First `security` job on main failed at `install-tools.sh` — “Failed to fetch available versions from GitHub.” Rerun of failed jobs passed. Flag with user-reported **prod bugs** for post-cycle **17-retrospective**.

## Test detail

```bash
uv run pytest \
  tests/unit/test_cors_policy.py \
  tests/unit/test_f70_f71_m122_green_gate.py \
  tests/unit/test_embedding_prefixes_runtime.py \
  tests/unit/test_embedding_modal_pins.py \
  tests/unit/shared_schemas/test_f71_*.py \
  tests/unit/test_f71_*.py \
  tests/e2e/test_uj075_multilingual_ask.py -q
# → passed (compose-dependent cases skipped)
```

## Personas (delta)

| Persona | Finding |
|---------|---------|
| Staff Backend | 🟢 TC-232–241 mapped; E0 rollback + cutover runbook present |
| Senior DevOps | 🟡 Live prod cutover + Modal image still at **13** (H4–H5) |
| Data & Privacy | 🟢 No UI/PII surface; stamps via env |
| CTO | 🟢 07 gate partial recorded; #159 close after 13 |

## Connectivity

- H0c: PASS  
- Smoke artifact: present  
- Verify script: `scripts/deploy/verify_connectivity.sh`

## Next

1. Continue Phase D: **09-qa** (then 10–13 per routing)  
2. After cycle close / deploy verify: **17-retrospective** (prod bugs + flaky security install) — queued, not started
