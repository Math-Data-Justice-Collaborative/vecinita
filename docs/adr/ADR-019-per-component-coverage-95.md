# ADR-019: Per-component unit coverage gate — 95% line and branch

**Status:** Accepted  
**Date:** 2026-06-13  
**Cycle:** EV-004  
**Deciders:** Product (01-requirements delta interview)

## Context

Vecinita v1 specified a **≥80% line coverage** target on selected packages and backends (`docs/test-plan.md`). CI did not enforce a numeric gate; `scripts/test/print_unit_coverage_summary.py` reports per-component totals but does not fail builds.

As of 2026-06-13 (`make test-unit-coverage` on `fix/es-en-full-ui`):

| Tier | Combined line | Combined branch |
|------|---------------|-----------------|
| All 12 components | **61.0%** | **~42.9%** |

Several components are far below any 95% target (e.g. `apps/internal-write-api` 40.8% lines / 13.2% branches; `apps/data-management-backend` 41.5% / 1.5%).

The monorepo groups coverage by **`packages/<name>`** and **`apps/<name>`** — twelve components total (six packages, four Python apps, two TypeScript frontends).

## Decision

Adopt **F31 — per-component unit coverage gate**:

1. **Granularity:** One gate per component (`packages/*`, `apps/*`) — twelve gates.
2. **Metrics:** **Line coverage ≥ 95%** and **branch coverage ≥ 95%** for each component.
3. **Test scope:** **Unit tests only** — Python `tests/unit` (pytest-cov) and frontend Vitest `--coverage`.
4. **Enforcement:** **Blocking in CI** — any component below either threshold fails the pipeline.
5. **Phasing:** **Single milestone** — all twelve components must pass before merge (no grandfathering, no incremental per-component rollout in v1 of this gate).
6. **Exclusions:** Keep existing omit/include rules:
   - Python (`pyproject.toml` `[tool.coverage.run]`): omit `*/tests/*`, `*/__init__.py`, `apps/database/alembic/*`.
   - TypeScript (Vitest): include `src/**/*.{ts,tsx}`; exclude `src/**/*.test.*`, `src/test/**`.
7. **Modal:** `apps/data-management-backend` gate includes Modal worker entrypoints and job modules (not split out).
8. **Frontends:** Same 95% line + branch gate as backends (no reduced frontend threshold).

**Supersedes** the v1 **≥80% line** coverage statement in `docs/test-plan.md` and `docs/acceptance-criteria.md` for unit-test scope.

### Gated components

| Component | Baseline line (2026-06-13) | Baseline branch |
|-----------|---------------------------|-----------------|
| `packages/rag` | 73.2% | 50.0% |
| `packages/ingest` | 71.4% | 55.0% |
| `packages/embedding-client` | 84.8% | 64.3% |
| `packages/llm-client` | 87.0% | 66.7% |
| `packages/tagging` | 57.7% | 16.7% |
| `packages/shared-schemas` | 88.9% | 52.2% |
| `apps/chat-rag-backend` | 42.8% | 13.0% |
| `apps/data-management-backend` | 41.5% | 1.5% |
| `apps/internal-write-api` | 40.8% | 13.2% |
| `apps/database` | 63.8% | 53.2% |
| `apps/chat-rag-frontend` | 80.2% | 66.8% |
| `apps/data-management-frontend` | 59.3% | 47.4% |

### Implementation hooks (04-tech-plan / 07-build)

**Resolved (EV-004 04-tech-plan 2026-06-13):**

- **TP-030:** Extend `scripts/test/print_unit_coverage_summary.py` with **`--enforce`** — exit non-zero when any component is below 95% line or branch; `scripts/test/unit_coverage.sh` passes `--enforce` by default.
- **TP-031:** Add dedicated **`coverage`** job to `.github/workflows/ci.yml` (uv + Node 24; runs `make test-unit-coverage` after lint jobs or in parallel with full pytest).
- Add Vitest `coverage.thresholds` (lines + branches **95**) per frontend app, aligned with the same target.
- Repo-wide pytest `[tool.coverage.report] fail_under` is **not** used; per-component aggregation in the summary script is the single source of truth.

**Build tasks:** Phase 9 in `docs/execution-plan.md` (T32.1–T36.4).

## Consequences

- **Positive:** Uniform quality bar; regressions caught per app/package; summary script becomes the single source of truth for the gate.
- **Negative:** Large test-writing effort (~39 pp line gap, ~52 pp branch gap on combined totals); branch coverage especially requires conditional-path tests in backends and admin UI.
- **Out of scope:** Integration/e2e coverage, `scripts/`, `infra/`, Cursor skills, generated OpenAPI clients.

## Compliance

Local parity:

```bash
make test-unit-coverage   # must exit 0 when gate is implemented
```

CI: dedicated **`coverage`** job runs `make test-unit-coverage` (summary script with `--enforce` per TP-031).

## Related

- F31 in `docs/feature-list.md`
- RD-053–RD-060 in `docs/decisions.md#requirements-decisions-01-requirements`
- ADR-018 (typing gate — complementary, not a substitute for coverage)
- `scripts/test/unit_coverage.sh`, `scripts/test/print_unit_coverage_summary.py`
