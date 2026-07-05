# ADR-035: EV-009 eval playground, unified jobs, and production RAG config

**Status:** Accepted  
**Stage:** 04-tech-plan (S008, EV-009)  
**Date:** 2026-07-02  
**Features:** F36 follow-ons (M65–M67) + **F37** (M68–M70)  
**Builds on:** [ADR-033](ADR-033-ev008-rag-evaluation-implementation.md), [ADR-034](ADR-034-ev008-eval-interactive-dashboard.md), [ADR-026](ADR-026-supabase-admin-auth.md), [ADR-009](ADR-009-vllm-primary-llm-modal.md), RD-114–RD-138

## Context

Post-F36 staging feedback on `/evaluation` requests four improvements: immediate run-list refresh,
eval runs on the unified **Jobs** tab, richer dashboard charts, and an admin **Playground** for
sandboxed RAG + judge experiments with versioned presets and super-admin **runtime promote** to
production ChatRAG (no redeploy).

01-requirements (S008) locked product scope (RD-114–RD-130). 04-tech-plan interview (2026-07-02)
resolved remaining engineering choices (RD-131–RD-138): fixed Modal LLM hyperparams only, single
`system_prompt` textarea, ChatRAG reads `rag_production_config` directly from shared Postgres,
forward-only promote with version history, two-column Playground layout, hardcoded default form
values, Jobs row click → `/evaluation?run=<id>`.

## Decision

### 1. Build order (TP-S008-01, R70)

Implement milestones **M65 → M66 → M67 → M68 → M69 → M70** on branch
`feat/S008-eval-ux-playground`. UX polish and Jobs integration ship before Playground backend/UI
and promote.

### 2. Optimistic run list (M65, TP-S008-02, RD-115)

After `POST /internal/v1/eval/runs` returns `202`, the admin FE **prepends** a pending run to the
history list immediately and updates status in place while polling `GET /internal/v1/eval/runs/{id}`.
`loadHistory()` full refresh remains on poll completion only. No API change.

### 3. Unified jobs list — HTTP aggregation (M66, TP-S008-03, RD-116)

`data-management-backend` `GET /jobs` merges:

1. Ingest/retag jobs from existing Modal Dict `JobStore`.
2. Eval runs fetched server-to-server from `internal-write-api`
   `GET /internal/v1/eval/runs` (internal API key), mapped to shared `Job` schema with
   `job_type: "eval"`.

Eval lifecycle stays in Postgres (`eval_runs`); no duplicate eval job rows in Modal Dict.
Status mapping: `pending` | `running` | `completed` | `failed` (1:1 with `eval_runs.status`).
`urls` empty; `options` may include `corpus_profile`, `mode`, `preset_id`.

**Rejected:** Writing eval jobs into Modal Dict at create time — duplicates source of truth and
requires cross-service sync on status updates.

### 4. Dashboard charts — frontend-only (M67, TP-S008-04, RD-117)

Extend `EvalMetricChart` / `EvaluationDashboardTab`:

- Chart types: **line**, **area** (existing), **scatter** (new).
- Time-range presets: **1D**, **7D**, **10D**, **1M**, **1Y**, **custom** (date picker).
- Filter client-side on existing `GET /internal/v1/eval/runs/timeseries` payload; no new API params
  in v1.
- Custom range with zero points → empty-state copy (TC-126).

X-axis formatting switches granularity by selected span (hour for 1D, day for 7D–1M, month for 1Y).

### 5. Config schema and validation (M68, TP-S008-05)

**New tables** (Alembic + privacy tests):

| Table | Purpose |
|-------|---------|
| `eval_config_presets` | Per-user versioned sandbox presets (`name`, `config` JSONB, `shared`, `owner_id`, `version`) |
| `rag_production_config` | Single active production row + version history (`config` JSONB, `config_version`, `promoted_at`, `promoted_by`) |

**`eval_runs` extension:** `config_snapshot` JSONB, `mode` (`golden` \| `adhoc`), optional `preset_id`.

**`EvalConfig` fields** (Pydantic in `vecinita_shared_schemas`, validated on create/preset/promote):

| Field | Type | Bounds | Default (form) |
|-------|------|--------|----------------|
| `top_k` | int | 1–50 (`MIN_TOP_K`/`MAX_TOP_K`) | 5 |
| `min_retrieval_score` | float | 0.0–1.0 | 0.2 |
| `system_prompt` | string | 1–8000 chars | built-in ChatRAG default text |
| `max_tokens` | int | 1–1024 | 256 |
| `temperature` | float | 0.0–2.0 | 0.2 |
| `corpus_profile` | enum | `fixture` \| `staging` | `fixture` |
| `criteria_ids` | uuid[] | existing eval criteria | all active criteria |
| `judge_temperature` | float | 0.0–2.0 | 0.2 |
| `model_id` | string | valid Ollama tag on `vecinita-models` volume | `qwen2.5:1.5b-instruct` |

**Model selection v1 (RD-132 superseded by RD-139–RD-141, 07-build interview 2026-07-02):**
**Ollama model picker** on Modal (`vecinita-models` volume). Playground lists models available via
the Ollama API; admin selects any stashed model. If the model is missing from the volume, a **Modal
background pull job** downloads it before the eval run proceeds. Super-admin **promote** includes
`model_id` so production ChatRAG switches LLM at runtime (not vLLM-only hyperparams).

**Rejected (RD-132):** Fixed Modal vLLM-only — user requires experimentation across Ollama models.
**Rejected:** External Ollama host in v1 — Modal Ollama only per RD-140.

