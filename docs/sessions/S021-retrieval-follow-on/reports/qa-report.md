# QA Report — EV-018 / S021 (F46 + F45 re-gate)

> Generated: 2026-08-02  
> Scope: delta — F46 empty retrieve fix + F45 CE re-gate (AC-BB9)  
> Branch: `evolve/EV-018-retrieval-follow-on` @ `1b46507`  
> Mode: evolve / delta_only · parallel with 10-e2e  
> Prior: 08-verify-build **PASS** · Gate C→D **passed** · S021-D23/D24

```text
QA Results:
  Lint:           PASS — 0 issues
  Format:         PASS — 457 files
  Typecheck:      PASS — 0 errors, 1 warning (test_modal_url_validate)
  Tests (Python): PASS (delta) — see 10-e2e; H0c PASS; full DB matrix SKIPPED locally
  Tests (FE):     SKIPPED — no FE delta in EV-018 (CI frontend matrix on PR)
  Tests (UI):     SKIPPED — no UI delta
  Coverage gate:  SKIPPED locally — CI on PR
  Security:       PASS — make audit (4 ignored nltk); secrets OK
  Cross-file:     PASS — ruff clean
  Dependencies:   advisory — nltk held <3.10 (documented)
  Template:       PASS — Modal no DATABASE_URL; OpenAPI OK; operator specs untracked
  Data / Modal:   Path B restore done; CE ship_gate_pass=true (T100.1)
```

**Overall: pass_with_advisories** — blocking local delta checks green; full pytest/FE deferred to CI; CE flag enablement deferred to 12/13 Path A.

## Executive summary

| Check | Blocking? | Status |
|-------|-----------|--------|
| Ruff lint | yes | **PASS** |
| Ruff format | yes | **PASS** |
| basedpyright | yes | **PASS** (0 errors) |
| H0c `test_cors_policy.py` | yes | **PASS** |
| Corpus reset guard | yes | **PASS** |
| Secrets / Modal DB / OpenAPI / operator specs | yes | **PASS** |
| `make audit` | yes | **PASS** (4 ignored nltk CVEs) |
| Full pytest + integration (Postgres) | yes (CI) | **SKIPPED locally** — Docker unavailable (S021-D23) |
| Frontend lint / Vitest / coverage | yes (CI) | **SKIPPED locally** — no FE delta |
| AC-BB9 / TC-184 | no (met) | **PASS** — [ce-ship-gate.md](./ce-ship-gate.md) |
| Staging H4–H5 | no | **ADVISORY** — 12/13 |

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
bash scripts/check_corpus_reset_guard.sh
uv run pytest tests/unit/test_cors_policy.py -q
```

## Findings

| ID | Severity | Finding |
|----|----------|---------|
| QA-S021-A01 | advisory | Local Docker/Postgres unavailable — full pytest/integration deferred to CI on PR |
| QA-S021-A02 | advisory | FE / Playwright / coverage not re-run locally (no FE delta) |
| QA-S021-A03 | advisory | nltk held `<3.10` with documented ignores |
| QA-S021-A04 | ship-path | Prod `VECINITA_RAG_RERANK_CE` still **false** until 12/13 Path A (AC-FO4 / S021-D24) |

## Connectivity (stage 09)

| Item | Status |
|------|--------|
| H0c CORS | **PASS** |
| H0i integration | **SKIPPED** (no Postgres) |
| H4–H5 staging frontends | **ADVISORY** — deferred to 12/13 |

## Cross-links

| Artifact | Path |
|----------|------|
| 08 verify | [verification-report.md](./verification-report.md) |
| 10 e2e | [e2e-report.md](./e2e-report.md) |
| CE ship gate | [ce-ship-gate.md](./ce-ship-gate.md) |
| Phase 23 gate | [phase23-gate.md](./phase23-gate.md) |
