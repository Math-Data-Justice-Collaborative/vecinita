# Feature Specification: Startup Model Pre-Pull for Modal LLM Service

**Feature Branch**: `004-modal-model-prepull`  
**Created**: 2026-04-20  
**Status**: Draft  
**Input**: User description: "For the model-modal, add a startup command that pre-pulls the model so deployments do not fail with default-model-missing behavior and teams can choose different models."

## Clarifications

### Session 2026-04-20

- Q: Should extensibility cover startup only or full lifecycle behavior? → A: Full lifecycle extensibility (startup + steady-state + teardown as pluggable strategies).
- Q: What teardown behavior should be the default? → A: Cache-preserving teardown (keep reusable model artifacts; clean temporary runtime files).
- Q: What startup pull failure policy should be used? → A: Bounded retries with fail-fast after retry limit.
- Q: What extensibility structure should govern lifecycle behavior? → A: Ordered lifecycle plugin registry with deterministic hook order.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Ensure default model is ready before traffic (Priority: P1)

As an operator, I want the model service to pull and cache the configured default model during startup so the first user request does not trigger an on-demand pull delay or startup warning.

**Why this priority**: This directly addresses the observed runtime error and prevents first-request latency and instability in production.

**Independent Test**: Deploy a new instance with an empty model cache and verify startup completes with the configured default model already available before any inference request is sent.

**Acceptance Scenarios**:

1. **Given** a fresh deployment with no cached model files, **When** the service starts, **Then** it preloads the configured default model and reports readiness only after preload completes.
2. **Given** the default model is already present in persistent storage, **When** the service starts, **Then** it skips redundant download work and reaches ready state without re-pulling unchanged model assets.

---

### User Story 2 - Allow model selection per deployment (Priority: P2)

As an operator, I want to configure which model is pre-pulled at startup so different environments can use different model families without code changes.

**Why this priority**: Environment-level flexibility is needed to support experimentation, cost tuning, and workload-specific quality targets.

**Independent Test**: Start two separate deployments with different configured model identifiers and verify each deployment preloads and serves its own configured model.

**Acceptance Scenarios**:

1. **Given** a deployment configuration that specifies Model A, **When** the service starts, **Then** Model A is pre-pulled and available for inference.
2. **Given** a deployment configuration that specifies Model B, **When** the service starts, **Then** Model B is pre-pulled and available for inference.

---

### User Story 3 - Fail fast on invalid model configuration (Priority: P3)

As an operator, I want startup to fail with a clear actionable message when the configured model cannot be pulled so I can correct configuration issues before serving traffic.

**Why this priority**: Clear startup failure behavior prevents partially healthy deployments and shortens incident resolution time.

**Independent Test**: Configure an invalid or inaccessible model identifier and verify startup exits with a clear reason and no false-ready health state.

**Acceptance Scenarios**:

1. **Given** an invalid model identifier, **When** startup preload runs, **Then** startup fails and logs an explicit configuration error.
2. **Given** a temporary model source outage, **When** startup preload runs, **Then** startup reports pull failure and does not claim readiness until a successful pull occurs.
3. **Given** a scale-down or replacement event, **When** shutdown executes, **Then** the service runs the configured teardown strategy and exits without corrupting reusable model cache state.
4. **Given** a transient model source failure during startup preload, **When** retries are attempted up to the configured limit, **Then** startup fails fast with a clear actionable error after the final failed attempt.

---

### Edge Cases

- What happens when model pull succeeds but integrity verification fails before ready state?
- How does the system handle partial model files left from interrupted prior downloads?
- What happens when startup model selection is omitted and no safe default is available?
- How does startup behave when storage limits are reached while pulling large models?
- How does the system recover when temporary runtime artifacts cannot be fully cleaned during teardown?

## Requirements *(mandatory)*

### Functional Requirements

**Requirement ID note**: Entries with an `A` suffix (for example, `FR-005A`) are normative refinements of the corresponding base requirement and do not replace it.

