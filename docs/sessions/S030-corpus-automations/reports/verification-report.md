# Verification Report

> Generated: 2026-08-12  
> Scope: Phase 30 / M129 — F77 LoRA FT (`EV-027` / S030) milestone 08-verify-build  
> Branch: `evolve/EV-027-corpus-automations` @ `eb951fd` (+ format auto-fix)  
> Corpus: [Corpus: feature-list.md §F77] [Corpus: feature-list.md §F75] [Corpus: feature-list.md §F76]  
> [Spec: docs/adr/ADR-053-modal-lora-finetune.md] [Spec: docs/test-plan.md §UJ-082]  
> Decisions: S030-D52 (nanoid/js-yaml), S030-D53 (react-router)

## Summary

| Check | Status | Findings | Auto-Fixed | Tool |
|-------|--------|----------|------------|------|
| Lint (Python) | PASS | 0 errors | 0 | ruff |
| Lint (FE) | PASS | 0 errors (3 pre-existing react-refresh warnings) | — | eslint |
| Format | PASS | Prettier issue in UJ-081 test | 1 (prettier --write) | ruff + prettier |
| Typecheck | PASS | 0 errors (1 pre-existing missing-module warning) | — | basedpyright + tsc |
| Tests (unit) | PASS | 1562 passed, 16 skipped | — | pytest |
| Tests (CORS H0c) | PASS | `tests/unit/test_cors_policy.py` | — | pytest |
| Tests (FE Vitest) | PASS | DM 813; chat-rag 190 | — | vitest |
| Tests (`make test-fast`) | SKIPPED | host bash 3.2 lacks `mapfile` — ran full unit + FE instead | — | scripts/ci/test_fast.sh |
| Security (suite) | PASS | Grype HIGH 0; npm audit 0 | 2 override bumps | `make security-scan` |
| Connectivity artifacts | PASS | `tests/smoke/test_staging_connectivity.py`; `scripts/deploy/verify_connectivity.sh` | — | ls |
| Performance | SKIPPED | No M129 perf thresholds | — | — |
| Data | SKIPPED | No weight staging for M129 | — | — |
| Personas | ADVISORY | 0 🔴 / 1 🟡 (deploy still at 13) | — | personas.md |
| Modal run smoke | SKIPPED | No GPU budget AskQuestion | — | ADR-004 |

**Overall:** **PASS**. M129 (F77) verified at 08; Gate C→D still waits on M130 Phase 30 close. Live H4–H5 remains **13**.

## Security remediation (blocking → cleared)

| Advisory | Package | From | To | Decision |
|----------|---------|------|----|----------|
| GHSA-2v37-7h3g-55p8 | `nanoid` | 3.3.16 | **3.3.17** | S030-D52 |
| GHSA-5p4m-2wfm-xmqj | `js-yaml` | 4.3.0 | **4.3.1** | S030-D52 |
| GHSA-qwww-vcr4-c8h2 | `react-router` / `react-router-dom` | 7.18.1 | **7.18.2** | S030-D53 |

Commits: `59ac29d` (nanoid/js-yaml), `eb951fd` (react-router).

## Auto-fixes

1. `apps/data-management-frontend/src/test/test_uj081_freshness_ui.test.tsx` — Prettier format (trailing blank lines).

## Test detail

```bash
make lint
make format-check   # after prettier auto-fix
make typecheck
uv run pytest tests/unit tests/unit/test_cors_policy.py -q
npm test -w vecinita-data-management-frontend -- --run
npm test -w vecinita-chat-rag-frontend -- --run
make security-scan
npm audit   # 0 vulnerabilities after react-router 7.18.2
```

## Personas (delta — F77)

| Persona | Finding |
|---------|---------|
| Staff Backend | 🟢 FT approve/promote API + kill-switch; no auto-promote |
| Staff Frontend | 🟢 DM `/finetune` UJ-082 journey covered |
| Senior DevOps | 🟡 Live Modal FT deploy / H4–H5 still at **13** |
| Data & Privacy | 🟢 Prod promote remains AskQuestion-gated |
| Community Partner | 🟢 Human promote/eval evidence before prod adapter pin |
| CTO | 🟢 Dependency High CVEs cleared before M130 |

## Connectivity

- H0c: PASS (`test_cors_policy.py`)
- Smoke artifact: present
- Verify script: `scripts/deploy/verify_connectivity.sh`

## Next

1. Start **T130.1** / M130 Phase 30 gate (leave PR #238 open)  
2. After M130: Phase C checkpoint → Gate C→D → 09–13 as routed  
