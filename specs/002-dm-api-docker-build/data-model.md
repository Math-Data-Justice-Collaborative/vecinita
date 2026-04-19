# Data model: packaging baselines and measurement

This feature does not introduce new application database entities. It adds **records** teams maintain
for evidence and regression detection.

## Entity: PackagingBaseline

| Field | Type (logical) | Required | Notes |
|-------|----------------|----------|--------|
| `id` | string | yes | Short label, e.g. `pre-opt-2026-04-18` |
| `scenario` | enum | yes | `repeat_edit` \| `cold` \| `ci_source_only` |
| `median_seconds` | number | yes | Aggregate agreed in methodology |
| `sample_count` | integer | yes | ≥1; prefer ≥3 for medians |
| `profile` | string | yes | References **MeasurementProfile.id** |
| `git_revision` | string | yes | Commit SHA of tree measured |
| `notes` | string | no | Anomalies, network retries excluded, etc. |

**Validation**: `median_seconds` > 0; `sample_count` ≥ 1; scenario-specific inputs documented in
**FR-008** appendix.

## Entity: DataManagementApiV1Deliverable

| Field | Type (logical) | Required | Notes |
|-------|----------------|----------|--------|
| `image_identity` | string | yes | Logical name: production scraper API image for DM V1 |
| `build_context_path` | string | yes | Repo-relative: `services/scraper` (per Render blueprint) |
| `dockerfile_path` | string | yes | Repo-relative: `services/scraper/Dockerfile` |
| `entrypoint` | string | yes | Unchanged server factory / port contract vs baseline |

**Validation**: Paths must match [render.yaml](../../render.yaml) for `vecinita-data-management-api-v1` unless an approved blueprint change updates them jointly.

## Entity: MeasurementProfile

| Field | Type (logical) | Required | Notes |
|-------|----------------|----------|--------|
| `id` | string | yes | e.g. `dev-m4-local`, `gh-ubuntu-latest-4cpu` |
| `cpu_class` | string | yes | Human-readable |
| `docker_version` | string | no | Helpful for local runs |
| `cache_policy` | string | yes | e.g. `warm_layers`, `no_cache` for cold |
| `network` | string | no | `office`, `ci`, etc. |

**Validation**: Same **profile.id** must be used when comparing before/after numbers for a given
scenario.

## Relationships

- Many **PackagingBaseline** rows reference one **MeasurementProfile** by `profile`.
- **DataManagementApiV1Deliverable** is the constant subject of baseline rows for this feature.
