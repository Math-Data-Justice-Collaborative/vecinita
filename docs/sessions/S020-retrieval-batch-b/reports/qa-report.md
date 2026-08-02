# QA Report — EV-017 / S020 (F43–F45)

> Generated: 2026-08-02  
> Scope: delta — F43 H1 cache + F44 soft language + F45 CE (Path A)  
> Branch: `evolve/EV-017-retrieval-batch-b` @ `d9c9f4a`  
> Mode: evolve / delta_only · parallel with 10-e2e  
> Prior: 08-verify-build **PASS (scoped)** · Gate C→D **passed** (S020-D19) · PR [#173](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/173)

```text
QA Results:
  Lint:           PASS — 0 issues
  Format:         PASS — 455 files
  Typecheck:      PASS — 0 errors, 1 warning (test_modal_url_validate)
  Tests (Python): PASS (Phase 22 scoped) — 100 passed / 11 skipped (+ H0c); full DB matrix SKIPPED locally
  Tests (FE):     SKIPPED — no FE delta in EV-017 (CI frontend matrix on PR)
  Tests (UI):     SKIPPED — no UI delta (Playwright unchanged)
  Coverage gate:  SKIPPED locally — no FE delta; CI coverage job on PR
  Security:       PASS — make audit (4 ignored nltk); secrets OK; gitleaks not installed
  Cross-file:     PASS — ruff F401/F841 clean via full lint
  Dependencies:   advisory — nltk held <3.10 (documented)
  Template:       PASS — Modal only under infra/; OpenAPI OK; no DATABASE_URL in Modal
  Data / Modal:   CE spike Path A deferred (AC-BB9); live staging URLs unset
```

**Overall: pass_with_advisories** — blocking local delta checks green; DB/FE full matrix deferred to GitHub CI on PR #173; AC-BB9 / TC-184 / UJ-060 staging CE ship evidence remain ship-path advisories.

## Executive summary

| Check | Blocking? | Status |
|-------|-----------|--------|
| Ruff lint | yes | **PASS** |
| Ruff format | yes | **PASS** |
| basedpyright | yes | **PASS** (0 errors) |
| H0c `test_cors_policy.py` | yes | **PASS** |
| Phase 22 unit + UJ-057–059 | yes (delta) | **PASS** (100 passed / 11 skipped in 08; e2e 11/11 in 10) |
| Full pytest + integration (Postgres) | yes (CI) | **SKIPPED locally** — Docker daemon down |
| Frontend lint / Vitest / Playwright / coverage | yes (CI) | **SKIPPED locally** — no FE/UI files in delta |
| `make audit` | yes | **PASS** (4 ignored nltk CVEs) |
| Secrets / Modal DB / OpenAPI / operator specs | yes | **PASS** |
| AC-BB9 / TC-184 / UJ-060 CE ship floors | no (ship-path) | **ADVISORY** — [ce-ship-gate.md](./ce-ship-gate.md) pending spike JSON |
| Staging H4–H5 / live Modal | no | **ADVISORY** — env unset; 12/13 |

## Commands run

```bash
uv run ruff check apps packages tests infra scripts
uv run ruff format --check apps packages tests infra scripts
uv run basedpyright apps packages tests infra scripts
make audit
bash scripts/check_secrets.sh
bash scripts/check_modal_no_database_url.sh
bash scripts/check_openapi_specs.sh
bash scripts/check_no_operator_specs_tracked.sh
uv run pytest tests/unit/test_cors_policy.py -q
# Phase 22 scoped suite — see verification-report.md (08) + e2e-report.md (10)
```

## Findings

| ID | Severity | Finding |
|----|----------|---------|
| QA-S020-A01 | advisory | Local Docker/Postgres unavailable — full pytest/integration deferred to CI on #173 |
| QA-S020-A02 | advisory | FE / Playwright / coverage not re-run locally (no FE delta); CI matrix is source of truth |
| QA-S020-A03 | ship-path | AC-BB9 / TC-184 / UJ-060 — CE ship-gate template pending live spike metrics |
| QA-S020-A04 | advisory | nltk held `<3.10` with documented ignores (`audit/pip-audit-ignore.txt`) |
| QA-S020-A05 | advisory | gitleaks not installed locally — tree secrets script PASS |

## Connectivity (stage 09)

| Item | Status |
|------|--------|
| H0c CORS | **PASS** |
| H0i integration | **SKIPPED** (no Postgres) |
| H4–H5 staging frontends | **ADVISORY** — `VECINITA_STAGING_*_FRONTEND_URL` unset |
| Artifacts | `test_cors_policy.py`, `test_staging_connectivity.py`, `scripts/deploy/verify_connectivity.sh` present |

## Cross-links

| Artifact | Path |
|----------|------|
| 08 verification | [verification-report.md](./verification-report.md) |
| 10 e2e | [e2e-report.md](./e2e-report.md) |
| Phase 22 gate | [phase22-gate-checklist.md](./phase22-gate-checklist.md) |
| CE ship gate | [ce-ship-gate.md](./ce-ship-gate.md) |
| PR | https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/173 |

## Recommended for 11-verify-impl

1. Confirm CI green on #173 (python + frontend + coverage + ui-e2e).  
2. Per-AC review for AC-BB1–BB8, BB10 at T2; AC-BB9 deferred to 12/13.  
3. Do not enable prod CE (`VECINITA_RAG_RERANK_CE`) without UJ-060 ship-gate pass.
