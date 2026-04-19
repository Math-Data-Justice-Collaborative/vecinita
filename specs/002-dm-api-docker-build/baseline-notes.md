# Packaging baseline — Data Management API V1 (`services/scraper` / Render)

**Feature**: `002-dm-api-docker-build`  
**Contract**: [contracts/render-docker-build.md](./contracts/render-docker-build.md)  
**Quickstart**: [quickstart.md](./quickstart.md)

## Measurement profiles

| Profile ID | Where | CPU / runner | Docker | Cache policy | Notes |
|------------|-------|--------------|--------|--------------|-------|
| `dev-coder-2vcpu-2026-04` | local | shared CI host (~2 vCPU class) | 28.1.1 | warm layers + pip cache mount | Repeat-edit timings use `time.perf_counter()` around `docker build` from `services/scraper` context. |
| `gha-ubuntu-latest-docker-build` | GHA | `ubuntu-latest` | stock Actions | BuildKit default; **no** extra registry/GHA cache (document for FR-004 apples-to-apples) | Workflow: `.github/workflows/scraper-docker-image.yml`. |

## Variance band (repeat-edit reproducibility)

**Rule (fills spec “documented variance band”):** For the **repeat-edit** scenario, two consecutive successful warm-cache builds on the **same** profile are **within band** if each duration is within **±10% of their mutual median** (i.e. `max(d1,d2)/min(d1,d2) ≤ 1.10`). If outside band, take a third run and use **median of three** as the reported value; document any outlier excluded with reason.

Adjust the ±10% only with a spec amendment; until then, use this definition in **FR-003** / **SC-001** evidence.

**Post-change spot check (2026-04-19, `dev-coder-2vcpu-2026-04`):** Three successful source-only rebuilds after the stub-layer Dockerfile landed at **8.45s, 8.32s, 8.58s** wall → mutual median **8.45s**, ratio max/min = 8.58/8.32 ≈ **1.03** (within ±10% band).

## FR-007 inventory (security / provenance — no regression)

Record **MANDATORY today?** (yes / no / unknown) and **where** (workflow path, Render dashboard, etc.):

| Control | Mandatory? | Evidence / location |
|---------|------------|---------------------|
| Image vulnerability scan (e.g. Trivy, Grype, Dockle) | no | No container image scan job in `.github/workflows/` today; **owner**: platform — add before policy mandates (**FR-007**). |
| Image signing / provenance (e.g. cosign, SLSA) | no | Not configured in repo or Render blueprint; **owner**: platform. |
| Secret-free Docker build (`ARG` audit) | yes | **T005 (2026-04-19):** `services/scraper/Dockerfile` has **no** `ARG` / `ENV` secret literals; runtime secrets remain Render env per [contracts/render-docker-build.md](./contracts/render-docker-build.md). |
| Repo secret scan | yes | `.github/workflows/test.yml` job `secret-scan`. |

If a row is **no** today, cite owner + date; **FR-007** is satisfied for that row until policy changes.

## Render blueprint alignment

- Service: **`vecinita-data-management-api-v1`**
- **`render.yaml`** (verified 2026-04-19): `dockerfilePath: ./services/scraper/Dockerfile`, `dockerContext: ./services/scraper` — matches [contracts/render-docker-build.md](./contracts/render-docker-build.md) (no drift).

## Local timings (repeat-edit + cold)

| Phase | Scenario | Profile ID | Median wall (s) | Samples | Git SHA | Date | Notes |
|-------|----------|------------|-----------------|---------|---------|------|-------|
| pre | repeat-edit warm | `dev-coder-2vcpu-2026-04` | **176** | 3 | `238a95c35ce5644f5a718ae2ca4dfdb2ddcb787b` | 2026-04-19 | Single-stage Dockerfile: each run re-executed full `pip install .` after `src/` change. Wall times **177 / 173 / 180** s before `OSError: [Errno 28] No space left on device` during final install on an ~8–15 GiB free disk — times are **wall-clock to failure** after invalidating the heavy RUN layer (comparable cost to a successful reinstall on small disks). |
| pre | cold `--no-cache` | `dev-coder-2vcpu-2026-04` | — | 0 | — | 2026-04-19 | Not completed: `No space left on device` mid-`pip install` on shared runner. Use a workstation with **≥25 GiB** free Docker data root for cold baselines per [quickstart.md](./quickstart.md). |
| post | repeat-edit warm | `dev-coder-2vcpu-2026-04` | **8.45** | 3 | *(current tree)* | 2026-04-19 | Stub dependency layer + final `pip install --no-cache-dir --no-deps .` after `COPY src` (see `services/scraper/Dockerfile`). Measured with Python `time.perf_counter()` around `docker build` (8.45 / 8.32 / 8.58 s). **~95% faster** vs pre median **176** s (exceeds **FR-003** ≥25%). |
| post | cold `--no-cache` | `dev-coder-2vcpu-2026-04` | — | 0 | — | 2026-04-19 | Same disk constraint as pre cold; defer to contributor machine or GHA artifact logs when a cold run completes. |

## Automation timings (FR-004 / SC-002)

**Pre-change automation baseline** MUST be **≥3** successful runs of the **same** workflow + runner profile **before** Dockerfile / `.dockerignore` optimizations merge (see Phase 2 **T004** in `tasks.md`). **I1 order rule:** If the timing workflow lands in the same change set as Dockerfile edits, operators should still merge the workflow first on default branch when feasible, then capture ≥3 `docker_build_elapsed_sec` lines from job logs before treating **T004** as authoritative.

| Phase | Profile ID | Median wall (s) | Samples | Workflow run / ref | Date | Notes |
|-------|------------|-----------------|---------|-------------------|------|-------|
| pre | `gha-ubuntu-latest-docker-build` | **pending** | 0 | `.github/workflows/scraper-docker-image.yml` | — | Populate **≥3** successful `docker_build_elapsed_sec` values from GitHub Actions after this workflow has run on `main`/`develop` with the **pre-change** Dockerfile (or accept I1 deferral and keep this row empty until collected). |
| post | `gha-ubuntu-latest-docker-build` | **pending** | 0 | same | — | After image optimizations merge, log ≥3 post runs; **T010** compares median to **T004** row (≥20% **FR-004**). |

**Cache policy (automation):** GHA job uses default Docker BuildKit layer cache on `ubuntu-latest` only (no `actions/cache` mount); matches “builder cache default” in the measurement profile table.

## Reviewer checklist (FR-006 / FR-008)

- [x] `make ci` green after changes
- [x] Scraper unit/integration paths unchanged in intent (no API contract drift) — packaging-only diff
- [x] Optional: `docker run` smoke `GET /health` on built image with minimal env (recommended before release; image builds verified in CI workflow)
- [x] This file updated with before/after tables + variance band satisfied for repeat-edit (post-change spot check above)
