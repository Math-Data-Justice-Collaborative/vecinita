# ADR-034: EV-008 interactive eval dashboard — charts, pivot explore, extensible criteria

**Status:** Accepted  
**Stage:** 04-tech-plan (S007, EV-008 — in-place delta R68)  
**Date:** 2026-07-01  
**Feature:** F36 (extended) — Admin RAG evaluation dashboard  
**Issue:** [#99](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/99)  
**Builds on:** [ADR-033](ADR-033-ev008-rag-evaluation-implementation.md), RD-114–RD-122, UJ-041–UJ-043

## Context

M59–M63 delivered the baseline **Evaluation** tab: run trigger, aggregate summary cards, run
history, and per-question drill-down. Operators need **trend visualization**, **pivot-style
exploration**, and **extensible criteria** to spot regressions and customize views — all within the
same S007 / Phase 14 session (R68), not a new feature or evolve cycle.

01-requirements delta locked product decisions RD-114–RD-122 and API shapes in `api-contract.md`
§EV-008 dashboard routes. This ADR records engineering decisions for M64 build (T64.1–T64.10).

## Decision

### 1. UI layout — three views on `/evaluation` (TP-S007-17, RD-115)

Extend `EvaluationPage` with tabbed sub-views (no new top-level route):

| View | Purpose | Journey |
|------|---------|---------|
| **Run / History** | Existing UJ-039/040 flow | Unchanged |
| **Dashboard** | Time-series charts, collapsible panels | UJ-041 |
| **Explore** | Pivot-style aggregation table | UJ-042 |
| **Criteria** | Built-in + custom criteria CRUD | UJ-043 |

Nav label remains `admin.nav.evaluation`; sub-view labels use new i18n keys under
`admin.eval.*`. Admin-only (hide entire `/evaluation` for viewer — RD-110).

### 2. Charting — shadcn/ui Chart + recharts (TP-S007-18, RD-120, R69)

| Item | Value |
|------|-------|
| Library | **`recharts`** (MIT) via shadcn/ui **Chart** primitives |
| Components | `EvalTrendCharts` — line/area series; threshold reference lines at CI gates |
| Data source | `GET /internal/v1/eval/runs/timeseries` |
| Filters | User-selectable metrics, date range (`since`/`until`), optional `run_ids` |
| Stretch | Overlay two runs on same chart (RD-121) |

**Why recharts:** Already the shadcn/ui Chart documented pattern; React 18 compatible; no D3
bundle in app code. **New FE dependency only** — no Python runtime change (ADR-033 §15 preserved).

### 3. Timeseries API (TP-S007-19, RD-116)

`GET /internal/v1/eval/runs/timeseries` on **internal-write-api**:

- Returns compact `{ items: [{ run_id, started_at, status, metrics }] }` for completed runs
- Query: `metrics`, `since`, `until`, `run_ids`, `limit` (default 100, max 500)
- Aggregates from `eval_runs.metrics_summary` JSONB — no scan of `eval_run_items` for v1
- Custom criterion keys included when present in `metrics_summary`
- Admin-only; viewer → 403

OpenAPI: extend `openapi/internal-write.yaml` in T64.8.

### 4. Extensible criteria — `eval_criteria` table + runner hook (TP-S007-20, RD-119)

Alembic migration adds **`eval_criteria`** (no PII):

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `key` | text UNIQUE | Stable metric key (e.g. `custom_conciseness`) |
| `name` | text | Display label |
| `scorer_type` | text | `builtin` \| `llm_rubric` v1 |
| `threshold` | float nullable | Display + pass/fail coloring |
| `enabled` | bool | Skip when false |
| `config` | JSONB nullable | Rubric prompt etc. — no PII |
| `created_at` / `updated_at` | timestamptz | |

**Built-in rows** seeded for `faithfulness`, `answer_relevancy`, `retrieval_relevance`,
`latency_p95_ms` (`builtin: true`, not deletable).

**Runner hook** (`packages/eval`): after built-in judges, iterate enabled custom criteria;
`llm_rubric` uses Modal LLM HTTP (same client as judges). Results merged into
`eval_run_items.metrics` and rolled into `eval_runs.metrics_summary`.

**API:** `GET/POST/PATCH /internal/v1/eval/criteria` per `api-contract.md` §EV-008.

### 5. Pivot explore — client-side aggregation v1 (TP-S007-21, RD-117)

`EvalExploreTable` component:

- Fetches run detail (`GET …/runs/{id}`) or recent runs list for multi-run explore
- User selects **row axis**, **column axis**, **value** (mean, pass rate, count)
- Axes: locale, domain (from golden metadata), case_id, metric name, pass/fail, run date bucket
- Aggregation in browser when total rows &lt; **500** (RD-117)
- Reuse **@tanstack/react-table** (already in admin FE)
- Stretch: CSV export (RD-121)

**Server-side pivot deferred** until row counts exceed client limit or staging corpus evals
grow beyond golden-set scale.

### 6. Layout persistence — device-local only (TP-S007-22, RD-118)

| Pref | Storage | Keys |
|------|---------|------|
| Collapsed chart panels | `localStorage` | `vecinita.eval.dashboard.panels` |
| Selected metrics / chart type | `localStorage` | `vecinita.eval.dashboard.metrics` |
| Explore pivot axis config | `localStorage` | `vecinita.eval.explore.axes` |

No server sync (ADR-004 — zero personal data; prefs are device-local operator UX).

### 7. Connectivity (TP-S007-23)

Extend `tests/unit/test_cors_policy.py` OPTIONS preflight for:

- `GET /internal/v1/eval/runs/timeseries`
- `GET/POST/PATCH /internal/v1/eval/criteria`

Same `configure_cors` + `Authorization` header pattern as baseline eval routes.

### 8. Git and redeploy (TP-S007-24)

| Item | Value |
|------|-------|
| Branch | `feat/S007-rag-eval` (unchanged) |
| PR | **PR-113** — M64 appended to Phase 14 |
| Redeploy order | migration (`eval_criteria`) → internal-write-api → data-management-frontend → CI |

### 9. Test tiers (extends ADR-033 §14)

| Tier | New coverage |
|------|----------------|
| T0 | `packages/eval` custom criteria scorer unit tests (mocked LLM) |
| T1 | `test_eval_timeseries.py`, `test_eval_criteria_routes.py` |
| T2 | Vitest TC-117–TC-121 |
| T3 | Live staging dashboard smoke at 13-deploy-smoke (informational) |

### 10. Dependencies (TP-S007-25)

| Package | Layer | New? | Notes |
|---------|-------|------|-------|
| **recharts** | `data-management-frontend` | **Yes** | Chart rendering; pin in app `package.json` |
| shadcn Chart | `data-management-frontend` | No | CLI add `chart` component (uses recharts) |

**Python:** still no new runtime deps.

## Consequences

**Positive**

- Operators get regression trends and flexible exploration without external observability tools
- Custom criteria extend eval without code deploys (admin-configured rubrics)
- Client-side pivot avoids new API surface for v1 golden-set scale
- Scope stays in S007 / EV-008 — single PR, single migration batch

**Negative**

- New FE dependency (`recharts`) — bundle size increase (~acceptable for admin-only app)
- `llm_rubric` custom criteria add LLM cost per enabled criterion per row
- Client pivot breaks down at large row counts — server aggregation needed later
- Layout prefs not shared across devices/browsers

## Alternatives considered

| Option | Verdict |
|--------|---------|
| Server-side pivot API | Deferred — unnecessary for &lt;500 rows |
| Langfuse/Phoenix dashboards | Rejected — same rationale as ADR-033 §1 |
| Chart.js / Victory | Rejected — shadcn/ui standard is recharts |
| New feature F37 | Rejected — R68 keeps scope in F36 / M64 |
| WebSocket live metrics | Out of scope — batch eval runs only |
