# Implementation Plan: Startup Model Pre-Pull and Lifecycle Extensibility for Modal Model Service

**Branch**: `004-modal-model-prepull` | **Date**: 2026-04-20 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `specs/004-modal-model-prepull/spec.md`

**Note**: This plan follows `/speckit.plan` phases and includes Modal best practices plus unit/integration testing for connection paths.

## Summary

Introduce a deterministic lifecycle system for `services/model-modal` that pre-pulls configured models before readiness, supports pluggable startup/steady-state/teardown hooks via an ordered registry, and applies bounded retry + fail-fast semantics for pull failures. The design preserves cache artifacts on shutdown to reduce restart latency, while expanding test coverage for service and backend connection behavior through explicit unit and integration suites.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: Modal SDK, FastAPI, Ollama Python client, pydantic-settings, pytest  
**Storage**: Modal Volume (`vecinita-models`) for model artifacts and cache metadata  
**Testing**: `pytest` with unit tests (mocked Ollama/Modal interactions) and integration tests (container lifecycle and connection flows)  
**Target Platform**: Modal serverless Linux containers, plus local Docker Compose for integration parity  
**Project Type**: Backend model-inference web service on Modal  
**Performance Goals**: First inference after cold start without blocking download in at least 95% of startup cycles; startup failure surfaced within one retry window  
**Constraints**: Deterministic lifecycle hook order; bounded retries only; preserve reusable cache; no silent teardown failure  
**Scale/Scope**: Single service (`services/model-modal`) with updates to app lifecycle handling, config, observability events, and tests

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design. Source: `.specify/memory/constitution.md`.*

- **Community benefit**: **Pass** - improves reliability of inference used by community-facing assistant surfaces.
- **Trustworthy retrieval**: **Pass** - this feature is infrastructure-focused and does not degrade attribution/grounding behavior.
- **Data stewardship**: **Pass** - model artifact handling stays in defined persistent volume; explicit lifecycle logs improve auditability.
- **Safety & quality**: **Pass** - includes unit + integration testing for connection paths and lifecycle failures.
- **Service boundaries**: **Pass** - changes are scoped to `services/model-modal` contracts and documented interfaces.

## Project Structure

### Documentation (this feature)

```text
specs/004-modal-model-prepull/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── lifecycle-plugin-contract.md
│   └── connection-testing-contract.md
└── tasks.md            # Created by /speckit.tasks
```

### Source Code (repository root)

```text
services/model-modal/
├── src/vecinita/
│   ├── app.py                 # Modal app + lifecycle behavior
│   ├── config.py              # Model and lifecycle settings
│   ├── volumes.py             # Modal volume bindings
│   ├── api/routes.py          # Health/chat endpoints
│   └── models/
│       └── ollama.py          # Backend connection handling
├── tests/
│   ├── test_app_runtime.py
│   ├── test_models_runtime.py
│   ├── test_routes.py
│   └── test_container_setup.py
└── .github/workflows/
    ├── tests.yml
    └── deploy.yml
```

**Structure Decision**: Keep implementation fully inside `services/model-modal` and extend existing runtime/test files with lifecycle and connection-focused coverage instead of introducing new cross-service modules.

## Phase 0 — Research (`research.md`)

Research resolves the following implementation decisions:

1. Modal lifecycle best practices for startup preloading and safe shutdown.
2. Retry strategy for model-pull/connect failures under serverless startup constraints.
3. Test strategy for connection reliability (unit and integration) without adding flakiness.
4. Plugin registry design that stays deterministic and backwards compatible.

## Phase 1 — Design (`data-model.md`, `contracts/`, `quickstart.md`)

- **Data model**: Define lifecycle configuration entities, plugin metadata, pull attempts, and readiness states.
- **Contracts**:
  - `contracts/lifecycle-plugin-contract.md`: lifecycle hook and ordering contract.
  - `contracts/connection-testing-contract.md`: required unit/integration coverage for connection paths.
- **Quickstart**: Document local verification steps for startup pre-pull, teardown behavior, and integration test execution.

## Testing Strategy (Required)

- **Unit tests**:
  - Validate plugin registry order resolution and default behavior.
  - Validate bounded retry and fail-fast outcomes for pull/connect failures.
  - Validate cache-preserving teardown semantics and non-silent failure logging.
  - Validate invalid plugin registration fails startup.
- **Integration tests**:
  - Simulate cold start with empty cache and ensure readiness only after preload.
  - Simulate warm start with cached model and verify no full re-download.
  - Simulate transient backend connection failures and verify bounded retries.
  - Simulate shutdown flow and verify temp cleanup while keeping reusable cache artifacts.

## Re-evaluated Constitution Check (Post-design)

- **Community benefit**: **Pass** - reduced first-request failures and better uptime.
- **Trustworthy retrieval**: **Pass** - no user-facing grounding regressions introduced.
- **Data stewardship**: **Pass** - explicit artifact handling and lifecycle logging.
- **Safety & quality**: **Pass** - contracts and test plan cover high-risk lifecycle paths.
- **Service boundaries**: **Pass** - no new hidden coupling; contracts capture service behavior.

## Complexity Tracking

No constitution violations requiring exception handling.
