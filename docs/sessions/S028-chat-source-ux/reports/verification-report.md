# Verification Report

> Generated: 2026-08-06  
> Scope: Phase 29 / M123–M126 — F72–F74 (`EV-026` / S028) Gate C→D / 08-verify-build  
> Branch: `evolve/EV-026-chat-source-ux` @ `70c4565` (+ 08 auto-fixes)  
> Corpus: [Corpus: feature-list.md §F72] [Corpus: feature-list.md §F73] [Corpus: feature-list.md §F74]  
> [Spec: docs/adr/ADR-051-display-title-vs-lock-flag.md] [Spec: docs/test-plan.md §TC-242–251]  
> [Spec: docs/acceptance-criteria.md §AC-SU1–SU10] [Decision: S028-D26 Gate C→D]

## Summary

| Check | Status | Findings | Auto-Fixed | Tool |
|-------|--------|----------|------------|------|
| Lint | PASS | RUF002 en-dash in migration docstring | 1 (hyphen) | ruff |
| Format | PASS | 535 files | 0 | `ruff format --check` |
| Typecheck | PASS | 0 errors (1 pre-existing missing-module warning) | — | basedpyright |
| FE lint | PASS | 0 errors (3 pre-existing react-refresh warnings) | — | eslint |
| Tests (unit) | PASS | full `tests/unit` | — | pytest |
| Tests (integration) | PASS | full `tests/integration` (alembic head assert updated for 0014) | — | pytest |
| Tests (EV-026 e2e + Vitest) | PASS | UJ-078/079 + SourceList + isSafeHttpUrl + DocumentAdmin | — | pytest + vitest |
| Tests (CORS H0c) | PASS | `test_cors_policy.py` + PATCH document H0c | — | pytest |
| Security (tracked secrets) | PASS | `check_secrets.sh` | — | scripts |
| Security (suite) | PASS | `.tmp` ignore; brace-expansion → 1.1.18/2.1.4/5.0.9 (GHSA-rgw5-rvv9-x895) | 2 | `make security-scan` |
| Connectivity H0c | PASS | CORS policy + F74 PATCH | — | pytest |
| Connectivity artifacts | PASS | `tests/smoke/test_staging_connectivity.py`; `scripts/deploy/verify_connectivity.sh` | — | ls |
| Performance | SKIPPED | No Phase 29 perf thresholds | — | — |
| Data | SKIPPED | No weight staging | — | — |
| Personas | ADVISORY | 0 🔴 / 2 🟡 | — | personas.md |
| Modal run smoke | SKIPPED | No GPU budget AskQuestion | — | ADR-004 |

**Overall:** **PASS**. Phase 29 **07-build** verified at 08; live H4–H5 remains **13** (AskQuestion S028-D2).

## Auto-fixes / remediation applied

1. `apps/database/alembic/versions/20260806_0014_ev026_display_title.py` — RUF002 en-dash → hyphen in docstring.
2. `tests/integration/test_ev002_schema.py` — head asserts follow `20260806_0014`; EV-002 `20260804_0012` remains in **history** (matches docstring / chain contract).
3. `scripts/security/run-all.sh` — ignore `.tmp` for 2ms (gitignored operator secret exports; see `docs/security/gitleaks-resolution.md`).
4. `package.json` overrides — `brace-expansion` 1.1.18 / 2.1.4 / 5.0.9 for GHSA-rgw5-rvv9-x895 (CVE-2026-69152); lockfile refreshed; grype-ignore comment updated.

## Test detail

```bash
uv run ruff check apps packages tests infra scripts
uv run ruff format --check apps packages tests infra scripts
uv run basedpyright apps packages tests infra scripts
uv run pytest tests/unit tests/integration -q
uv run pytest \
  tests/e2e/test_uj078_relevance_sources.py \
  tests/e2e/test_uj079_display_title.py \
  tests/unit/test_cors_policy.py \
  tests/unit/test_cors_ev002.py::test_cors_patch_document_metadata -q
# Vitest: frontend-ui isSafeHttpUrl; chat SourceList; admin display_title
bash scripts/check_secrets.sh
make security-scan
```

## Personas (delta)

| Persona | Finding |
|---------|---------|
| Staff Backend | 🟢 COALESCE + PATCH + audit; ADR-051 Accepted; OpenAPI synced |
| Staff Frontend | 🟢 URL helper shared; DocumentAdmin rename/clear; CorpusList prefers display |
| Senior DevOps | 🟡 Live H4–H5 + DO/Modal redeploy still at **13** (AskQuestion) |
| Data & Privacy | 🟢 No new PII surface; operator override only; audit before/after |
| Community Partner | 🟢 Invalid citation URLs no longer look clickable; few-strong sources |
| CTO | 🟡 #222–#224 close after 11 (13 if deploy); RD-321 ingest title→display deferred |

## Connectivity

- H0c: PASS (incl. `OPTIONS PATCH /internal/v1/documents/{id}`)
- Smoke artifact: present
- Verify script: `scripts/deploy/verify_connectivity.sh`

## Next

1. Continue Phase D: **09-qa** (then 10–11; 12–13 AskQuestion-gated)  
2. Open PR-75 from `evolve/EV-026-chat-source-ux` when ready (after push + CI watch)