**Guardrails v1 (RD-133):** Single `system_prompt` textarea (persona + rules + guardrails combined).
No structured rule builder in v1.

### 6. Sandbox isolation (TP-S008-07, RD-126)

Per-run `config` overrides apply only to the eval runner path (`packages/eval` + `packages/rag`).
Production ChatRAG is unchanged until super-admin promote. `config_snapshot` persisted on each run
for audit and compare.

### 7. Preset sharing (TP-S008-08, RD-121)

- **Private by default** (`shared: false`) — owner read/write.
- **Share-read** (`shared: true`) — other admins may list/read/clone; only owner may PATCH/delete.
- Clone creates a new preset owned by the cloner.

### 8. Playground UI (M69, TP-S008-09, RD-136)

New tab `?tab=playground` on `/evaluation`:

- **Two-column layout:** config form (left), run controls + recent results (right).
- Run modes: golden batch \| ad-hoc single question.
- **Run evaluation** button on Runs tab opens Playground with **hardcoded defaults** matching
  current ChatRAG env defaults (RD-137) — not live production DB config until user loads a preset.
- Compare runs: side-by-side aggregate + per-question diff (RD-130).
- Ad-hoc questions stored in `eval_run_items` (RD-128).

### 9. Super-admin role (M70, TP-S008-10, RD-127)

New JWT role **`super-admin`** in Supabase `app_metadata.role`, seeded for
`VECINITA_SUPER_ADMIN_EMAIL` at bootstrap. Hierarchy: `super-admin` > `admin` > `viewer`.

- `admin`: playground run/view/compare/presets.
- `super-admin`: above + `POST /internal/v1/rag/config/promote`.
- `viewer`: `403` on all eval and promote routes.

### 10. Production config promote (M70, TP-S008-11, RD-135)

`POST /internal/v1/rag/config/promote` (super-admin only):

- Source: completed run `config_snapshot` or saved preset.
- Upserts `rag_production_config` with monotonic `config_version`.
- **Forward-only v1:** rollback = re-promote an older preset/run from history (no one-click revert
  button).
- Audit log entry on promote.

### 11. ChatRAG config reader (M70, TP-S008-12, RD-134)

`chat-rag-backend` reads active row from `rag_production_config` via existing `DATABASE_URL` on
each `POST /api/v1/ask` (or lazy load at request start). Fallback to env vars
(`VECINITA_RAG_CONFIG_FALLBACK_*` per config-spec) when no row exists.

**Rejected:** HTTP call to `GET /internal/v1/rag/config/active` per request — adds latency and
couples ChatRAG to internal-write-api availability for every ask.

Admin UI may still call `GET /internal/v1/rag/config/active` for display.

### 12. Jobs tab navigation (TP-S008-13, RD-138)

Clicking `job_type=eval` row navigates to `/evaluation?run=<run_id>` with that run selected in
history. Ingest/retag behavior unchanged.

### 13. API surface (api-contract §EV-009)

Endpoints per `docs/api-contract.md` §EV-009: extended `POST /eval/runs`, preset CRUD,
`POST /rag/config/promote`, `GET /rag/config/active`. OpenAPI updated in 07-build.

### 14. Testing (TP-S008-14)

| Layer | Coverage |
|-------|----------|
| Vitest | TC-123–TC-130 (page, dashboard, playground, compare) |
| API E2E | TC-124, TC-127–TC-129, TC-131–TC-133 |
| Integration | `test_eval_config_presets.py`, `test_rag_production_config.py` |
| Playwright T0-ui | `uj044-eval-jobs-tab.spec.ts`, `uj045-eval-playground.spec.ts` |
| Privacy | New tables — no PII columns |

Modal tiers: T0–T2 merge-blocking; T3 live promote smoke at 13-deploy-smoke.

### 15. Dependencies (TP-S008-15)

**No new Python runtime dependencies.** Frontend: no new packages (reuse `recharts` for scatter).

### 16. Deploy order (TP-S008-16)

1. Alembic migration (presets + production config + eval_runs columns).
2. `internal-write-api` (preset routes, extended eval create, promote).
3. `data-management-backend` (unified jobs aggregation).
4. `chat-rag-backend` (production config reader).
5. `data-management-frontend` (M65–M69 UI).
6. Set `VECINITA_SUPER_ADMIN_EMAIL` on staging/prod.

## Consequences

**Positive**

- Operators see eval runs immediately and on Jobs tab without context switching.
- Sandbox experiments cannot accidentally change production ChatRAG.
- Runtime promote avoids redeploy for prompt/retrieval tuning.
- Chart improvements ship without backend API work.

**Negative / trade-offs**

- Unified jobs list adds one HTTP hop from DM backend to internal-write-api on each poll.
- ChatRAG reads DB each ask — acceptable at pilot scale; cache deferred.
- Ollama model pull jobs add Modal volume I/O and cold-start latency for new models.
- Super-admin is a single seeded email in v1 — expand role assignment in a later evolve cycle.

## Alternatives considered

| Alternative | Why rejected |
|-------------|--------------|
| Hotfix path for item 1 only | User chose full evolve for consistency (R69) |
| Separate eval jobs store in Modal Dict | Duplicate lifecycle; sync complexity |
| Backend timeseries range params | FE filter sufficient for v1 data volume (RD-117) |
| Langfuse / Phoenix for playground | Out of scope (session brief) |
| In-app redeploy button | Runtime DB switch instead (R71) |
| ChatRAG config via internal API | Extra hop; DB already shared (RD-134) |
