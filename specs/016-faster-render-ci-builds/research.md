# Research: Faster Render builds and GitHub Actions CI

## 1. GitHub Actions: dependency and tool caches

**Decision**: Use **actions/cache** (or built-in **setup-node** `cache`, **setup-uv** cache options where available) keyed on **lockfiles** (`uv.lock`, `package-lock.json`, `backend/uv.lock` if split) and a **stable cache id** per runner OS.

**Rationale**: Runners start clean; restoring wheels and npm modules avoids repeated network-bound install steps, often the largest slice of `backend-quality` / `frontend-quality` jobs.

**Alternatives considered**:

- **No caching** — simplest but leaves minutes on the table vs spec **SC-001**.
- **Single monolithic cache key on `main` only** — risks stale deps; rejected unless combined with **fail-fast** regen job on lockfile change.

## 2. Path filters (`paths` / `paths-ignore`) on workflows or jobs

**Decision**: Introduce **path-based conditional jobs** (or `dorny/paths-filter`-style steps) only where **FR-006** can be satisfied: log output lists the filter decision; **full run** still occurs on `main`/`develop` or when lockfiles / shared contracts change.

**Rationale**: Matches spec user story on skipping redundant work for docs-only changes while avoiding false negatives on cross-cutting edits.

**Alternatives considered**:

- **Per-PR manual labels** — higher friction; defer.
- **Skip backend when only `frontend/` changes** — risky if shared `packages/` or OpenAPI snapshots change; any filter must include **`packages/`**, **`scripts/`**, **`render.yaml`**, **`.github/workflows/`** as “wide” triggers.

## 3. Parallelism vs serialized `make test-schemathesis`

**Decision**: In **CI**, prefer **separate jobs** (or parallel steps) for **gateway**, **agent**, and **data-management** Schemathesis+TraceCov suites instead of one long sequential shell chain, **if** total wall-clock for the workflow stage dominates contributor wait time. Locally, **`Makefile`** may keep sequential `test-schemathesis` for single-machine tracecov HTML output unless we add a **`test-schemathesis-parallel`** target documented in **TESTING_DOCUMENTATION.md**.

**Rationale**: Today `test-schemathesis` runs three pytest invocations **serially**; each loads hooks and TraceCov. Parallel jobs use **3×** runners but **~1×** calendar time for that stage. Spec allows time reduction without removing checks.

**Alternatives considered**:

- **Lower `--tracecov-fail-under`** — **rejected**: violates **FR-007** / constitution on contract rigor.
- **Disable TraceCov on PR, nightly only** — **conditional accept**: only if **FR-004**-style written approval and **equivalent** signal (e.g. nightly still enforces 100% on `main`); default plan keeps PR parity unless metrics prove nightly-only is safe.

## 4. Render Docker builds: layer order and context

**Decision**: Align **`backend/Dockerfile`** (and any service Dockerfile) with **deps-before-sources** copy order; keep **`.dockerignore`** aggressive to shrink context; document in [contracts/render-docker-build-layers.md](./contracts/render-docker-build-layers.md).

**Rationale**: Render rebuilds images on deploy; better layer cache reuse speeds **code-only** deploys (**FR-003**, **SC-002**).

**Alternatives considered**:

- **Pre-built images in a registry** — larger process change; defer beyond this plan unless tasks expand scope.
- **Smaller base image** — evaluate in tasks; security and glibc compatibility must be checked.

## 5. Submodule and clone depth

**Decision**: Keep **`fetch-depth`** and **`git submodule update --init --depth 1`** patterns; audit for **duplicate** submodule checkouts across jobs in the same workflow (merge steps or reuse artifacts if safe).

**Rationale**: Clone time is visible on every run; depth-1 already used in places — extend consistently where full history is not required.

**Alternatives considered**:

- **`fetch-depth: 0` everywhere** — needed only for release/changelog jobs; narrow scope.

## 6. Baseline methodology

**Decision**: Use **GitHub Actions run history** (median over **N** runs, **N ≥ 20** where possible) and **Render deploy/build timestamps** for the same calendar window; segment by **change category** (see [data-model.md](./data-model.md)).

**Rationale**: Satisfies **FR-001** and makes **SC-001**–**SC-003** verifiable.

**Alternatives considered**:

- **Developer laptop timings only** — insufficient for Render; use as supplementary only.
