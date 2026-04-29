# Baseline (pre-optimization) — governance artifact (016)

**Feature**: [../spec.md](../spec.md)  
**FR-001**: All numeric medians below are **provisional** until each row has **N ≥ 20** successful samples in a fixed window (extend window or record lead-approved minimum N).  
**Branch protection**: If repository **required** checks are a **strict subset** of `.github/workflows/test.yml` jobs, attach an export or dashboard link here and list exclusions.

---

## (A) Job-level inventory — `.github/workflows/test.yml`

One row per **`jobs:`** id. Fill `median_sec`, `n_runs`, and `cache_state` from GitHub Actions history; keep `provisional=yes` until **FR-001** sample counts are met.

| job_id | median_sec | n_runs | cache_state | provisional | source | change_category_notes (optional) |
|--------|------------|--------|-------------|---------------|--------|----------------------------------|
| workflow-context | — | — | unknown | yes | github_actions | typically `infrastructure_or_workflow` |
| secret-scan | — | — | unknown | yes | github_actions | `infrastructure_or_workflow` / security |
| backend-quality | — | — | unknown | yes | github_actions | `dependency_or_lockfile` when lock-driven |
| frontend-quality | — | — | unknown | yes | github_actions | |
| data-management-api-structure | — | — | unknown | yes | github_actions | |
| data-management-frontend-quality | — | — | unknown | yes | github_actions | |
| data-management-frontend-ci | — | — | unknown | yes | github_actions | |
| embedding-modal-quality | — | — | unknown | yes | github_actions | |
| embedding-modal-ci | — | — | unknown | yes | github_actions | |
| model-modal-quality | — | — | unknown | yes | github_actions | |
| model-modal-ci | — | — | unknown | yes | github_actions | |
| scraper-quality | — | — | unknown | yes | github_actions | |
| scraper-ci | — | — | unknown | yes | github_actions | |
| backend-ci | — | — | unknown | yes | github_actions | |
| backend-integration | — | — | unknown | yes | github_actions | |
| backend-schema-gateway | — | — | unknown | yes | github_actions | Schemathesis gateway + DM `dm_openapi_diff` (**SC-002**) |
| backend-schema-agent | — | — | unknown | yes | github_actions | Schemathesis agent |
| backend-schema-data-management | — | — | unknown | yes | github_actions | Schemathesis data-management (live spec; skips without secrets) |
| frontend-unit | — | — | unknown | yes | github_actions | |
| backend-integration-pgvector | — | — | unknown | yes | github_actions | |

**Rollup hint**: Map jobs to [spec Definitions](../spec.md) **Canonical change categories** when reporting **(B)**; use **strictest** category that applies to the PR.

---

## (B) Category rollup — paired (a) / (b) per FR-001

**Metric (a)**: wall-clock until **all required** CI checks **passed** for the sampled ref.  
**Metric (b)**: Render **build-phase** only (per Definitions — excludes queue, traffic switch, post-deploy health stabilization), **where applicable**.

| change_category | metric | phase_label | median_sec | n_runs | cache_state | provisional | source |
|-----------------|--------|-------------|------------|--------|-------------|---------------|--------|
| documentation_only | (a) | `ci_total` | — | — | unknown | yes | github_actions |
| documentation_only | (b) | *omitted* | — | — | — | yes | *N/A — no Render build required for docs-only baseline per FR-001* |
| application_code_typical | (a) | `ci_total` | — | — | unknown | yes | github_actions |
| application_code_typical | (b) | `render_build_vecinita-agent` | — | — | unknown | yes | render_dashboard |
| dependency_or_lockfile | (a) | `ci_total` | — | — | unknown | yes | github_actions |
| dependency_or_lockfile | (b) | `render_build_vecinita-agent` | — | — | unknown | yes | render_dashboard |
| container_image_or_base | (a) | `ci_total` | — | — | unknown | yes | github_actions |
| container_image_or_base | (b) | `render_build_vecinita-agent` | — | — | unknown | yes | render_dashboard |
| infrastructure_or_workflow | (a) | `ci_total` | — | — | unknown | yes | github_actions |
| infrastructure_or_workflow | (b) | `render_build_vecinita-agent` | — | — | unknown | yes | render_dashboard |
| full_span | (a) | `ci_total` | — | — | unknown | yes | github_actions |
| full_span | (b) | `render_build_vecinita-agent` | — | — | unknown | yes | render_dashboard |

---

## Render — services using `backend/Dockerfile` (T005)

Per root **`render.yaml`**, only **`vecinita-agent`** uses **`dockerfilePath: ./backend/Dockerfile`** with **`dockerContext: ./backend`**.

| service_name | dockerfilePath | dockerContext | build_phase_median_sec | n_runs | cache_state | provisional | sampled_utc_window | notes |
|--------------|----------------|---------------|-------------------------|--------|-------------|---------------|----------------------|-------|
| vecinita-agent | ./backend/Dockerfile | ./backend | — | — | unknown | yes | *TBD* | code-only deploy samples per [quickstart §2](../quickstart.md); link Render **Events** or export |

---

## Path filters (T010)

**T010 N/A** — `.github/workflows/test.yml` does not yet use `paths` / `paths-ignore` or `dorny/paths-filter` (record updated when **T010** ships).

---

## T014 — `dockerContext` / `dockerfilePath` review (US2)

| Source | Service / image | dockerfilePath | dockerContext | Notes |
|--------|-----------------|----------------|-----------------|-------|
| Root `render.yaml` | vecinita-agent | `./backend/Dockerfile` | `./backend` | Minimal; matches Dockerfile location. |
| Root `render.yaml` | vecinita-gateway | `./backend/Dockerfile.gateway` | `./backend` | Same context as agent; no shrink without splitting images. |
| Root `render.yaml` | vecinita-frontend | `./frontend/Dockerfile` | `./frontend` | Minimal. |
| Root `render.yaml` | vecinita-data-management-frontend-v1 | `./apps/data-management-frontend/Dockerfile` | `./apps/data-management-frontend` | Minimal. |
| Root `render.yaml` | vecinita-data-management-api-v1 | `./services/scraper/Dockerfile` | `./services/scraper` | Minimal. |
| `apps/data-management-frontend/render.yaml` | vecinita-data-management-frontend-v1 | `./apps/frontend/Dockerfile` | `./apps/frontend` | **Inconsistent** with repo tree (`apps/frontend/` absent; DM UI lives under `apps/data-management-frontend/`). **No path change in US2** — update this blueprint deliberately in a follow-up if it is still used. |

**Conclusion:** No `dockerContext` shrink in US2 beyond **`backend/.dockerignore`** reducing bytes sent for `./backend` builds.

---

## T015 — After-US2 Render build-phase samples (provisional)

Fill after warm/cold deploys on **`vecinita-agent`** (same columns as the **Render — services using `backend/Dockerfile` (T005)** table above). Label rows **after-US2** when comparing to pre-optimization baselines.

| service_name | build_phase_median_sec (warm) | build_phase_median_sec (cold) | n_runs | cache_state | provisional | sampled_utc_window | notes |
|--------------|------------------------------|-------------------------------|--------|-------------|---------------|---------------------|-------|
| vecinita-agent | — | — | — | warm / cold | yes | *TBD post-deploy* | Re-measure after **T012**/**T013** ship; compare to §T005 table. |
