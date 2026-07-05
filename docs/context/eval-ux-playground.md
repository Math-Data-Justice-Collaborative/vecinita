# Scoped context — Evaluation UX polish + playground (S008)

**Session:** S008-eval-ux-playground  
**Stage:** 00-context (scoped delta)  
**Date:** 2026-07-02  
**Prior session:** S007-rag-eval (F36 / EV-008) — build complete; deploy stages 12–13 pending  
**Evolve cycle:** EV-009 (proposed)  
**Feature IDs:** F36 follow-ons (items 1–3) + **F37** (proposed — eval playground + super-admin promote)

---

## Executive summary

Post-deploy feedback on the admin **Evaluation** tab ([staging](https://vecinita-admin-frontend-ef4ob.ondigitalocean.app/evaluation))
requests four improvements: immediate run list refresh, unified **Jobs** visibility for eval runs,
richer dashboard charts, and a full **evaluation playground** for RAG + judge hyper-parameters with
versioned experiment history. User approved **evolve-lite** session **S008** (not hotfix path),
build order **1→2→3→4**, isolated sandbox with **runtime promote** to production via new
**super-admin** role, and **unified jobs API** for eval runs.

---

## User requests (verbatim themes)

| # | Request | User priority |
|---|---------|---------------|
| 1 | New eval run does not appear in history until manual page refresh | UX polish — first |
| 2 | Eval runs should appear on **Jobs** tab with status like ingest/retag | Integration — second |
| 3 | Time-series charts show day-only labels; want scatter, time spans (1D/7D/10D/1M/1Y/custom) | Dashboard — third |
| 4 | Config screen / playground: model, temperature, system prompt, guardrails, retrieval, judge rubrics | Largest — fourth |

---

## Current state (repo evidence)

### Item 1 — Run list not updating immediately

[`EvaluationPage.tsx`](../../apps/data-management-frontend/src/pages/EvaluationPage.tsx):
`handleRun` → `triggerEvalRun` → `pollRun` updates `selectedRun` only; `runs` list refreshes
only when `pollRun` finishes via `loadHistory()`. No optimistic prepend after create.

**Classification:** Implementation gap (not API). Minimal FE fix; user chose evolve path for consistency.

### Item 2 — Jobs tab excludes eval runs

| System | Store | Types |
|--------|-------|-------|
| Jobs (`/jobs`) | `data-management-backend` job store | `ingest`, `retag` only |
| Eval (`/evaluation`) | Postgres `eval_runs` via `internal-write-api` | Separate lifecycle |

[`JobsPage.tsx`](../../apps/data-management-frontend/src/pages/JobsPage.tsx) polls `listJobs` every 4s.
[`JobType`](../../apps/data-management-frontend/src/api/types.ts) = `"ingest" | "retag"`.

**User decision:** Unified jobs API — add `job_type=eval`, eval runner registers like ingest.

### Item 3 — Dashboard charts

[`EvalMetricChart.tsx`](../../apps/data-management-frontend/src/evaluation/EvalMetricChart.tsx):
X-axis uses `toLocaleDateString()` (day granularity). [`EvaluationDashboardTab`](../../apps/data-management-frontend/src/evaluation/EvaluationDashboardTab.tsx)
supports line/area toggle only; timeseries from `GET /internal/v1/eval/runs/timeseries?limit=N`.

**User decision:** v1 = **frontend-only** — preset ranges (1D/7D/1M/1Y/custom) + scatter chart type on existing API.

### Item 4 — Playground (no v1 surface today)

F36 v1 ([`feature-list.md` §F36](../feature-list.md)): golden-set batch runs;
`EvalRunCreateRequest` body = `corpus_profile: fixture | staging` only.
**Limitations:** no auto prompt tuning; judge uses Modal LLM same as ChatRAG.

**User decisions (interview 2026-07-02):**

| Topic | Decision |
|-------|----------|
| Configure | **Both** production RAG path + judge/scoring |
| Run modes | Golden-set batch **and** ad-hoc single-question experiments |
| Persistence | **Versioned** experiment history |
| Parameters | model, hyperparams, system_prompt, retrieval, guardrails, judge_rubric, corpus_profile |
| Isolation | **Sandbox** — overrides apply only to eval runs |
| Promote to prod | **Runtime switch** — super-admin sets DB-backed active production config; ChatRAG reads on next request (no redeploy button v1) |
| Roles | New **`super-admin`** — initially only canonical admin email; can promote config to production |
| Saved configs | **Per-user** presets; private by default, **share-read** (other admins can clone) |
| Jobs integration | Unified API (item 2) |

**Scope note:** F36 explicitly excluded prompt tuning; F37 playground is a **new feature** (maps to deferred **P4** "A/B prompts" partially). Requires 01-requirements delta + ADR for super-admin role and runtime config store.

---

## Multi-app topology (connectivity)

| Consumer | API | Change |
|----------|-----|--------|
| Admin FE `/evaluation` | `internal-write-api` | Playground UI, optimistic run list, chart controls |
| Admin FE `/jobs` | DM backend `GET /jobs` | Include `eval` job_type (unified list) |
| Eval runner | `packages/rag` + Modal + Postgres | Accept per-run config overrides; register job status |
| ChatRAG backend | `chat-rag-backend` | Read **active production config** row (runtime switch) — super-admin only write |

**Browser integration risk:** Low — same patterns as F32 jobs + F36 eval.

**Auth expansion:** `super-admin` > `admin` > `viewer` — Supabase `app_metadata.role`; gate promote endpoint.

---

## Resolution log (S008 00-context)

| # | Category | Resolution |
|---|----------|------------|
| R68 | Decision | Session: close S007 scope boundary; open **S008-eval-ux-playground** |
| R69 | Decision | Magnitude: **all evolve** (not hotfix) |
| R70 | Decision | Build order: **1→2→3→4** (UX first, playground last) |
| R71 | Decision | Playground isolation: sandbox + **runtime_switch** promote (super-admin) |
| R72 | Decision | Jobs: **unified_api** (`job_type=eval`) |
| R73 | Decision | Charts v1: **fe_only** presets + scatter on existing timeseries |
| R74 | Decision | Config visibility: **share_read** per-user presets |
| R75 | Decision | Routing: **evolve-lite** 00→01→04→07→08→09→10→11→12→13 |

---

## Unresolved gaps (for 04-tech-plan)

**All closed 2026-07-02** — see ADR-035 and `docs/sessions/S008-eval-ux-playground/reports/04-tech-plan.md`.

| Gap | Resolution |
|-----|------------|
| F37 feature ID | **F37** (RD-114) |
| Super-admin bootstrap | `VECINITA_SUPER_ADMIN_EMAIL` (RD-127) |
| Production config schema | `EvalConfig` bounds in config-spec + ADR-035 §5 |
| Ad-hoc eval privacy | `eval_run_items` retention (RD-128) |
| Chart custom range | Date picker + empty state (RD-117) |
| 04-tech-plan interview | RD-131–138, TP-S008-01–16 |
| S007 deploy | 12–13 remain on S007 backlog; S008 does not block |

---

## Proposed milestones (01-requirements draft)

| Milestone | Scope |
|-----------|-------|
| M65 | Item 1 — optimistic eval run list + poll UX |
| M66 | Item 2 — unified jobs API + Jobs tab `eval` type |
| M67 | Item 3 — dashboard chart types + time-range presets |
| M68 | Item 4a — eval config schema + per-user presets API |
| M69 | Item 4b — playground UI (golden + ad-hoc) |
| M70 | Item 4c — super-admin runtime promote + ChatRAG config reader |

---

## Source analysis

| Source | Finding |
|--------|---------|
| [Evaluation staging UI](https://vecinita-admin-frontend-ef4ob.ondigitalocean.app/evaluation) | User-reported refresh + jobs visibility gaps |
| `docs/feature-list.md` §F36 | Baseline eval tab; limitations inform F37 boundary |
| `docs/config-spec.md` §RAG evaluation | Env thresholds only; no per-run overrides today |
| `packages/rag/vecinita_rag/engine.py` | `top_k`, LLM assembly — override injection point for sandbox |
| S007 `docs/context/rag-eval.md` | Prior F36 context; superseded for playground by this brief |
