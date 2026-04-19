# Phase 0 research: Render-aligned Docker build optimization

## 1. Render platform constraints (Docker)

**Decision**: Treat [Render’s Docker on Render](https://render.com/docs/docker) and related docs as
**normative** for this feature.

**Rationale**:

- Production **`vecinita-data-management-api-v1`** uses `runtime: docker` with explicit
  `dockerfilePath` and `dockerContext` in the root blueprint (`render.yaml`).
- Render builds images with **BuildKit**, **caches intermediate layers**, and honors **`.dockerignore`**
  to omit files from the build context—directly addressing large contexts (e.g. accidental `.venv`
  upload).
- Render may pass dashboard **environment variables** into the image as **build `ARG`s**; their docs
  warn **not** to reference `ARG`s that contain **secrets**, or those values can end up in the image.

**Alternatives considered**:

- **Optimize a different Dockerfile** (e.g. under `services/data-management-api/`) — **rejected**
  for production scope: blueprint explicitly builds **`services/scraper`** to avoid nested submodule
  init on Render.
- **Require prebuilt registry images only** — deferred: would change deploy workflow and ownership;
  current requirement is faster **Render-from-Dockerfile** builds.

## 2. Build context and `.dockerignore`

**Decision**: Add a **`services/scraper/.dockerignore`** (or equivalent at context root) listing
artifacts that must never be sent to Render: `.venv/`, `**/__pycache__/`, `.pytest_cache/`,
`.mypy_cache/`, `.hypothesis/`, `tests/` (if not required for `pip install .`), editor/OS junk, and
large dev-only trees. Validate with `docker build` that the image still installs and runs.

**Rationale**: Render documents that omitted paths reduce context size and speed uploads; the
submodule tree currently may include heavy dev artifacts globbed into context.

**Alternatives considered**:

- Rely on developers to clean trees manually — **rejected** (fragile, not reproducible on CI).

## 3. Layer caching and Dockerfile structure

**Decision**: Keep **`python:3.11-slim`** (or pin to immutable digest once chosen in implementation)
and reorder steps so **dependency resolution** invalidates cache **only** when dependency inputs
change—typically `COPY pyproject.toml` (+ lock file if adopted for install) **before** `COPY src/`,
then run install in split steps (`pip install` / `uv sync`) per feasibility in `pyproject.toml`.

**Rationale**: Matches Docker and Render guidance on **order-stable layers** and multi-stage
optionality; maximizes “repeat edit” wins when only `src/` changes.

**Alternatives considered**:

- **Single-stage, only reorder COPY** — acceptable MVP if split install is awkward; still pair with
  `.dockerignore`.
- **`uv` in Docker** using `uv.lock` — **candidate**: faster reproducible installs; must prove
  identical installed dependency set vs current image (FR-006) before adopting.

## 4. Base image tags and registry cache

**Decision**: Prefer **immutable** references for external bases (specific patch tag or digest) per
Render’s warning that **mutable tags** (e.g. `latest`) can resolve to **older cached** public images.

**Rationale**: Avoids “mystery” drift and surprise security/behavior changes while preserving cache
friendliness.

**Alternatives considered**:

- Stay on `python:3.11-slim` floating tag — acceptable short-term but document risk; planning should
  move to pinned digest in implementation tasks if operators agree.

## 5. Secrets and build-time configuration

**Decision**: Do **not** add `ARG` instructions that consume sensitive Render env vars. If build-time
config is needed, use **non-secret** build args only, or secrets mechanisms Render documents (e.g.
secret files), not echoed into layers.

**Rationale**: Render explicitly calls out secret leakage via `ARG`.

## 6. What we are not optimizing in this phase

**Decision**: Out of scope per spec—**runtime** API latency, Postgres tuning, Modal workers, gateway
frontend images, and blueprint redesign—unless a minimal one-line coupling is required and filed
under **FR-007**.

**Rationale**: Keeps validation focused and avoids scope creep.
