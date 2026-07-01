# ADR-033: EV-008 admin RAG evaluation — tooling, runner, and persistence

**Status:** Accepted  
**Stage:** 04-tech-plan (S007, EV-008)  
**Date:** 2026-07-01  
**Feature:** F36 — Admin RAG evaluation tab + golden eval set  
**Issue:** [#99](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/99)  
**Builds on:** [ADR-006](ADR-006-llamaindex-rag-orchestration.md), [ADR-004](ADR-004-cost-sovereignty-zero-personal-data.md), RD-099–RD-113, R63

## Context

GitHub #99 requests an admin-only **Model / RAG Evaluation** tab, a maintained bilingual golden
eval set, and a backend runner that scores retrieval + answer-quality metrics with persisted run
history. Issue #99 lists five tooling options (Langfuse, Ragas, DeepEval, custom, hybrid) and is
**blocked** until a deliberate choice is recorded.

01-requirements (S007) locked product decisions RD-099–RD-113: 10 cases / 14 locale rows,
retrieval ≥80% on `hit` + `any_of` rows, faithfulness and answer relevancy CI ≥0.60 with admin
highlight &lt;0.70, admin-only access (viewer → 403), judge in query language. Preliminary tooling
**R63** selected **LlamaIndex native evaluators + custom harness** in 00-context; this ADR
formalizes that choice and resolves remaining engineering decisions for 07-build.

Vecinita already runs RAG via **LlamaIndex 0.13.x** (`packages/rag`) with Modal **vLLM**
(Qwen2.5-1.5B-Instruct) as the synthesis and judge LLM. The standing harness
`tests/eval/test_eval_retrieval_relevance.py` covers only 3-pair URL-in-top-k scoring and must be
extended for the expanded fixture and answer metrics.

## Decision

### 1. Eval tooling — LlamaIndex + custom harness (TP-S007-01, RD-112, R63)

**Selected for v1:**

| Layer | Choice | Role |
|-------|--------|------|
| Retrieval scoring | **Custom** URL-in-top-k + `retrieval_expectation` (`hit`, `any_of`, `abstain`, `empty`) | Deterministic; no LLM judge |
| Faithfulness / groundedness | **LlamaIndex `FaithfulnessEvaluator`** | LLM-as-judge via Modal vLLM HTTP |
| Answer relevancy | **LlamaIndex `AnswerRelevancyEvaluator`** | LLM-as-judge via Modal vLLM HTTP |
| Persistence + admin UI | **Custom** Postgres tables + `data-management-frontend` `/evaluation` | Product goal is in-app admin tab, not a second observability platform |

**Rejected for v1 (defer):**

| Option | Reason |
|--------|--------|
| **Langfuse** | Self-host adds always-on Postgres + ClickHouse + Redis + S3; duplicates admin UI goal; ops/cost exceed pilot cap |
| **Ragas** | New Python dep; metrics overlap LlamaIndex evaluators; no admin UI |
| **DeepEval** | New Python dep; pytest-native overlap with existing `tests/eval/` harness |
| **Hybrid Ragas + Langfuse** | Two new stacks for marginal benefit |

**Revisit trigger:** If LlamaIndex judge scores are unstable on Qwen2.5-1.5B at &lt;0.60 aggregate
after golden-set tuning, evaluate **Ragas** as a drop-in metric library behind the same
`packages/eval` interface (no Langfuse v1).

**Dependencies:** **No new runtime packages** — evaluators ship in existing `llama-index` pin
(dependency-inventory §LlamaIndex evaluation).

### 2. New workspace package `packages/eval` (TP-S007-02)

Add **`vecinita-eval`** (`packages/eval/`) as Modal-agnostic core logic:

| Module | Responsibility |
|--------|----------------|
| `golden.py` | Load / validate `qa_pairs.json` schema |
| `retrieval.py` | URL-in-top-k scoring per `retrieval_expectation` |
| `judges.py` | LlamaIndex evaluator wiring; injectable LLM client |
| `runner.py` | Orchestrate full RAG path per row + aggregate metrics |
| `groundedness.py` | `GroundednessScorer` protocol — default `LlamaIndexFaithfulnessScorer`; swap for #84 verifier when landed |

Consumed by:

- `tests/eval/` — CI harness (TC-111–TC-113)
- `apps/internal-write-api` — admin-triggered runs (TC-114–TC-115)
- **Not** imported from Modal apps (ADR-007 write boundary unchanged)

### 3. Postgres schema (TP-S007-03)

Alembic migration adds two tables (no PII columns — ADR-004):

**`eval_runs`**

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | `run_id` in API |
| `status` | enum text | `pending` \| `running` \| `completed` \| `failed` |
| `corpus_profile` | text | `fixture` \| `staging` |
| `metrics_summary` | JSONB | Aggregates when complete |
| `error_message` | text nullable | On `failed` |
| `created_at` / `started_at` / `completed_at` | timestamptz | |

**`eval_run_items`**

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `run_id` | UUID FK → `eval_runs` | CASCADE delete |
| `case_id` | text | Golden row `id` |
| `locale` | text | `en` \| `es` |
| `question` | text | Fixture text only — no visitor PII |
| `expected_doc_url` | text nullable | |
| `retrieved_urls` | JSONB | string[] |
| `answer` | text nullable | Synthesized answer |
| `metrics` | JSONB | Per-row scores + `retrieval_pass` |
| `latency_ms` | int | Wall-clock for row |

Privacy test: `tests/privacy/test_eval_tables.py` asserts no email/name/ip columns.

### 4. Runner execution — DO BackgroundTasks, not new Modal app (TP-S007-04)

| Property | Value |
|----------|-------|
| Trigger | `POST /internal/v1/eval/runs` on **internal-write-api** |
| Response | `202` with `status: pending` |
| Execution | **FastAPI `BackgroundTasks`** on the DO container |
| RAG path | Same as ChatRAG: `packages/rag` retriever + synthesizer + **HTTP LLM client** to `VECINITA_MODAL_LLM_URL` |
| Embed | HTTP to `VECINITA_MODAL_EMBED_URL` (or test doubles in CI) |
| Timeout | Per-row; whole run bounded by DO request worker lifetime — acceptable for 14 rows (~2–5 min at pilot) |

**Why not Modal job v1:** Ingest/retag jobs need Modal for CPU-heavy corpus writes. Eval is
read-heavy RAG + judge calls already available via HTTP from DO (same pattern as `chat-rag-backend`).
Avoids a new Modal deployable and keeps admin trigger on the sole `DATABASE_URL` holder.

**Future:** If runs exceed DO worker limits (e.g. 100+ golden rows), add `job_type=eval` on Modal
data-management without changing API contract.

### 5. Corpus profiles (TP-S007-05)

| Profile | Corpus source | Default |
|---------|---------------|---------|
| `fixture` | `seed_eval_corpus()` + fixture URLs in `qa_pairs.json` | **Yes** — CI + local |
| `staging` | Live Postgres corpus on `DATABASE_URL` | Optional via POST body `corpus_profile: staging` |

Env default: `VECINITA_EVAL_CORPUS_PROFILE=fixture` (config-spec). Staging profile for operator
regression against production-like corpus; not used in CI gates.

### 6. Access control (TP-S007-06, RD-110)

All `/internal/v1/eval/*` routes require **`role=admin`** via `require_admin_write` (same as
destructive admin writes). **`viewer` → 403** on POST and GET. No read-only eval access for
viewers in v1.

### 7. API contract alignment (TP-S007-07)

Implement routes per `api-contract.md` §EV-008:

- `POST /internal/v1/eval/runs` — optional body `{ "corpus_profile": "fixture" | "staging" }`
- `GET /internal/v1/eval/runs` — paginated history
- `GET /internal/v1/eval/runs/{run_id}` — drill-down with `items[]`

Pydantic models in `vecinita_shared_schemas` (OpenAPI source of truth per ADR-011). Extend
`openapi/internal-write.yaml` in same milestone as routes.

### 8. Admin UI (TP-S007-08)

| Item | Value |
|------|-------|
| Route | `/evaluation` in `data-management-frontend` |
| Nav | `admin.nav.evaluation` (en/es) — lucide `FlaskConical` or `ListChecks` icon |
| Auth | Admin-only nav item (hide for viewer) |
| Flow | Summary → **Run evaluation** → poll `GET …/runs/{id}` until terminal → history list + drill-down table |
| Thresholds | Read `VECINITA_EVAL_*_DISPLAY_MIN` from API response metadata or hardcode display constants matching config-spec (server is source of truth for CI gates) |

Vitest: `test_evaluation_page.test.tsx` (TC-116). E2E: `test_uj039_eval_run_trigger.py` (TC-114/115).

### 9. #84 groundedness coordination (TP-S007-09)

Define `GroundednessScorer` protocol in `packages/eval/groundedness.py`:

- **v1 default:** `FaithfulnessEvaluator` score as `faithfulness` metric
- **When #84 lands:** Implement `OutputVerificationScorer` adapter that delegates to
  `packages/rag` groundedness verifier; eval tab surfaces the same field name (`faithfulness`)
  to avoid duplicate metrics

No blocker — ship v1 with LlamaIndex; swap adapter in a follow-up PR tied to #84.

### 10. LLM judge cost (TP-S007-10)

**Per run (v1 golden set):** 14 rows × (1 synthesis + 2 judge calls) ≈ **42 Modal LLM HTTP
requests**. At pilot scale (manual admin triggers, scale-to-zero T4), estimated **&lt;$0.50/run**
— within ADR-027 ~$75/mo cap. CI mocks judge responses (TC-112); no Modal GPU in merge gate.

### 11. Connectivity (TP-S007-11)

Eval routes use existing **internal-write-api CORS** (`configure_cors` + `Authorization` header).
Extend `tests/unit/test_cors_policy.py` with OPTIONS preflight on `POST /internal/v1/eval/runs`.
No new browser-facing FastAPI app.

### 12. Git strategy (TP-S007-12)

| Item | Value |
|------|-------|
| Branch | `feat/S007-rag-eval` (open) |
| PR | **PR-50** — Phase 14 / S007 (EV-008) → `main` |
| Commits | Atomic per task T59.x–T63.x on evolve-lite path |

### 13. Redeploy order (TP-S007-13)

Per `deployment-integration.md` §EV-008:

1. Alembic migration (`eval_runs`, `eval_run_items`)
2. **internal-write-api** — eval routes + runner
3. **data-management-frontend** — `/evaluation` tab
4. CI — extended `tests/eval/` + admin e2e

No Modal redeploy required for v1 runner (HTTP clients only). Ensure `VECINITA_MODAL_LLM_URL` and
`VECINITA_MODAL_EMBED_URL` set on internal-write-api if not already present for health checks.

### 14. Modal test tiers (TP-S007-14)

| Tier | Coverage |
|------|----------|
| T0 | `packages/eval` unit tests — mocked LLM |
| T1 | `tests/eval/` integration — Postgres + mocked Modal HTTP |
| T2 | `test_uj039_eval_run_trigger.py` — TestClient + admin JWT |
| T3 | Live staging eval run at 13-deploy-smoke (informational) |

### 15. Dependencies (TP-S007-16)

**No new dependencies.** LlamaIndex evaluators use existing `llama-index` pin. Record in
dependency-inventory §EV-008 evaluation.

## Consequences

**Positive**

- Unblocks #99 tooling blocker with zero new runtime deps
- Reuses LlamaIndex + Modal LLM stack — consistent with ChatRAG
- Admin tab is the single eval UI; no Langfuse ops burden
- `packages/eval` shared between CI and admin runs — one source of metric truth

**Negative**

- LlamaIndex judge quality tied to Qwen2.5-1.5B — may need rubric tuning or Ragas revisit
- BackgroundTasks on DO ties run duration to App Platform worker limits
- Viewer cannot read eval results — admin-only may limit team visibility (acceptable per RD-110)

## Alternatives considered

See §1 rejected options and `docs/context/rag-eval.md` §Eval framework provider re-evaluation.