- **FR-001**: System MUST execute a startup pre-pull step for the configured default model before exposing a ready service state.
- **FR-002**: System MUST allow operators to set the startup model identifier through deployment configuration without modifying source code.
- **FR-003**: System MUST support startup pre-pull for different valid model identifiers across environments (for example, development, staging, and production).
- **FR-004**: System MUST detect when the configured model already exists in persistent storage and avoid redundant full re-download.
- **FR-005**: System MUST fail startup with a clear actionable error if model pre-pull cannot complete successfully.
- **FR-005A**: Startup failure errors for model pre-pull MUST include, at minimum, `error_code`, `failure_phase`, `attempt_count`, and `recommended_operator_action`.
- **FR-006**: System MUST emit startup observability events that indicate pre-pull start, pre-pull success, and pre-pull failure outcomes.
- **FR-006A**: Lifecycle observability events MUST use a consistent schema containing `event_type`, `phase`, `correlation_id`, `timestamp`, and `details` fields for all startup and teardown lifecycle outcomes.
- **FR-007**: Users MUST be able to send the first inference request after startup without triggering an additional blocking model download step.
- **FR-008**: System MUST provide an extensibility contract that allows separate pluggable strategies for startup, steady-state lifecycle handling, and teardown behavior.
- **FR-009**: System MUST execute the configured teardown strategy during container shutdown and handle teardown failures with explicit non-silent reporting.
- **FR-010**: System MUST preserve compatibility of existing deployments by defining a default lifecycle strategy that requires no custom extension implementation.
- **FR-011**: System MUST treat cache-preserving teardown as the default behavior, retaining reusable model artifacts while cleaning temporary runtime files on shutdown.
- **FR-012**: System MUST apply bounded retry attempts for startup model pull operations and fail startup deterministically when retry limits are exhausted.
- **FR-012A**: The retry window MUST be explicitly defined as `retry_limit * retry_backoff_ms`, and startup MUST terminate as failed within one configured retry window after the first failed preload attempt.
- **FR-013**: System MUST support an ordered lifecycle plugin registry that executes startup, steady-state, and teardown hooks in deterministic order.
- **FR-014**: System MUST validate lifecycle plugin registration at startup and fail fast when required hooks are missing or invalid.
- **FR-015**: System MUST define behavior when startup model selection is omitted, including either a validated safe default model or deterministic startup failure with actionable operator guidance.
- **FR-016**: System MUST define behavior for storage-capacity exhaustion during model pull, including deterministic startup failure classification and operator guidance.

### Key Entities *(include if feature involves data)*

- **Model Startup Configuration**: Deployment-supplied model selection inputs used to determine which model to preload and serve.
- **Model Cache Artifact**: Persisted model files and metadata representing an already downloaded model that can be reused on future startups.
- **Startup Readiness State**: Service lifecycle state transitions that gate traffic until model preload has either succeeded or failed explicitly.
- **Pre-Pull Event Record**: Structured startup event output indicating pull phase, result status, and failure context when applicable.
- **Lifecycle Strategy**: Configurable behavior unit defining startup, steady-state, and teardown handling rules for a deployment.
- **Lifecycle Plugin**: A registered hook implementation bound to a specific lifecycle phase and explicit execution order.
- **Plugin Registry**: Ordered configuration source that defines which lifecycle plugins execute for startup, steady-state, and teardown.

## Success Criteria *(mandatory)*

### Measurable Outcomes

**Success criteria ID note**: Entries with an `A` suffix (for example, `SC-002A`) are measurable refinements of the corresponding base success criterion and are evaluated together with it.

- **SC-001**: In 100% of fresh deployments, the configured model is available before the service reports ready status.
- **SC-002**: First successful inference request after cold deployment completes without an additional model-download wait in at least 95% of startup cycles.
- **SC-002A**: Startup-to-ready latency MUST be measured and reported per startup cycle, and the service MUST demonstrate that first successful inference avoids blocking model download in at least 95% of measured cold-start cycles.
- **SC-003**: Operators can switch startup model selection per environment using configuration only, with zero required source-code edits.
- **SC-004**: Startup failures caused by invalid or inaccessible model configuration are detectable within one startup cycle and include an actionable failure reason.
- **SC-005**: Operators can enable at least one alternate lifecycle strategy (beyond the default) through configuration only, without changing core service code.
- **SC-006**: In at least 95% of restart cycles, cache-preserving teardown enables subsequent startup without requiring full model re-download.
- **SC-007**: In 100% of startup pull failure cases that exceed retry limits, the service exits startup within one retry window and emits a clear failure reason.
- **SC-007A**: In 100% of retry-exhaustion failures, emitted failure payloads include the required actionable error fields defined by `FR-005A`.
- **SC-008**: In 100% of deployments, registered lifecycle plugins execute in the configured deterministic order and emit traceable lifecycle events.
- **SC-008A**: In 100% of validated lifecycle events, required schema fields defined by `FR-006A` are present and non-empty.

## Assumptions

- Deployments have access to persistent storage suitable for retaining downloaded model artifacts across restarts.
- Operators manage model identifiers and access credentials through existing environment configuration practices.
- Startup time increase from pre-pull is acceptable because it is preferred over runtime first-request delays.
- Health/readiness checks are already part of the deployment lifecycle and can reflect preload completion state.
