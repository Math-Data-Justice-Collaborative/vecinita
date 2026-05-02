# CI Evidence (Feature 017)

## SC-001 parity evidence

- DM/frontend pact: pass (`apps/data-management-frontend/tests/pact/dm-api.pact.test.ts`)
- Gateway/frontend pact: pass (`frontend/tests/pact/chat-gateway.pact.test.ts`)
- Backend parity integration: pass (`backend/tests/integration/test_corpus_dm_gateway_parity.py`)
- System parity/read-only/fail-closed: pass (`frontend/tests/e2e/corpus-parity.spec.ts`, `frontend/tests/e2e/documents-readonly.spec.ts`, `frontend/tests/e2e/documents-fail-closed.spec.ts`)

## SC-003 rolling 30-day pass-rate method

- Source: CI provider build history for merge-blocking pact/contract jobs.
- Window: trailing 30 calendar days from release cut date.
- Metric:
  - `pact_pass_rate = passed_pact_runs / total_pact_runs`
  - `contract_pass_rate = passed_contract_runs / total_contract_runs`
- Current value capture process:
  - Query CI run history for workflow `test.yml`.
  - Filter jobs for pact and contract suites.
  - Export counts + computed percentages to release evidence bundle.

## Local command evidence

- `python3 scripts/ci/impacted_corpus_test_suites.py --mode impacted --emit-json` (pass)
- `cd backend && uv run pytest tests/integration/test_corpus_visibility_slo.py tests/integration/test_corpus_partial_failure_recovery.py tests/integration/test_corpus_concurrency_resolution.py -q --tb=short` (pass)
