# Data Model: Startup Lifecycle and Connection Reliability

## Entity: ModelStartupConfiguration

- **Description**: Deployment-level configuration for startup preload and lifecycle behavior.
- **Fields**:
  - `default_model_id` (string, required): canonical model identifier from supported registry.
  - `models_path` (string, required): mount path for model artifacts.
  - `retry_limit` (integer, required): bounded number of startup retry attempts.
  - `retry_backoff_ms` (integer, required): delay between retry attempts.
  - `lifecycle_registry_id` (string, required): references active plugin registry definition.
- **Validation rules**:
  - `default_model_id` must map to a supported model entry.
  - `retry_limit` must be >= 1.
  - `retry_backoff_ms` must be > 0.

## Entity: LifecyclePlugin

- **Description**: A registered lifecycle hook implementation.
- **Fields**:
  - `plugin_id` (string, required, unique): stable plugin name.
  - `phase` (enum, required): `startup | steady_state | teardown`.
  - `order` (integer, required): deterministic execution position in phase.
  - `required` (boolean, required): startup must fail if required plugin is invalid or missing.
  - `enabled` (boolean, required): toggles plugin execution.
- **Validation rules**:
  - `order` must be unique within each `phase`.
  - `required=true` plugins must be resolvable at startup.

## Entity: PluginRegistry

- **Description**: Ordered set of lifecycle plugins for a deployment.
- **Fields**:
  - `registry_id` (string, required, unique)
  - `version` (string, required)
  - `plugins` (list of LifecyclePlugin, required)
- **Relationships**:
  - One `PluginRegistry` contains many `LifecyclePlugin` entries.
  - `ModelStartupConfiguration.lifecycle_registry_id` references `PluginRegistry.registry_id`.

## Entity: PullAttempt

- **Description**: Records one model preload attempt during startup.
- **Fields**:
  - `attempt_number` (integer, required)
  - `model_ollama_name` (string, required)
  - `started_at` (timestamp, required)
  - `ended_at` (timestamp, optional)
  - `outcome` (enum, required): `success | transient_failure | permanent_failure`
  - `failure_reason` (string, optional)
- **Validation rules**:
  - `attempt_number` must be <= configured `retry_limit`.

## Entity: CacheArtifactState

- **Description**: State of reusable model artifacts in persistent volume.
- **Fields**:
  - `model_ollama_name` (string, required)
  - `is_present` (boolean, required)
  - `integrity_status` (enum, required): `unknown | valid | invalid | partial`
  - `last_verified_at` (timestamp, optional)
- **Lifecycle notes**:
  - Warm startup path uses `is_present=true` + `integrity_status=valid`.
  - Teardown keeps `valid` artifacts and cleans temporary runtime files.

## Entity: LifecycleEventRecord

- **Description**: Structured observability event for lifecycle execution.
- **Fields**:
  - `event_type` (enum, required): `preload_start | preload_success | preload_failure | retry | teardown_start | teardown_success | teardown_failure | plugin_validation_failure`
  - `phase` (enum, required): `startup | steady_state | teardown`
  - `plugin_id` (string, optional)
  - `correlation_id` (string, required)
  - `timestamp` (timestamp, required)
  - `details` (object, optional)

## State Machine: StartupReadinessState

- **States**:
  - `initializing`
  - `preloading`
  - `ready`
  - `failed_startup`
  - `shutting_down`
- **Transitions**:
  - `initializing -> preloading` when startup lifecycle begins.
  - `preloading -> ready` when preload and required startup plugins succeed.
  - `preloading -> failed_startup` when retry limit exceeded or required plugin validation fails.
  - `ready -> shutting_down` when container stop event starts teardown.
