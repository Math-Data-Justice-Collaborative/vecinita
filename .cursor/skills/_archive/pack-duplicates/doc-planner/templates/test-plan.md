<!-- TEMPLATE: test-plan.md -->
<!-- Instructions: Replace all [bracketed placeholders] with project-specific content. -->
<!-- Remove this comment block before finalizing. -->

# Test Plan

> **Project**: [Project Name]
> **Repository**: [Repository URL]
> **Last updated**: [Date]

## Scope

**In scope**: [What this test plan covers — e.g., core pipeline validation, API E2E, UI interaction E2E, paper result reproduction]

**Out of scope**: [e.g., performance benchmarking, training from scratch — **do not** list Playwright UI E2E here if the product has frontends]

## User Journeys (E2E)

Product-facing journeys are defined in [user-journeys.md](user-journeys.md) (UJ-001–…).
Map each journey to **API E2E** (`tests/e2e/`), **UI E2E** (`tests/ui/`), and/or **Vitest** as appropriate.

| Journey | Feature | API E2E (`tests/e2e/`) | UI E2E (`tests/ui/`) | Vitest | live E2E | TC |
|---------|---------|------------------------|----------------------|--------|----------|-----|
| UJ-001 | F# | `test_uj001_*.py` | `chat/uj001-*.spec.ts` | `ChatPanel.test.tsx` | [optional] | TC-001 |

For UI journeys, document **component interactions** under test (e.g. sidebar ↔ outlet, tabs ↔ URL query).

## Test Requirements by Change

Map each new or changed feature/contract/behavior to the layer where it is consumed (see
`.cursor/rules/e2e-coverage.mdc` and `.cursor/rules/tdd.mdc`). Every change gets at least one row.

| Change (feature / contract / behavior) | Layer | Test artifact | Status |
|----------------------------------------|-------|---------------|--------|
| [UJ-001 — user-facing backend flow] | API E2E | `tests/e2e/test_uj001_*.py` (TC-001) | planned |
| [UJ-001 — cross-component UI interaction] | UI E2E | `tests/ui/chat/uj001-*.spec.ts` (TC-00N) | planned |
| [ChatPanel hook behavior] | Vitest | `apps/chat-rag-frontend/src/...test.tsx` | planned |
| [POST /jobs — request schema change] | Integration | `tests/integration/test_jobs_contract.py` | planned |
| [normalize() — new behavior] | Unit | `tests/unit/test_normalize.py` (payloads below) | planned |

Rules:

- **API E2E** required for caller-facing backend journeys (`tests/e2e/`).
- **UI E2E (Playwright T0-ui)** required when behavior depends on **browser interaction between
  components** — not covered by isolated Vitest.
- **Vitest** for component/hook logic; not a substitute for Playwright cross-panel flows.
- **Integration test** required whenever a **contract** changes (endpoint, request/response schema,
  or job payload shape).
- **Unit test + payloads** required for new/changed function or module behavior.

### Example payloads (unit / integration)

For each new or changed function/contract, record concrete example payloads so tests can be written
TDD-first in 07-build:

- **Function / endpoint**: [name]
- **Sample input**:

```json
{ "field": "value" }
```

- **Expected output**:

```json
{ "result": "value" }
```

- **Edge / error inputs**: [empty, oversized, malformed, …] → [expected error or behavior]

## Connectivity & wiring (multi-app / UI)

If static frontends call APIs on **different origins**, document tiers per
`.cursor/skills/connectivity-gates.md`:

| Tier | Scope | Command |
|------|-------|---------|
| H0c | CORS policy (in-process) | `pytest tests/unit/test_cors_policy.py` |
| H0i | Cross-service integration | `pytest tests/integration` |
| H4 | Live CORS preflight | `pytest tests/smoke/test_staging_connectivity.py -m live` |
| H5 | Frontend bundle URLs | `scripts/deploy/verify_connectivity.sh` |
| **T0-ui** | **Playwright — component interactions** | `make test-ui` / `bash scripts/ui/run_playwright.sh` |
| **T3-ui** | **Playwright — live staging** | `npm run test:ui:staging` (needs `VECINITA_STAGING_*_FRONTEND_URL`) |

