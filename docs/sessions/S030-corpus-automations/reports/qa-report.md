# QA Report — EV-027 / S030 (F75–F77)

> Generated: 2026-09-05  
> Scope: Full-repo QA after reopened `08-verify-build` pass for Phase 30  
> Branch: `evolve/EV-027-corpus-automations`  
> Mode: evolve / full-repo · `09-qa` report-only pass

[Corpus: feature-list.md §F75] [Corpus: feature-list.md §F76] [Corpus: feature-list.md §F77]  
[Corpus: tests] [Corpus: deploy-integration]  
[Spec: docs/adr/ADR-052-corpus-automation-orchestration.md]  
[Spec: docs/adr/ADR-053-modal-lora-finetune.md]  
[Spec: docs/sessions/S030-corpus-automations/reports/verification-report.md]

```text
QA Results:
  Lint:           PASS — 0 issues
  Format:         PASS — 0 files needing changes
  Typecheck:      PASS — 0 Python/TS errors
  Tests (Python): PASS — 2413 passed, 40 skipped
  Tests (FE):     PASS — chat-rag 195; data-management 846
  Security:       PASS — audit clean; secrets clean; security suite passed
  Cross-file:     PASS — no dangerous app/package patterns found; no modal imports in apps/packages
  Dependencies:   ADVISORY — 2 outdated local Python packages (`mlx`, `wheel`)
  Template:       PASS — monorepo layout + Modal isolation OK
  Data / Modal:   PASS with advisories — D1-D9 verified; staging live URLs unset
```

## Overall

**PASS_WITH_ADVISORIES**. No blocking QA failures reproduced in this rerun. The earlier
historical `QA-S030-001` alembic-head failure is no longer present because the full Python
suite now passes cleanly. Remaining items are advisory only and can flow into `10-e2e`
and `11-verify-impl`.

## Executive summary

| Area | Blocking | Advisory | Status |
|------|----------|----------|--------|
| Lint / format / types | 0 | 0 | PASS |
| H0c + H0i Python checks | 0 | 40 skips | PASS |
| Frontend Vitest | 0 | provider-guard console traces in passing tests | PASS |
| Security tree | 0 | 0 | PASS |
| Cross-file / template | 0 | 1 skipped cycle analysis | PASS |
| Dependencies | 0 | 2 outdated packages | ADVISORY |
| Data staging | 0 | 0 | PASS |
| H4-H5 live staging connectivity | 0 | frontend/backend staging URLs unset | ADVISORY |

## Commands and evidence

Reused fresh `08-verify-build` evidence from the same reopened session:

```bash
make ci-push
```

Additional QA-only checks:

```bash
python3 -m pip list --outdated --format=json
rg 'pickle\.loads|\beval\(|\bexec\(' apps packages
rg '^import modal|^from modal' --type py
```

## Per-check detail

### Build-parity baseline

`make ci-push` passed on 2026-09-05 with:

- guard scripts: PASS
- lint: PASS
- format-check: PASS
- typecheck: PASS
- `make audit`: PASS
- `make security-scan`: PASS
- Python test suite: `2413 passed, 40 skipped`
- chat-rag Vitest: `38 files / 195 tests passed`
- data-management Vitest: `99 files / 846 tests passed`
- frontend production builds: PASS

### Security

- `make audit`: no Python vulnerabilities
- `make security-scan`: passed; KICS blocking severities clear, Grype high clear, Supabase advisors 0
- `scripts/check_secrets.sh`: clean
- `gitleaks detect --no-git`: covered in `make ci-push`

### Cross-file / template

- Dangerous-pattern scan over `apps/` and `packages/`: no risky app/package code matches
- One false positive exists in a frontend test regex using `.exec(...)`; not a runtime code issue
- `import modal` is confined to `infra/modal/` and deploy scripts, not `apps/` or `packages/`
- Layout remains aligned with the repo’s monorepo + Modal split

### Dependency health

Outdated local Python packages:

- `mlx` `0.32.1 -> 0.32.2`
- `wheel` `0.47.0 -> 0.48.0`

These are advisory only; no dependency-health blocker surfaced in this pass.

### Data / Modal / connectivity

From `docs/sessions/S000-internal-docs-archive/data-staging-state.md`:

- D1-D5, D8-D9: verified
- D6 FastEmbed: verified
- D7 Qwen2.5-1.5B-Instruct: verified

Live staging connectivity remains advisory in this stage because these env-gated URLs were unset:

- `VECINITA_STAGING_CHAT_URL`
- `VECINITA_STAGING_DATA_MANAGEMENT_URL`
- `VECINITA_STAGING_CHAT_FRONTEND_URL`
- `VECINITA_STAGING_DATA_MANAGEMENT_FRONTEND_URL`

## Findings for 11-verify-impl

| ID | Severity | Finding | Suggested action |
|----|----------|---------|------------------|
| QA-S030-001 | advisory | Stage-09 live staging connectivity was not exercised because the required staging URLs were unset in the local environment. | Run env-gated live connectivity checks at `10-e2e` or `13-deploy-smoke` when URLs are available. |
| QA-S030-002 | advisory | Two local Python packages are outdated: `mlx`, `wheel`. | Review whether these are intentional pins before any dependency bump. |
| QA-S030-003 | advisory | Circular-dependency analysis was not run as a dedicated graph check in this QA pass. | If `11-verify-impl` needs stronger evidence, run a focused import-graph pass. |
| QA-S030-004 | advisory | Passing Vitest suites emit expected provider-guard error traces in hook misuse tests, which can look noisy in logs. | No code action required unless you want cleaner test output later. |
| QA-S030-005 | advisory | Live prod automation enable and LoRA promote remain explicitly gated. | Keep deferred until the later deploy stage with explicit approval. |

## Phase / execution-plan alignment

- Phase 30 M127-M130 remain complete
- Reopened `08-verify-build` rerun passed on 2026-09-05
- `09-qa` has no blocking failure in this pass
- PR [#238](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/238) remains open

## Next

Proceed to `10-e2e`, then use `11-verify-impl` to review the advisories above.
