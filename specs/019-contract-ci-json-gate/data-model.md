# Data model: CI attestation & manifest (019-contract-ci-json-gate)

## Entity: RequiredCheck (manifest entry)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | Stable slug (`^[a-z0-9][a-z0-9-]*$`); used in attestation `checks`. |
| `title` | string | yes | Human-readable name (FR-001). |
| `description` | string | no | Contributor-facing hint. |
| `command` | string | yes | Shell command run from repo root by generator (e.g. `make ci`). |

**Validation rules**

- `id` values MUST be unique within the manifest.
- Ordering MAY be significant for documentation only; validator treats manifest as a set of ids.

## Entity: RequiredChecksManifest (file)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `manifest_version` | integer | yes | Starts at `1`. |
| `checks` | array of RequiredCheck | yes | Non-empty. |

**Relationships**

- One manifest file per repository revision (committed `.ci/required-checks.json`).
- Defines the authoritative set **S** of ids that must appear in a valid attestation (each `id` exactly once in `checks`; duplicates fail validation per spec FR-007).

## Entity: CheckOutcome (attestation entry)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | yes | References `RequiredCheck.id`. |
| `title` | string | v2 yes | Human-readable check title copied from manifest. |
| `command` | string | v2 yes | Executed shell command from manifest. |
| `status` | string | yes | `passed` or `failed` (extensible enum later). |
| `exit_code` | integer | v2 yes | Process exit code for the command run. |
| `started_at` | string | v2 yes | ISO-8601 UTC start time for this check run. |
| `finished_at` | string | no | ISO-8601 UTC end time for this check (optional in v1 if only top-level `generated_at` is used). |
| `duration_seconds` | number | v2 yes | Elapsed wall-clock runtime for this check. |
| `stdout` | string | v2 yes | Captured stdout for this check command. |
| `stderr` | string | v2 yes | Captured stderr for this check command. |

## Entity: CiAttestation (file)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `format_version` | integer | yes | Attestation format version (FR-003); `1` (minimal) or `2` (detailed outputs). |
| `run_id` | string | yes | Unique run identifier (UUID v4 per research). |
| `generated_at` | string | yes | ISO-8601 UTC when attestation was finalized (FR-002, FR-006). |
| `git_head` | string | no | Abbreviated commit SHA for correlation. |
| `checks` | array of CheckOutcome | yes | Must include exactly the manifest ids, each `passed` for merge; v2 includes per-check execution output details. |

**State / transitions**

1. **Absent** → validator fails (FR-005).
2. **Present + invalid schema** → fail.
3. **Present + valid + stale** → fail (FR-006).
4. **Present + valid + fresh + all passed** → success (FR-007–FR-008).
5. **Present + valid + fresh + any failed/missing** → fail.

**Integrity**

- Optional later: `manifest_sha256` or embedded manifest version to detect drift between attestation generation and validation time; out of scope for v1 unless tasks add it.
