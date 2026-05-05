# Data model: CI and Render timing optimization

Conceptual entities for baselines, segmentation, and auditable skips. Not a database schema.

## BaselineWindow

| Field | Description |
|--------|-------------|
| `id` | Stable label (e.g. `baseline-2026-04`). |
| `start_utc` / `end_utc` | Inclusive window for sampling. |
| `source` | e.g. `github_actions`, `render_dashboard`, `manual_export`. |
| `sampling_rule` | e.g. median of successful runs on `main` + PRs to `develop`. |

**Validation**: Window MUST be fixed before “after” comparisons (**FR-001**). If **N < 20** successful samples, label **provisional** per [spec.md](./spec.md) **FR-001**.

## ChangeCategory

Normative labels match [spec.md](./spec.md) **Definitions** (**Canonical change categories**). Use this table to map PRs to a single primary category (strictest applicable):

| Spec label | Typical path signals |
|------------|----------------------|
| `documentation_only` | Docs-only paths; no lockfiles, Docker, or runtime source |
| `application_code_typical` | App/service source edits; default **primary** unless another label wins frequency |
| `dependency_or_lockfile` | `uv.lock`, `package-lock.json`, `pyproject.toml`, `package.json`, etc. |
| `container_image_or_base` | `Dockerfile`, base image references, image digest bumps |
| `infrastructure_or_workflow` | `.github/workflows/`, `render.yaml`, `Makefile` CI targets |
| `full_span` | Ambiguous or multi-area; use for conservative baselines |

Legacy aliases (for existing spreadsheets only): `docs_only` → `documentation_only`; `backend_code` / `frontend_only` / `contracts_shared` → fold into **`application_code_typical`** or **`full_span`** per engineering-lead mapping recorded in the governance artifact.

**Relationships**: Each **TimingSample** carries one primary `ChangeCategory` (the strictest applicable).

## GovernanceArtifact

| Field | Description |
|--------|-------------|
| `path_or_url` | Directory under `specs/016-faster-render-ci-builds/artifacts/` plus linked files, or approved wiki URL referenced there (**spec** Definitions). |
| `contents` | Baselines, **FR-004** rows, absolute caps (**FR-003**), `post-optimization-snapshot.md`, `fr008-regression-playbook.md`, and other **FR-008** evidence. |

## TimingSample

| Field | Description |
|--------|-------------|
| `run_id` | CI run id or Render deploy id. |
| `duration_sec` | Wall-clock for the measured phase (full workflow, single job, or Render build phase). |
| `phase` | e.g. `ci_total`, `backend_quality`, `schemathesis_gateway`, `render_build`. |
| `change_category` | `ChangeCategory` |
| `cache_state` | `warm` \| `cold` \| `unknown` (per spec edge cases). |
| `outcome` | `success` \| `failure` (exclude failures from median unless analyzing flakes). |

## JobSkipDecision

| Field | Description |
|--------|-------------|
| `job_name` | Workflow job id. |
| `skipped` | Boolean. |
| `reason` | Human-readable: path filter rule id, `manual_dispatch`, `lockfile_changed`, etc. |
| `rule_ref` | Pointer into [contracts/ci-path-triggers.md](./contracts/ci-path-triggers.md). |

**Validation**: Every `skipped: true` MUST be recoverable from logs or workflow YAML (**FR-006**).

## EquivalenceRecord (FR-004)

| Field | Description |
|--------|-------------|
| `baseline_check_id` | Stable name of required check or behavior being replaced or waived. |
| `replacement_summary` | What runs instead (e.g. parallel job, cached step). |
| `same_intent_note` | How defect/security classes remain covered (**spec** Definitions). |
| `approver` | Named person or role. |
| `approval_date` | ISO date. |
| `rationale` | Why the change is acceptable. |

No row → no waiver.