Vitest/component tests and Playwright T0-ui are **not** a substitute for H4–H5.

### UI mock strategy (hybrid)

| Tier | Data source | When |
|------|-------------|------|
| T0-ui | Playwright `page.route` mocks | CI `ui-e2e` job |
| T3-ui | Live staging bundles | Post-deploy / manual |
| Optional | Local Postgres + APIs | Nightly / manual (if adopted) |

## Test Strategy

| Level | Framework | Scope | Run Command | Est. Duration |
|-------|-----------|-------|-------------|---------------|
| Smoke | [framework] | Basic pipeline executes without error | `[command]` | [time] |
| Unit | pytest | Individual functions and modules | `uv run pytest tests/unit` | [time] |
| Integration | pytest | API + DB contracts | `uv run pytest tests/integration` | [time] |
| API E2E | pytest | User journeys (TestClient + DB) | `uv run pytest tests/e2e` | [time] |
| Component | Vitest | Frontend hooks/components | `npm test` per app | [time] |
| **UI E2E** | **Playwright** | **Cross-component browser flows** | **`make test-ui`** | [time] |
| Validation | [framework] | Reproduce paper results | `[command]` | [time] |

## Test Cases

### TC-001: [Smoke Test Name]

- **Objective**: Verify the pipeline runs end-to-end without crashing
- **Preconditions**: [What must be set up first]
- **Input**: [Input files, parameters, or commands]
- **Steps**:
  1. [Step 1]
  2. [Step 2]
- **Expected output**: [What success looks like]
- **Pass criteria**: [Specific measurable condition]
- **Source**: [Paper §X] or [Repo: test file]

### TC-002: [UI interaction test name]

- **Objective**: [Cross-component behavior — e.g. chat survives corpus navigation]
- **Preconditions**: [Playwright build, route mocks]
- **Components**: [e.g. App shell, ChatPanel, Sidebar]
- **Steps**:
  1. [Browser action 1]
  2. [Assert interaction outcome]
- **Pass criteria**: [Observable UI state]
- **Source**: `tests/ui/[path].spec.ts`, UJ-NNN

### TC-003: [Unit Test Name]

- **Objective**: [What this test validates]
- **Preconditions**: [What must be set up first]
- **Input**: [Input files, parameters, or commands]
- **Steps**:
  1. [Step 1]
  2. [Step 2]
- **Expected output**: [What success looks like]
- **Pass criteria**: [Specific measurable condition]
- **Source**: [Paper §X] or [Repo: test file]

## Test Data

| Dataset | Source | Size | Format | How to Obtain |
|---------|--------|------|--------|---------------|
| [name] | [URL or path] | [size] | [format] | [download/generate instructions] |

### Test Fixtures

- Location: `[path to test fixtures in repo]`
- Generation: `[command to generate fixtures if needed]`

## Metrics & Thresholds

| Metric | Threshold | Context | Paper Reference |
|--------|-----------|---------|-----------------|
| [metric] | [value] | [when this applies] | [Paper §X] |
| Frontend branch coverage | ≥95% | Vitest per app | ADR-019 |

## Environment Requirements

| Resource | Minimum | Recommended | Notes |
|----------|---------|-------------|-------|
| GPU | [spec] | [spec] | Required for [which tests] |
| RAM | [spec] | [spec] | |
| Disk | [spec] | [spec] | For test data storage |
| Node | 24 LTS | 24 LTS | Frontends + Playwright |

## CI Integration

- **CI system**: [GitHub Actions / GitLab CI / etc.]
- **Test jobs**: `python`, `frontend` matrix, **`ui-e2e`**, `coverage`
- **Reproduce CI locally**: `make ci` / `make test-ui`

## Known Gaps

- [ ] ⚠️ [Gap 1 — what's missing and why]
- [ ] ⚠️ [Gap 2 — what's missing and why]
