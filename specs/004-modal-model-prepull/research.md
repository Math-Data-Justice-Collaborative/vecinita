# Research: Startup Model Pre-Pull and Lifecycle Extensibility

## Decision 1: Use explicit startup preload before ready state

- **Decision**: Keep model preload in startup lifecycle and gate readiness on successful completion.
- **Rationale**: Eliminates first-request download delays, aligns with spec requirement for deterministic readiness, and fits Modal cold-start best practices for predictable serve behavior.
- **Alternatives considered**:
  - Pull lazily on first request: rejected due to latency spikes and user-visible failures.
  - Background pull after ready: rejected because it violates readiness semantics and complicates failure handling.

## Decision 2: Apply bounded retries with fail-fast for pull/connect failures

- **Decision**: Retry startup pull/connect operations a fixed number of times with bounded delay, then fail startup with a clear error.
- **Rationale**: Handles transient network/backend issues while preventing indefinite startup loops that consume resources and hide real outages.
- **Alternatives considered**:
  - No retries: rejected as too brittle for transient failures.
  - Unlimited retries: rejected because it can stall deployment health and autoscaling behavior.

## Decision 3: Default teardown is cache-preserving

- **Decision**: On shutdown, clean temporary runtime artifacts only and retain reusable model cache artifacts in Modal Volume.
- **Rationale**: Improves restart speed and reduces repeated model downloads while maintaining operational cleanliness.
- **Alternatives considered**:
  - Full cleanup of all artifacts: rejected due to repeated cold-start penalty.
  - No cleanup at all: rejected due to risk of temp-file accumulation and operational drift.

## Decision 4: Ordered lifecycle plugin registry

- **Decision**: Use a deterministic plugin registry with explicit phase (`startup`, `steady_state`, `teardown`) and execution order.
- **Rationale**: Supports extensibility without sacrificing predictability, testability, and backward compatibility.
- **Alternatives considered**:
  - Single monolithic strategy object: rejected as harder to compose and test.
  - Unordered callback discovery: rejected due to non-deterministic behavior across deployments.

## Decision 5: Connection testing must include both unit and integration levels

- **Decision**: Add required coverage for connection paths at two layers:
  - Unit: mocked Ollama/Modal failure and retry behavior.
  - Integration: lifecycle startup/shutdown and backend connectivity flows.
- **Rationale**: Unit tests keep failure-path validation fast and deterministic; integration tests validate real orchestration and container assumptions.
- **Alternatives considered**:
  - Unit tests only: rejected because container/lifecycle behavior can diverge from mocks.
  - Integration tests only: rejected due to slower feedback and higher flake risk.

## Decision 6: Emit structured lifecycle observability events

- **Decision**: Standardize events for preload start/success/failure, retries, teardown start/success/failure, and plugin registration outcomes.
- **Rationale**: Enables production debugging without ad-hoc instrumentation and aligns with constitution operational simplicity requirements.
- **Alternatives considered**:
  - Minimal logging only on errors: rejected due to weak diagnostics for intermittent failures.
