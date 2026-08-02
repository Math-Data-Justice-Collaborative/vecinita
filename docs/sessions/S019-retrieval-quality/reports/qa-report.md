# QA Report — EV-016 / S019 (F42)

> Generated: 2026-08-02T00:59:54Z  
> Scope: delta — F42 H7 multi-query + P1 packing (Hy1 on E0)  
> Branch: `evolve/EV-016-retrieval-quality` @ `257486f`  
> Mode: evolve / delta_only · parallel with 10-e2e  
> Prior: 08-verify-build **PASS (delta)** · Gate C→D approved

```text
QA Results (post-remediation S019-D47):
  Lint:           PASS — 0 issues (full apps/packages/tests/infra/scripts)
  Format:         PASS
  Typecheck:      PASS — 0 errors, 1 warning (test_modal_url_validate missing-module-source)
  Tests (Python): PASS (F42 + spikes scoped) — spike/*.py + UJ-055 + packing/H7 + H0c green
  Tests (FE):     PASS — chat-rag 162/162; DM 697/697 (prior 09 run; unchanged)
  Tests (UI):     PASS — Playwright 42 passed / 2 staging skipped (prior 09 run)
  Coverage gate:  PASS — prior 09 run
  Security:       PASS — nltk CVEs documented-ignored (see remediation); secrets OK
  Cross-file:     PASS
  Dependencies:   advisory — nltk held at 3.9.4,<3.10 (inisec + in-tree venv)
  Template:       PASS
  Data / Modal:   D1–D9 / D6 / D7 verified; live Modal/staging URLs unset
```

**Overall: pass_with_advisories** — blockers B01–B03 cleared (S019-D47 fix-in-place).
Initial 09 run was **FAIL**; remediation re-check green for lint/types/audit.
AC-RQ6 / ISS-008 deploy remain ship-path advisories.

## Executive summary

| Check | Blocking? | Status |
|-------|-----------|--------|
| Ruff lint (`apps packages tests infra scripts`) | yes | **FAIL** — 17 (spike unit tests) |
| Ruff format | yes | PASS |
| basedpyright (full CI paths) | yes | **FAIL** — 53 errors |
| basedpyright F42 production (`packages/rag`, chat-rag, eval) | yes (prod) | PASS — 0 errors |
| H0c `test_cors_policy.py` | yes | PASS (env-gated cases skipped) |
| F42 unit + UJ-055 e2e | yes (delta) | PASS |
| Full pytest + integration (Postgres) | yes (CI) | **SKIPPED locally** — Docker/Postgres unavailable |
| Frontend lint + Vitest (both apps) | yes | PASS |
| Playwright `make test-ui` | yes | PASS (42/2 skip staging) |
| FE coverage gate (chat-rag) | yes (CI) | PASS |
| `make audit` / pip-audit | yes | **FAIL** — CVE-2026-12075/61/74 (nltk) |
| Secrets / Modal DB guard / OpenAPI | yes | PASS |
| AC-RQ6 / ISS-008 Hy1 staging floors | no (ship-path) | ADVISORY — deferred (`hy1-ship-gate.md`) |
| Staging H4–H5 / live Modal | no | ADVISORY — env unset |
| Out-of-scope uncommitted Modal/AWQ work | no | ADVISORY — exclude from F42 blame |

## Commands run

