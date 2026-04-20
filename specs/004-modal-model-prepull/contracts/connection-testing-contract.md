# Contract: Connection Testing for Startup and Lifecycle Flows

## Purpose

Define mandatory unit and integration tests for all startup/shutdown connection paths in `services/model-modal`.

## Connection Surfaces Covered

1. Modal container startup lifecycle to local Ollama daemon.
2. Ollama client connectivity for list/pull/chat.
3. Modal Volume artifact commit and reuse behavior.
4. Lifecycle plugin execution and validation interactions.

## Unit Test Requirements

Unit tests must validate with mocks/fakes:

1. Startup retries:
   - transient failure retries up to limit.
   - retry exhaustion triggers deterministic startup failure.
2. Plugin registry validation:
   - duplicate order and missing required plugin fail startup.
   - disabled plugins are skipped.
3. Cache behavior:
   - existing model skips full pull.
   - missing model triggers pull then commit.
4. Teardown behavior:
   - temp cleanup attempted.
   - cache artifacts preserved by default.
   - teardown failure emitted as explicit error event.

## Integration Test Requirements

Integration tests must validate end-to-end lifecycle behavior:

1. Cold startup path:
   - empty cache requires preload before readiness.
2. Warm startup path:
   - cached model allows startup without full re-download.
3. Transient connection failure path:
   - bounded retries are applied.
   - startup fails after retry limit with clear reason.
4. Shutdown path:
   - teardown hooks execute in deterministic order.
   - cache artifacts remain available for subsequent startup.

## Test Stability Requirements

- Avoid real external network dependencies beyond local test containers/mocks.
- Use deterministic timeout and retry values for tests.
- Keep integration tests runnable in CI without manual setup steps.

## CI Gate Expectations

- Unit and integration lifecycle/connection suites are mandatory in `make test` for `services/model-modal`.
- Regressions in lifecycle connection behavior block merge readiness.

## Implementation Notes (2026-04-20)

- Unit coverage implemented in:
  - `services/model-modal/tests/test_app_runtime.py`
  - `services/model-modal/tests/test_models_runtime.py`
- Integration-style lifecycle wiring checks implemented in:
  - `services/model-modal/tests/test_container_setup.py`
- Added assertions for:
  - environment-driven startup model resolution wiring
  - transient retry exhaustion branch presence
  - permanent failure classification path for storage-like pull failures
  - omitted startup model fallback behavior
  - startup-to-ready latency evidence fields (`attempt_count`, `retry_window_ms`)
