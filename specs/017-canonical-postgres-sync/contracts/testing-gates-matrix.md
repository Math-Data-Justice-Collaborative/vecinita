# Contract: Testing Gates Matrix

## Purpose

Define required suite coverage and execution gates for corpus synchronization changes.

## Required Suites

| Suite | Primary Risk Covered | Mandatory Gate |
|-------|----------------------|----------------|
| Pact | Consumer-provider request/response drift | Consumer + provider verification must pass on impacted boundaries |
| Contract | Provider schema/behavior regressions | Contract tests must pass for changed endpoints/models |
| Integration | Persistence and propagation correctness | DB-backed propagation checks must pass |
| System (Playwright) | User-visible end-to-end behavior | Core journeys and outage/fail-closed behavior must pass |

## Impact-to-Suite Mapping

| Change Type | Required Suites |
|-------------|-----------------|
| DM frontend API client/request mapping | Pact (DM boundary), contract (DM provider), integration, system |
| DM API response/route/schema affecting corpus | Pact (DM boundary), contract, integration, system |
| Gateway response/route/schema affecting documents tab | Pact (gateway boundary), contract, integration, system |
| Canonical corpus persistence/query logic | Integration, system, and impacted pact/contract suites |
| Documents tab rendering or read path behavior | Pact (gateway boundary), integration, system |

## Coverage Gate Policy

- CI must enforce per-suite minimums for pact, contract, integration, and system suites.
- CI must fail if any impacted required suite is skipped, missing, or below threshold.
- Combined aggregate coverage alone is not sufficient for merge approval.
- Minimum suite thresholds for this feature are pact >= 95%, contract >= 95%, integration >= 90%, and system >= 85%, measured as line coverage by each suite's primary CI reporter.
- CI threshold env keys in `.github/workflows/test.yml`:
  - `PACT_COVERAGE_THRESHOLD`
  - `CONTRACT_COVERAGE_THRESHOLD`
  - `INTEGRATION_COVERAGE_THRESHOLD`
  - `SYSTEM_COVERAGE_THRESHOLD`
- Contract drift synchronization gate runs in `.github/workflows/test.yml` (`Contract drift synchronization gate` step).

## Playwright Expansion Guidance

- Expand unit/integration adjacency where failures are hard to isolate from system tests.
- Keep Playwright focused on critical user journeys:
  - parity of displayed corpus across surfaces,
  - read-only behavior of documents tab,
  - 30-second write-to-visibility SLO,
  - fail-closed outage state.

## Release Readiness Rule

- Release candidate is blocked unless all required suites for impacted components pass in CI and `make ci` passes from repo root.

## Implemented Gate File Map

- DM consumer pact: `apps/data-management-frontend/tests/pact/dm-api.pact.test.ts`
- DM provider pact verify: `apis/data-management-api/tests/pact/test_dm_frontend_provider_verify.py`
- Gateway consumer pact: `frontend/tests/pact/chat-gateway.pact.test.ts`
- Gateway provider pact verify: `backend/tests/pact/test_frontend_documents_provider_verify.py`
- Corpus contracts: `backend/tests/contracts/test_corpus_source_policy_contract.py`, `backend/tests/contracts/test_gateway_corpus_projection_contract.py`
- Corpus integrations: `backend/tests/integration/test_corpus_dm_gateway_parity.py`, `backend/tests/integration/test_corpus_fail_closed_behavior.py`, `backend/tests/integration/test_corpus_visibility_slo.py`, `backend/tests/integration/test_corpus_partial_failure_recovery.py`, `backend/tests/integration/test_corpus_concurrency_resolution.py`
- Corpus system tests: `frontend/tests/e2e/corpus-parity.spec.ts`, `frontend/tests/e2e/documents-readonly.spec.ts`, `frontend/tests/e2e/documents-fail-closed.spec.ts`