```bash
# Lint / format / types (CI parity)
uv run ruff check apps packages tests infra scripts
uv run ruff format --check apps packages tests infra scripts
uv run basedpyright apps packages tests infra scripts
uv run ruff check --select F401,F841 apps packages tests infra scripts
uv run basedpyright packages/rag apps/chat-rag-backend packages/eval

# F42 + connectivity (blocking delta)
uv run pytest tests/unit/rag/test_context_packing.py \
  tests/unit/rag/test_multi_query.py \
  tests/unit/eval/test_sandbox_f42_packing.py \
  tests/e2e/test_uj055_h7_p1_ask.py \
  tests/unit/test_cors_policy.py \
  tests/unit/scripts/test_spike_hybrid_sweep.py -q
uv run pytest tests/unit/chat_rag/test_config.py tests/unit/chat_rag/test_service.py -q
uv run pytest tests/unit/internal_write_api/test_eval_service.py -k 'fixture_path' -q

# Broader Python (env-gated locally)
uv run pytest tests/unit tests/privacy tests/e2e tests/smoke tests/eval tests/bugs -q
# → many ERROR/FAILED from Postgres connection refused (no Docker)

# Frontends
cd apps/chat-rag-frontend && npm run lint && npm test -- --run
cd apps/data-management-frontend && npm run lint && npm test -- --run
make test-coverage-fe FE_APP=chat-rag-frontend
make test-ui

# Security / platform
make audit   # or pip-audit + audit/pip-audit-ignore.txt
bash scripts/check_secrets.sh
bash scripts/check_modal_no_database_url.sh
bash scripts/check_openapi_specs.sh
bash scripts/check_no_operator_specs_tracked.sh
# gitleaks: not installed → SKIPPED
```

## Per-check details

### Lint (FAIL)

17 ruff issues, all under `tests/unit/scripts/test_spike_*.py` (S019 research harness units on HEAD):

| Rule | Count | Files |
|------|------:|-------|
| PLR2004 | 12 | `test_spike_e1_shadow_f36`, `test_spike_embed_retrieval`, `test_spike_hybrid_sweep`, `test_spike_model_prompt_baseline` |
| PT018 | 2 | `test_spike_e1_shadow_f36`, `test_spike_embed_retrieval` |
| PLC0415 | 1 | `test_spike_embed_retrieval` |

F401/F841: **PASS**. Format: **PASS** (441 files).

### Typecheck (FAIL)

53 basedpyright errors, 1 warning (`test_modal_url_validate` missing-module-source).

| Area | Errors | Notes |
|------|-------:|-------|
| `tests/unit/scripts/test_spike_*.py` | ~50 | `reportAny` / unknown from dynamic `importlib` script loads |
| `tests/e2e/test_uj055_h7_p1_ask.py:103` | 1 | `body` is `Any` (**F42**) |
| `tests/unit/internal_write_api/test_eval_service.py:589` | 1 | `fixture_path` is `Any` (ISS-008 / UJ-056) |

F42 **production** (`packages/rag`, `apps/chat-rag-backend`, `packages/eval`): **0 errors**.

### Tests (Python)

| Suite | Result |
|-------|--------|
| Packing + multi-query + sandbox F42 + UJ-055 + H0c + spike hybrid | **37 passed**, 11 skipped |
| ChatRAG `test_config` + `test_service` | **PASS** |
| ISS-008 `_fixture_path` units (`-k fixture_path`) | **3 passed** |
| `test_execute_eval_run_staging_profile_uses_staging_golden` | **SKIPPED/ERROR** — needs Postgres |
| `tests/integration` + DB-backed unit/e2e | **SKIPPED** — `docker=no`, Postgres refused |
| Spike hybrid/e1 units (runtime) | **PASS** (lint/types still fail CI) |

H0c: **PASS** (blocking). H0i integration: env-gated SKIPPED (same as 08).

### Frontend / UI / coverage

| App / job | Result |
|-----------|--------|
| chat-rag ESLint | PASS (0 errors) |
| chat-rag Vitest | 162/162 PASS |
| DM ESLint | PASS (0 errors; 3 react-refresh warnings) |
| DM Vitest | 697/697 PASS |
| Playwright T0-ui | 42 passed; 2 staging specs skipped (URLs unset) |
| `make test-coverage-fe FE_APP=chat-rag-frontend` | exit 0 PASS |
| Full `make test-unit-coverage` (Python+FE) | not re-run (Postgres unavailable for many unit packages) |

### Security

