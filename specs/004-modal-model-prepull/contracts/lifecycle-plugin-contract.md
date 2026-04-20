# Contract: Lifecycle Plugin Registry for Modal Model Service

## Purpose

Define deterministic lifecycle extensibility for startup, steady-state, and teardown phases.

## Scope

- Applies to `services/model-modal` runtime lifecycle orchestration.
- Covers plugin registration, validation, ordering, and failure handling.

## Lifecycle Phases

- `startup`: preload model and validate required runtime prerequisites.
- `steady_state`: optional runtime hooks while service is ready.
- `teardown`: shutdown hooks for cleanup and state finalization.

## Plugin Contract

Each plugin must declare:

- `plugin_id` (unique string)
- `phase` (`startup | steady_state | teardown`)
- `order` (integer; deterministic execution order)
- `required` (boolean)
- `enabled` (boolean)

## Registration Rules

1. Plugin order must be unique per phase.
2. Required plugins must resolve and validate at startup.
3. Invalid registration (missing required plugin, duplicate order, unknown phase) fails startup.

## Execution Rules

1. Plugins execute in ascending `order` within phase.
2. Disabled plugins are skipped and logged.
3. `startup` phase failures:
   - Retry only if failure is classified transient and retry budget remains.
   - Fail fast when retry budget is exhausted.
4. `teardown` phase failures:
   - Must be logged explicitly with actionable context.
   - Must not silently mark cleanup as successful.

## Default Strategy

- The default strategy is cache-preserving teardown:
  - Keep reusable model artifacts in persistent volume.
  - Remove temporary runtime artifacts created during active execution.

## Observability Requirements

Emit lifecycle event records for:

- preload start/success/failure
- retry attempts
- teardown start/success/failure
- plugin validation failures

Each event must include a correlation identifier and timestamp.

## Implementation Notes (2026-04-20)

- Implemented in `services/model-modal/src/vecinita/lifecycle.py` with
  `PluginRegistry`, `LifecyclePlugin`, and deterministic ascending `order`.
- Startup and teardown defaults are registered via
  `make_default_registry(..., startup_hook, teardown_hook)`.
- Startup execution and retry/fail-fast orchestration is integrated in
  `services/model-modal/src/vecinita/app.py` (`_run_startup_lifecycle`).
- Teardown execution and explicit failure surfacing is integrated in
  `services/model-modal/src/vecinita/app.py` (`_run_teardown_lifecycle`).
- Structured lifecycle event payloads with correlation IDs and timestamps are
  generated through `make_lifecycle_event(...)`.
