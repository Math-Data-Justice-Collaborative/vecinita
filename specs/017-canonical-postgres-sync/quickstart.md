# Quickstart: Canonical Corpus Sync Validation

Use this after implementation tasks are generated to validate the feature end-to-end.

## 1) Configure environment

- Ensure `DATABASE_URL` points to the intended Postgres instance for the test environment.
- Do not enable mock/placeholder corpus sources in production-profile validation.
- Ensure frontend and API services use their normal integration URLs and credentials.

## 2) Run contract and pact suites

- Run DM boundary pact tests (consumer and provider):
  - `cd apps/data-management-frontend && npm run test:pact:corpus-sync`
  - `cd backend && PYTHONPATH=../apis/data-management-api/packages/service-clients:../apis/data-management-api/packages/shared-schemas:../apis/data-management-api/packages/shared-config:../apis/data-management-api/apps/backend uv run pytest ../apis/data-management-api/tests/pact/test_dm_frontend_provider_verify.py -q --tb=short`
- Run gateway boundary pact tests (consumer and provider):
  - `cd frontend && npm run test:pact -- tests/pact/chat-gateway.pact.test.ts`
  - `cd backend && uv run pytest tests/pact/test_frontend_documents_provider_verify.py -q --tb=short`
- Run contract tests for changed corpus endpoints/schemas:
  - `cd backend && uv run pytest tests/contracts/test_corpus_source_policy_contract.py tests/contracts/test_gateway_corpus_projection_contract.py -q --tb=short`

Example entrypoint:

```bash
make ci
```

## 3) Run persistence integration checks

- Validate integration gates:
  - `cd backend && uv run pytest tests/integration/test_corpus_dm_gateway_parity.py tests/integration/test_corpus_fail_closed_behavior.py tests/integration/test_corpus_visibility_slo.py tests/integration/test_corpus_partial_failure_recovery.py tests/integration/test_corpus_concurrency_resolution.py -q --tb=short`

## 4) Run Playwright system scenarios

- Execute corpus system gate:
  - `cd frontend && npm run test:e2e:corpus-sync`

## 5) Validate suite gating

- Confirm per-suite gate results are present for pact, contract, integration, and system layers.
- Confirm thresholds are met: pact >= 95%, contract >= 95%, integration >= 90%, system >= 85% (line coverage).
- Confirm impacted suites:
  - `python3 scripts/ci/impacted_corpus_test_suites.py --mode impacted --emit-json`

## 5b) Capture rolling-window evidence

- Record 30-day rolling pact/contract pass-rate from repository CI provider history.
- Add this evidence to `specs/017-canonical-postgres-sync/artifacts/ci-evidence.md`.

## 6) Final gate

```bash
make ci
```

Feature is merge-ready only when all required suite gates and root CI pass.
