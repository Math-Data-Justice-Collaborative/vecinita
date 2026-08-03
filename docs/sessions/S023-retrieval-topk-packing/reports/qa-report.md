# QA Report — EV-020 / S023 (F50–F51 retrieval top_k + P3 packing)

> Generated: 2026-08-03  
> Scope: delta — F50 `top_k=8` · F51 default packer `p3`  
> Branch: `evolve/EV-020-retrieval-topk-packing` @ `4ea0c62`  
> Mode: evolve / delta_only · parallel with 10-e2e  
> Prior: 08-verify-build **PASS** · Gate C→D **passed** (S023-D14) · Phase 25 M105–M107 complete

```text
QA Results:
  Lint:           PASS — 0 issues
  Format:         PASS — 466 files
  Typecheck:      PASS — 0 errors, 1 warning (test_modal_url_validate)
  Tests (Python): PASS (delta) — 76 passed, 12 skipped (F50–F51 + H0c + UJ-055/063)
  Tests (FE):     PASS (lint/typecheck via make check-fast); Vitest/coverage deferred to CI
  Tests (UI):     SKIPPED — AC-RQ10 / no FE knobs (no Playwright for UJ-063)
  Coverage gate:  SKIPPED locally — CI on PR
  Security:       PASS — make audit (4 ignored nltk); secrets OK
  Cross-file:     PASS — ruff clean; no pickle.loads / bare eval/exec in apps+packages
  Dependencies:   advisory — workspace packages skipped by pip-audit; nltk held
  Template:       PASS — Modal no DATABASE_URL; OpenAPI OK; operator specs untracked
  Data / Modal:   D1–D9 verified; D6/D7 verified (2026-06-30)
```

**Overall: pass_with_advisories** — blocking local delta checks green; full pytest/integration + FE coverage deferred to CI (Docker/Postgres unavailable).

## Executive summary

| Check | Blocking? | Status |
|-------|-----------|--------|
| Ruff lint | yes | **PASS** |
| Ruff format | yes | **PASS** |
| basedpyright | yes | **PASS** (0 errors) |
| `make check-fast` (incl. FE lint/tsc) | yes | **PASS** (3 react-refresh warnings DM FE) |
| H0c `test_cors_policy.py` | yes | **PASS** (21 collected w/ skips in delta run) |
| Corpus reset guard | yes | **PASS** |
| Secrets / Modal DB / OpenAPI / operator specs | yes | **PASS** |
| `make audit` | yes | **PASS** (4 ignored nltk CVEs) |
| F50–F51 delta pytest | yes | **PASS** — 76 passed, 12 skipped |
| Full pytest + integration (Postgres) | yes (CI) | **SKIPPED locally** — Docker unavailable |
| Frontend Vitest / coverage gate | yes (CI) | **SKIPPED locally** — no FE product delta (AC-RQ10) |
| Playwright T0-ui | yes (CI when enabled) | **SKIPPED** — AC-RQ10 / no ChatRAG FE knobs |
| Staging H4–H5 | no | **ADVISORY** — deferred to 12/13 |

## Commands run

```bash
make check-fast
uv run ruff check apps packages tests infra scripts
uv run ruff format --check apps packages tests infra scripts
uv run basedpyright apps packages tests infra scripts
make audit
bash scripts/check_secrets.sh
bash scripts/check_modal_no_database_url.sh
bash scripts/check_openapi_specs.sh
bash scripts/check_no_operator_specs_tracked.sh
bash scripts/check_corpus_reset_guard.sh
uv run pytest \
  tests/unit/rag/test_constants.py \
  tests/unit/rag/test_context_packing.py \
  tests/unit/chat_rag/test_config.py \
  tests/unit/eval/test_runner_sandbox_config.py \
  tests/e2e/test_uj063_topk_p3_ask.py \
  tests/e2e/test_uj055_h7_p1_ask.py \
  tests/e2e/test_uj004_local_bootstrap.py \
  tests/unit/test_cors_policy.py -v
```

## Findings for 11-verify-impl

| ID | Severity | Finding | Suggested action |
|----|----------|---------|------------------|
| QA-S023-A01 | advisory | Local Docker/Postgres unavailable — full pytest/integration deferred to CI on PR | Confirm green `ci.yml` after push |
| QA-S023-A02 | advisory | FE Vitest / coverage / Playwright not re-run locally (no FE product delta; AC-RQ10) | CI frontend + ui-e2e on PR |
| QA-S023-A03 | advisory | nltk held `<3.10` with documented pip-audit ignores | Keep until intentional bump + ADR |
| QA-S023-A04 | ship-path | DO env already has `VECINITA_TOP_K=8` + `VECINITA_RAG_PACKER=p3` in `infra/do/chat-rag-backend.yaml`; live DO app must receive values at deploy | Confirm at 12/13 sync/redeploy |
| QA-S023-A05 | info | basedpyright warning on `deploy.modal_url_validate` import (pre-existing) | No action for EV-020 |

## Connectivity (stage 09)

| Item | Status |
|------|--------|
| H0c CORS | **PASS** |
| H0i integration | **SKIPPED** (no Postgres / Docker) |
| H4–H5 staging frontends | **ADVISORY** — deferred to 12/13 |

## Phase / execution-plan alignment

| Item | Status |
|------|--------|
| Phase 25 M105–M107 | completed @ `4ea0c62` |
| 08-verify-build | PASS (verification-report.md) |
| AC-RQ10 scope | held (no Playwright / no CE / no adaptive top_k / no Path B) |
| DO defaults | `VECINITA_TOP_K=8`, `VECINITA_RAG_PACKER=p3` in infra |

## Advisory remediation (2026-08-03 — S023-D16)

User chose option 2: address advisories before 11-verify-impl.

| ID | Action | Result |
|----|--------|--------|
| QA-S023-A01 / A02 | Push branch · watch `ci.yml` | In progress (this commit + push) |
| QA-S023-A04 | Confirm DO env in infra | **CONFIRMED** — `infra/do/chat-rag-backend.yaml` has `VECINITA_TOP_K=8`, `VECINITA_RAG_PACKER=p3` (plain RUN_TIME values, not secrets) |
| Live DO app read | `doctl` / `prod.env` | **BLOCKED locally** — no `prod.env` / `DIGITALOCEAN_TOKEN` in this environment; live apply remains 12/13 |
| QA-S023-A03 | nltk holds | No change (intentional) |

## Cross-links

| Artifact | Path |
|----------|------|
| 08 verify | [verification-report.md](./verification-report.md) |
| 10 e2e | [e2e-report.md](./e2e-report.md) |
| HANDOFF | [../HANDOFF.md](../HANDOFF.md) |