| Layer | Result |
|-------|--------|
| pip-audit / `make audit` | **FAIL** — nltk 3.9.4: CVE-2026-12075 (SSRF), CVE-2026-12061 (ReDoS), CVE-2026-12074 (path traversal); fix 3.10.0+. Ignore file has older `PYSEC-2026-597` only |
| `check_secrets.sh` | PASS |
| gitleaks working-tree | **SKIPPED** — binary not installed |
| Dangerous patterns | PASS — no `pickle.loads` / bare `eval(` / `exec(` in apps/packages production code |

Workspace `vecinita-*` packages skipped by pip-audit (expected).

### Template / data / connectivity

| Item | Status |
|------|--------|
| Layout `apps/*` `packages/*` `tests/` `openapi/` `infra/` | OK |
| Modal imports confined to `infra/modal/` + deploy/session scripts | OK |
| `check_modal_no_database_url.sh` | PASS |
| `check_openapi_specs.sh` | PASS |
| Operator specs not tracked | PASS |
| D1–D5, D8–D9 | verified |
| D6 FastEmbed / D7 Qwen | verified (`vecinita` workspace per staging state) |
| Live Modal URL validate | SKIPPED — `VECINITA_MODAL_*` unset |
| H4–H5 staging frontends | ADVISORY — `VECINITA_STAGING_*` unset |

## F42 delta surface (functional)

| Surface | Evidence | QA |
|---------|----------|-----|
| `packages/rag` packing + multi-query | `test_context_packing` / `test_multi_query` | PASS |
| ChatRAG config/service wire-up | `test_config` / `test_service` (P1 packed prompt) | PASS |
| F36 eval sandbox packing | `test_sandbox_f42_packing` | PASS |
| UJ-055 / TC-170–173 | `test_uj055_h7_p1_ask.py` | PASS |
| UJ-056 / TC-174 fixture path | `_fixture_path` units | PASS |
| TC-175 / AC-RQ6 Hy1 floors | `hy1-ship-gate.md` | deferred ship-path |
| H0c CORS | `test_cors_policy.py` | PASS |

Cross-check: parallel `docs/sessions/S019-retrieval-quality/reports/e2e-report.md` also **PASS** on T0 F42.

## Deferred / out of scope (advisory)

### AC-RQ6 / ISS-008 ship-path

Staging Hy1 floors (relevancy ≥ 0.28, faithfulness ≥ 0.91) and write-api deploy for
`qa_pairs_staging.json` remain **deferred** to 12/13 per `hy1-ship-gate.md`. Not blocking
for this delta QA overall classification (blockers are CI lint/types/audit).

### Uncommitted out-of-F42-scope files (do not require clean tree)

| Path | Note |
|------|------|
| `infra/modal/llm_app.py` | Modal LLM — not F42 |
| `infra/modal/llm_playground_app.py` | Playground — not F42 |
| `packages/shared-schemas/.../playground_hf_registry.py` (+ tests) | Registry — not F42 |
| `tests/unit/modal/test_llm_volume_manifest.py` | Modal — not F42 |
| `tests/unit/modal/test_llm_engine_awq_kwargs.py` | AWQ — untracked |
| `scripts/deploy/_tmp_proxy_key_check.py` | temp deploy helper — untracked |
| `workflow-state.yaml` | WSM updates (expected) |
| `docs/sessions/S019-retrieval-quality/reports/e2e-report.md` | 10-e2e parallel artifact |

## Findings for 11-verify-impl

| ID | Severity | Finding | Suggested action |
|----|----------|---------|------------------|
| QA-S019-B01 | **blocking** | Ruff: 17 issues in `tests/unit/scripts/test_spike_*.py` (PLR2004/PT018/PLC0415) — CI `ruff check` will fail | Fix spike tests or add documented per-file-ignores for research harness units |
| QA-S019-B02 | **blocking** | basedpyright: 53 errors — spike dynamic imports + `test_uj055_h7_p1_ask.py:103` (`body` Any) + `test_eval_service.py:589` (`fixture_path` Any) | Typed wrappers for spike loaders; narrow JSON/`call_args` types in F42/ISS-008 tests |
| QA-S019-B03 | **blocking** | pip-audit: nltk 3.9.4 CVEs CVE-2026-12075/12061/12074 (fix ≥3.10.0); not listed in `audit/pip-audit-ignore.txt` | Bump nltk if LlamaIndex allows, else add CVE IDs + pin rationale to ignore file (same pattern as existing nltk PYSEC) |
| QA-S019-A01 | advisory | AC-RQ6 / TC-175 Hy1 staging floors deferred until ISS-008 write-api deploy | Track via `hy1-ship-gate.md` → 12/13 |
| QA-S019-A02 | advisory | Local Docker/Postgres unavailable — integration + DB-backed unit/e2e not executed | Re-run H0i / full pytest when Docker up; CI remains merge gate |
| QA-S019-A03 | advisory | Staging H4–H5 / live Modal URLs unset | `verify_connectivity.sh` / staging-runbook when URLs set |
| QA-S019-A04 | advisory | Uncommitted Modal/playground/AWQ/`_tmp_proxy_*` files outside F42 | Keep out of F42 PR; do not block QA clean-tree |
| QA-S019-A05 | advisory | gitleaks not installed locally | Install for working-tree scan; CI `--no-git` remains source of truth |
| QA-S019-A06 | advisory | Outdated transitive deps (fastapi, openai major, nltk, etc.); LlamaIndex pin stack | Intentional pins per dependency-inventory; only act on blocking CVEs (B03) |

## Env skips

| Prerequisite | Local | Impact |
|--------------|-------|--------|
| Docker / Postgres | unavailable | integration + many DB unit/e2e ERROR — **not** overall FAIL alone |
| `VECINITA_STAGING_*` frontend URLs | unset | H4–H5 advisory; Playwright staging 2 skipped |
| `VECINITA_MODAL_EMBED_URL` / `LLM_URL` | unset | live Modal validate SKIPPED |
| gitleaks | not installed | history/tree leak scan SKIPPED |

## Remediation (S019-D47 — 2026-08-01)

User chose fix-in-place for B01–B03. Changes (committed on evolve/EV-016-retrieval-quality):

| ID | Fix |
|----|-----|
| B01 | Typed Protocol loaders + ruff constants / split asserts in `tests/unit/scripts/test_spike_*.py` |
| B02 | Same Protocol loaders; `response_json_object` in UJ-055; cast kwargs in ISS-008 fixture_path assert |
| B03 | Hold `nltk>=3.9.4,<3.10` override; document CVE-2026-12075/61/74 in `audit/pip-audit-ignore.txt` (3.10 inisec false-positive blocks `regex` when `.venv` is under repo root) |

Re-check commands (all PASS):

```bash
uv run ruff check apps packages tests infra scripts
uv run basedpyright apps packages tests infra scripts   # 0 errors
make audit                                              # 0 vulns, 4 ignored
uv run pytest tests/unit/scripts/test_spike_*.py \
  tests/e2e/test_uj055_h7_p1_ask.py \
  tests/unit/rag/test_context_packing.py \
  tests/unit/rag/test_multi_query.py \
  tests/unit/test_cors_policy.py -q
```

| ID | Severity | Status after remediation |
|----|----------|--------------------------|
| QA-S019-B01 | was blocking | **cleared** |
| QA-S019-B02 | was blocking | **cleared** |
| QA-S019-B03 | was blocking | **cleared** (documented ignore + pin) |
| QA-S019-A01–A06 | advisory | unchanged |

## Phase / plan alignment

- Evolve **EV-016** / feature **F42**; Phase 21 M91–M93 code complete @ `257486f` (+ remediation WIP).
- 08-verify-build PASS (delta); 09 initial FAIL → remediation → **pass_with_advisories**.
- **10-e2e** T0 PASS (UJ-055). Ready for **11-verify-impl**.

---

```
Enter this into the chat to continue:
@.cursor/skills/11-verify-impl/SKILL.md
```
