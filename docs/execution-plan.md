# Execution Plan

> **Project**: Vecinita  
> **Generated**: 2026-05-19 (EV-001 delta 2026-05-24; EV-002 delta 2026-05-26; EV-004 delta 2026-06-13; S003 delta 2026-06-26; S007 delta 2026-07-01; S008 delta 2026-07-02)  
> **Skill**: 04-tech-plan  
> **Specs consumed**: feature-list.md, spec.md, user-journeys.md, test-plan.md, config-spec.md, api-contract.md, data-management-plan.md, deployment-integration.md, dependency-inventory.md, acceptance-criteria.md, eval-golden-set.md, ADR-001–035

## Current State

| Field | Value |
|-------|-------|
| **Active phase** | Phase 15: EV-009 — Eval UX polish + playground (F36 follow-ons + F37) |
| **Active milestone** | M68: Config schema + preset API + DB (+ Ollama model picker) |
| **Active task** | **T68.8** — OpenAPI `internal-write.yaml` EV-009 routes *(next)* |
| **Tasks completed** | Phase 14 M59–M64 complete (S007); Phase 15 M65–M67 complete (S008) |
| **Last updated** | 2026-07-02 |
| **Evolve cycle** | EV-009 (F36 follow-ons + F37) — **04-tech-plan complete** |
| **Git branch** | `feat/S008-eval-ux-playground` |
| **Active session** | S008-eval-ux-playground — evolve-lite. 04-tech-plan approved (ADR-035, TP-S008-01–16). Build order M65→M70. |
| **Scope addition** | 2026-07-02 — S008/EV-009: run list refresh, unified jobs, dashboard charts, Playground + super-admin promote (ADR-035, UJ-044–047, TC-123–TC-133). |

## Template

| Field | Value |
|-------|-------|
| **Template ID** | `api+worker` |
| **Service name** | `vecinita` |
| **Database** | DigitalOcean Managed Postgres + pgvector |
| **Deploy** | Hybrid Modal (ingest, embed, vLLM) + DO (HTTP APIs, frontends, DB) |

## Tech Stack Summary

| Category | Choice | Source | Spec Reference |
|----------|--------|--------|----------------|
| Language (Python) | **3.11** | 04-tech-plan interview | spec.md H10 |
| Language (Node) | **24 LTS** | dependency-inventory.md; TP-S004-11 | Frontends |
| Linter | **Ruff** (+ `ANN401` no-Any) | hooks + ADR-018 | `docs/typing-policy.md` |
| Formatter | **Ruff format** | hooks | test-plan.md |
| Typechecker | **basedpyright** (`reportExplicitAny`) | ADR-018; `.cursor/hooks/typecheck.py` | `docs/typing-policy.md` (supersedes pyright/mypy) |
| TS type safety | **ESLint** `no-explicit-any` + `no-unsafe-*` | ADR-018 | `docs/typing-policy.md` |
| Test runner | **pytest** | test-plan.md | §Test Strategy |
| Frontend tests | **Vitest** | test-plan.md | Frontends |
| Package manager | **uv** (Python) + **npm workspaces** (frontends) | TP-035, ADR-012 | monorepo workspace |
| Frontend workspaces | **root package.json** — `apps/*`, `packages/frontend-*` | TP-035 | F31 |
| Shared i18n | **`packages/frontend-i18n`** — strict typed `t()` | TP-032, ADR-019 | F31 |
| Shared UI | **`packages/frontend-ui`** — React + Tailwind | TP-036, ADR-020 | F31 |
| RAG framework | **LlamaIndex 0.11.x** (pinned at M9) | ADR-006, interview | F4 |
| Vector store | **pgvector** 384-dim | ADR-005, ADR-008 | F5, F10 |
| Embeddings | **FastEmbed** on Modal | ADR-008 | F10 |
| LLM | **vLLM** + **Qwen2.5-1.5B-Instruct** on Modal T4 | ADR-009, 04-tech-plan | F6 |
| LLM fallback | **Ollama** (documented, not default) | ADR-009 | If cost gate fails after DO consolidation |
| API contracts | **OpenAPI** in `openapi/` | ADR-011 | spec.md |
| CI | **GitHub Actions** | test-plan.md | 06-tech-tooling creates workflows |
| Security scan | **pip-audit** blocking high/critical | 04-tech-plan | considerations.md §5 |
| Local DB | **docker-compose** Postgres 15 + pgvector | RD-011 | F18 |
| Gateway (v1) | **None** — direct backend URLs | 04-tech-plan (R6) | ADR-010 |

## Cost Estimate (04-tech-plan)

**Assumptions:** US regions; scale-to-zero on Modal GPU; light community traffic (~2k queries/mo); multi-app DO per ADR-010.

| Line item | Est. $/mo | Notes |
|-----------|-----------|-------|
| DO Managed Postgres (1 GB basic) | 15 | User-selected tier |
| DO App: `chat-rag-backend` (1 vCPU / 1 GiB) | 10–12 | May use $10 tier for headroom |
| DO App: `internal-write-api` ($5 shared) | 5 | Minimal always-on |
| DO App: static frontends (×2) | 0–10 | Often $5 each or shared static component |
| Modal CPU (embed + scrape + ASGI idle) | 2–8 | Per-invoke; low at pilot scale |
| Modal GPU T4 (vLLM, scale-to-zero) | 5–20 | ~10–35 GPU-hours/mo at pilot; **not** 24×7 |
| **Total (pilot)** | **~$42–48** (typical) | Upper stress **≤ $50** with scale-to-zero GPU |

**Gate result (TP-009):** Multi-app DO + vLLM **fits ≤ $50/mo** at pilot traffic with scale-to-zero GPU. Stress scenarios above $50 trigger consolidation (below) before cap breach. **$25/mo target** requires consolidation or minimal query volume — see mitigation.

**Cost-cap change — EV-005 (TP-S004-06, ADR-027):** Adding **Supabase Pro ($25/mo**, incl. $10
compute credits; required for branching) on top of the ~$42–48/mo above raises the all-in total to
**~$67–75/mo**. This **exceeds the prior $50 hard cap**; the user **approved raising the cap to
~$75/mo** (ADR-027 supersedes ADR-004's cost line). Branching is billed at `$0.01344`/preview
branch/hour and is **outside** the spend cap → keep preview branches **ephemeral** (tear down after
PR/migration). The org spend cap stays **ON** for non-branch usage.

| Line item (EV-005 addition) | Est. $/mo | Notes |
|-----------------------------|-----------|-------|
| Supabase Pro (identity + auth) | 25 | Includes $10 compute credits |
| Supabase preview branches | 0–10 | Ephemeral; ~$9.60/mo if a branch runs 24×7 |
| **New all-in total** | **~$67–75** | New hard cap **~$75/mo** (ADR-027) |

**If estimate exceeds $50 (Risk R1) — user lever order:**

1. **Consolidate DO** (interview): single App Platform app with multiple components; merge static sites into one SPA (`/chat`, `/admin`); keep internal write API as separate **process** only if security review requires — prefer one DO web service + one static site before touching LLM.
2. Downgrade LLM to Ollama or smaller model (ADR-009 fallback).
3. Raise cap only via explicit ADR change + user approval.

## Data Dependencies

| Asset | Type | Size | Staging Status | Needed By Tasks |
|-------|------|------|----------------|-----------------|
| D1 | Seed corpus EN | corpus_fixture | < 5 MB | pending | T2.5, T2.6, T8.2, T10.1, T10.6, UJ-001 |
| D2 | Seed corpus ES | corpus_fixture | < 5 MB | pending | T2.5, T2.6, T8.5, T10.1, UJ-001 |
| D3 | Eval Q&A pairs | eval_set | < 1 MB | pending | T2.8, T14.5 |
| D4 | Ingest HTML fixture | corpus_fixture | < 1 MB | pending | T2.9, T6.1, T6.5, UJ-002 |
| D5 | Alembic migrations | migration | — | pending | T3.2+ |
| D6 | FastEmbed weights | model_weights | ~100–500 MB | pending | T6.3 |
| D7 | Qwen2.5-1.5B-Instruct weights | model_weights | ~3 GB | pending | T10.3 |
| D8 | Seed tag vocabulary | config_fixture | < 50 KB | verified | T15.4, T15.6, TC-041, F20 |
| D9 | Tagged corpus fixtures | corpus_fixture | < 2 MB | pending | T15.5, T17.2, TC-040, TC-044 |
| D10 | Frontend i18n messages | workspace_package | repo-local | verified | T33.1–T33.4, T36.3–T36.6 |
| D11 | Frontend UI components | workspace_package | repo-local | verified | T34.1–T34.7 |

**Data management gate:** Assets must be `verified` in `docs/data-staging-state.md` before dependent tasks start.

## Implementation Phases

### Phase 1: Foundation

**Objective:** Monorepo scaffold, database schema, privacy guardrails, OpenAPI skeletons, dev tooling baseline.  
**Entry gate:** Execution plan approved (04-tech-plan Phase 4).  
**Exit gate:** Migrations apply on empty DB; privacy tests pass; ruff + basedpyright clean on scaffold; pytest runs (smoke).

#### M1: Monorepo scaffold

**Goal:** `apps/*`, `packages/*`, `infra/`, `tests/` layout per template-conformance.mdc.  
**Branch:** `feat/M1-monorepo-scaffold` → `phase/1-foundation`

| # | Task | Type | Status | Spec Source | Depends On | Data Deps |
|---|------|------|--------|-------------|------------|-----------|
| T1.1 | Create directory layout (`apps/*` incl. `internal-write-api`, `packages/`, `openapi/`, `tests/`) | Config | completed | spec.md §Component Overview, ADR-010 | — | — |
| T1.2 | Root `pyproject.toml` uv workspace + Python 3.11 pin | Config | completed | dependency-inventory.md | T1.1 | — |
| T1.3 | Placeholder `__init__.py` / package stubs per app | Config | completed | ADR-012 | T1.2 | — |
| T1.4 | Test: smoke import all packages (`tests/smoke/test_imports.py`) | Test | completed | test-plan.md §Smoke | T1.3 | — |
| T1.5 | Configure ruff + basedpyright (`pyproject.toml`, `pyrightconfig.json`; ADR-018) | Config | completed | 04-tech-plan | T1.2 | — |
| T1.6 | `infra/docker-compose.yml` Postgres 15 + pgvector image | Config | completed | deployment-integration.md | T1.1 | — |

**Parallelizable:** T1.1, T1.6 after T1.1 starts.

#### M2: Database schema & privacy

**Goal:** Alembic schema, pgvector 384-dim, forbidden-table tests, seed fixtures.  
**Branch:** `feat/M2-database-privacy` → `phase/1-foundation`

| # | Task | Type | Status | Spec Source | Depends On | Data Deps |
|---|------|------|--------|-------------|------------|-----------|
| T2.1 | Test: `tests/privacy/test_no_pii_tables.py` (red) | Test | completed | test-plan TC-031, ADR-004 | T1.4 | — |
| T2.2 | Alembic initial revision: documents, chunks, embeddings, jobs, config | Code | completed | data-management-plan.md §Schema | T2.1 | — |
| T2.3 | Test: pgvector extension + `vector(384)` dimension check | Test | completed | data-management-plan D5 | T2.2 | — |
| T2.4 | Implement migrations + `apps/database` Alembic env | Code | completed | feature-list F13 | T2.3 | — |
| T2.5 | Seed scripts + `data/fixtures/corpus/{en,es}/` | Code | completed | feature-list F14, data-mgmt D1–D2 | T2.4 | D1, D2 |
| T2.6 | Test: seed load + row counts (`tests/integration/test_seed.py`) | Test | completed | data-management-plan §Verification | T2.5 | D1, D2 |
| T2.7 | `data/fixtures/MANIFEST.json` checksums | Config | completed | data-management-plan.md | T2.5 | D1–D4 |
| T2.8 | Eval Q&A fixtures `data/fixtures/eval/` (D3) | Code | completed | feature-list F14, data-mgmt D3 | T2.5 | D3 |
| T2.9 | Ingest HTML fixture `data/fixtures/ingest/` (D4) | Code | completed | data-management-plan D4 | T2.5 | D4 |

#### M3: OpenAPI & shared schemas

**Goal:** Contract-first types for ChatRAG and data-mgmt surfaces.  
**Branch:** `feat/M3-openapi-schemas` → `phase/1-foundation`

| # | Task | Type | Status | Spec Source | Depends On | Data Deps |
|---|------|------|--------|-------------|------------|-----------|
| T3.1 | `openapi/chat-rag.yaml` — ask, ask/stream, health | Docs | completed | api-contract.md, ADR-011 | T1.1 | — |
| T3.2 | `openapi/data-management.yaml` — jobs, health | Docs | completed | api-contract.md | T1.1 | — |
| T3.3 | `openapi/internal-write.yaml` — write + corpus CRUD | Docs | completed | spec.md §DO internal write API | T2.2 | — |
| T3.4 | `packages/shared-schemas` Pydantic models from OpenAPI | Code | completed | ADR-011 | T3.1–T3.3 | — |
| T3.5 | Test: reject identity fields in ask body (red) | Test | completed | test-plan TC-030, config-spec | T3.4 | — |
| T3.6 | Validation layer for identity deny-list | Code | completed | ADR-004, config-spec | T3.5 | — |
| T3.7 | Shared observability: structured logging + `VECINITA_LOG_*`; no prompt persistence (F17, AC-P4) | Code | completed | feature-list F17, ADR-004 | T1.3 | — |

#### Phase 1 Gate Check

- [x] All M1–M3 tasks completed
- [x] `alembic upgrade head` succeeds on empty docker-compose DB
- [x] `pytest tests/smoke tests/privacy tests/integration/test_seed.py -q` passes
- [x] ruff + basedpyright clean (no `Any`; see `docs/typing-policy.md`)
- [x] OpenAPI files present and referenced in api-contract.md

---

### Phase 2: Data Management

**Objective:** DO internal write API, Modal FastEmbed, ingest pipeline, admin UI; UJ-002, UJ-003, UJ-006, UJ-008.  
**Entry gate:** Phase 1 gate passed.  
**Exit gate:** Ingest E2E (mocked Modal) passes; job lifecycle works; unauthorized rejected.

#### M4: DO internal write API

**Branch:** `feat/M4-internal-write-api` → `phase/2-data-management`

| # | Task | Type | Status | Spec Source | Depends On | Data Deps |
|---|------|------|--------|-------------|------------|-----------|
| T4.1 | Test: write API auth + upsert chunks (`tests/integration/test_write_api.py`) | Test | completed | test-plan, ADR-007 | T3.4, T2.4 | D1 |
| T4.2 | FastAPI app `apps/internal-write-api` | Code | completed | spec.md §DO internal write API | T4.1 | — |
| T4.3 | Corpus list/delete endpoints | Code | completed | feature-list F9 | T4.2 | — |
| T4.4 | Test: corpus delete excludes chunks (TC-012 prep) | Test | completed | test-plan TC-012 | T4.3 | D1 |

#### M5: FastEmbed Modal service

**Branch:** `feat/M5-fastembed-modal` → `phase/2-data-management`

| # | Task | Type | Status | Spec Source | Depends On | Data Deps |
|---|------|------|--------|-------------|------------|-----------|
| T5.1 | Test: embedding client mock contract (`tests/unit/test_embedding_client.py`) | Test | completed | ADR-008 | T1.3 | — |
| T5.2 | `packages/embedding-client` HTTP client | Code | completed | spec.md §Modal FastEmbed | T5.1 | — |
| T5.3 | Modal app `vecinita-embedding` + volume `embedding-models` | Code | completed | deployment-integration.md | T5.2 | D6 |
| T5.4 | Test: 384-dim vector shape integration (mocked HTTP) | Test | completed | data-management-plan §Verification | T5.3 | D6 |

#### M6: Modal ingest (ASGI + workers)

**Branch:** `feat/M6-modal-ingest` → `phase/2-data-management`

| # | Task | Type | Status | Spec Source | Depends On | Data Deps |
|---|------|------|--------|-------------|------------|-----------|
| T6.1 | `packages/ingest` scrape + chunk unit tests | Test | completed | feature-list F7 | T1.3 | D4 |
| T6.2 | Implement scrape/chunk helpers | Code | completed | spec.md §Data Management | T6.1 | — |
| T6.3 | Modal ASGI `/jobs` + `requires_proxy_auth` | Code | completed | ADR-002, RD-019 | T3.2, T4.2 | — |
| T6.4 | Modal queue worker: scrape → embed → DO write API | Code | completed | spec.md §Ingest path | T6.2, T5.2, T4.2 | D4, D6 |
| T6.5 | Test: job lifecycle mocked (`tests/e2e/test_uj002_ingest_job.py`) | Test | completed | UJ-002, TC-010 | T6.4 | D4 |
| T6.6 | Test: job failure (`tests/e2e/test_uj006_job_failure.py`) | Test | completed | UJ-006, TC-013 | T6.4 | — |
| T6.7 | Test: unauthorized (`tests/e2e/test_uj008_unauthorized_admin.py`) | Test | completed | UJ-008, TC-014 | T6.3 | — |

#### M7: Data Management Frontend

**Branch:** `feat/M7-data-mgmt-frontend` → `phase/2-data-management`

| # | Task | Type | Status | Spec Source | Depends On | Data Deps |
|---|------|------|--------|-------------|------------|-----------|
| T7.1 | Vite React scaffold `apps/data-management-frontend` | Config | completed | feature-list F12 | T1.1 | — |
| T7.2 | Jobs submit + poll UI | Code | completed | user-journeys UJ-002 | T6.3, T7.1 | — |
| T7.3 | Corpus list/delete UI | Code | completed | UJ-003 | T4.3, T7.2 | — |
| T7.4 | Vitest smoke for job form component | Test | completed | test-plan.md | T7.2 | — |
| T7.5 | Test: UJ-003 corpus delete E2E (`tests/e2e/test_uj003_corpus_delete.py`) | Test | completed | UJ-003, AC-D4 | T4.3, T7.3 | D1 |

#### Phase 2 Gate Check

- [x] `pytest tests/e2e/test_uj002*.py test_uj006*.py test_uj008*.py` passes (local tier)
- [x] Modal deploy configs documented in `infra/modal/`
- [x] No `DATABASE_URL` in Modal worker code (static check / scope-reviewer)

---

### Phase 3: ChatRAG

**Objective:** LlamaIndex RAG, vLLM, ChatRAG backend/frontend; UJ-001, UJ-005, UJ-007.  
**Entry gate:** Phase 2 gate passed.  
**Exit gate:** Ask + stream E2E pass with mocked Modal LLM/embed.

#### M8: packages/rag (LlamaIndex)

**Branch:** `feat/M8-packages-rag` → `phase/3-chatrag`

| # | Task | Type | Status | Spec Source | Depends On | Data Deps |
|---|------|------|--------|-------------|------------|-----------|
| T8.1 | Pin `llama-index` + `llama-index-vector-stores-postgres` 0.11.x | Config | completed | dependency-inventory, ADR-006 | T1.2 | — |
| T8.2 | Test: retriever returns seeded chunk (unit) | Test | completed | test-plan TC-001 | T2.6, T8.1 | D1 |
| T8.3 | Test: empty retrieval message (TC-003) | Test | completed | UJ-005 | T8.2 | — |
| T8.4 | Implement query engine + bilingual detect hook | Code | completed | spec.md §ChatRAG, ADR-013 | T8.3 | — |
| T8.5 | Test: Spanish question → Spanish chunk (TC-011) | Test | completed | UJ-001 | T8.4 | D2 |

#### M9: vLLM Modal service

**Branch:** `feat/M9-vllm-modal` → `phase/3-chatrag`

| # | Task | Type | Status | Spec Source | Depends On | Data Deps |
|---|------|------|--------|-------------|------------|-----------|
| T9.1 | Modal app `vecinita-llm` GPU T4, scale-to-zero | Config | completed | ADR-009, deployment-integration | T1.1 | D7 |
| T9.2 | vLLM serve **Qwen2.5-1.5B-Instruct** + health route | Code | completed | 04-tech-plan model decision | T9.1 | D7 |
| T9.3 | Test: LLM HTTP client mock streaming contract | Test | completed | test-plan TC-001 | T9.2 | — |

#### M10: ChatRAG Backend

**Branch:** `feat/M10-chat-rag-backend` → `phase/3-chatrag`

| # | Task | Type | Status | Spec Source | Depends On | Data Deps |
|---|------|------|--------|-------------|------------|-----------|
| T10.1 | Test: `POST /api/v1/ask` integration (mock Modal) | Test | completed | test-plan TC-002 | T8.4, T5.2, T9.3 | D1 |
| T10.2 | Test: `POST /api/v1/ask/stream` SSE (TC-001) | Test | completed | UJ-001 | T10.1 | D1 |
| T10.3 | FastAPI `apps/chat-rag-backend` routes + health | Code | completed | api-contract.md | T10.2 | — |
| T10.4 | Wire `packages/rag` + config (`VECINITA_*`) | Code | completed | config-spec.md | T10.3 | — |
| T10.5 | Test: reject identity fields E2E (`test_uj007`) | Test | completed | UJ-007, TC-030 | T3.6, T10.4 | — |
| T10.6 | Test: UJ-001 ask + stream E2E (`tests/e2e/test_uj001_ask_stream.py`) | Test | completed | UJ-001, AC-C1 | T10.4, T11.2 | D1 |
| T10.7 | Test: UJ-005 empty retrieval E2E (`tests/e2e/test_uj005_empty_retrieval.py`) | Test | completed | UJ-005, AC-C5 | T10.4 | D1 |

#### M11: ChatRAG Frontend

**Branch:** `feat/M11-chat-rag-frontend` → `phase/3-chatrag`

| # | Task | Type | Status | Spec Source | Depends On | Data Deps |
|---|------|------|--------|-------------|------------|-----------|
| T11.1 | Vite React scaffold `apps/chat-rag-frontend` | Config | completed | feature-list F11 | T1.1 | — |
| T11.2 | Streaming chat UI + source citations | Code | completed | UJ-001 | T10.3, T11.1 | — |
| T11.3 | Client-side-only history (no server session) | Code | completed | feature-list F3, ADR-004 | T11.2 | — |
| T11.4 | Vitest smoke chat component | Test | completed | test-plan.md | T11.2 | — |

#### Phase 3 Gate Check

- [ ] `pytest tests/e2e/test_uj001*.py test_uj005*.py test_uj007*.py` passes
- [ ] Per-component unit coverage ≥ 95% line + 95% branch on all twelve components (F31 / ADR-019; `make test-unit-coverage`)
- [ ] p95 latency measured in integration (informative; target < 15s excl. cold start)

---

### Phase 4: Integration & Deploy

**Objective:** Local dev docs, CI, staging deploy, cost validation.  
**Entry gate:** Phase 3 gate passed.  
**Exit gate:** Staging smoke H1–H3; cost spreadsheet archived; ready for 11-verify-impl.

#### M12: Local dev (F18)

**Branch:** `feat/M12-local-dev` → `phase/4-integration`

| # | Task | Type | Status | Spec Source | Depends On | Data Deps |
|---|------|------|--------|-------------|------------|-----------|
| T12.1 | Test: UJ-004 bootstrap smoke (`test_uj004_local_bootstrap.py`) | Test | completed | UJ-004, TC-020 | T10.3, T6.3 | D1–D5 |
| T12.2 | `infra/vecinita.yaml` example + README local dev | Docs | completed | config-spec.md | T12.1 | — |
| T12.3 | `modal serve` docs for embed + llm + data-mgmt | Docs | completed | deployment-integration.md | T12.2 | — |

#### M13: CI/CD (06-tech-tooling coordination)

**Branch:** `feat/M13-ci` → `phase/4-integration`

| # | Task | Type | Status | Spec Source | Depends On | Data Deps |
|---|------|------|--------|-------------|------------|-----------|
| T13.1 | GitHub Actions: ruff, basedpyright, pytest, pip-audit (blocking) | Config | completed | test-plan §CI/CD | T1.5 | — |
| T13.2 | Frontend eslint + vitest in CI | Config | completed | test-plan.md | T7.1, T11.1 | — |
| T13.3 | Privacy + OpenAPI validator hooks in CI | Config | completed | 03-plan-tooling skills | T13.1 | — |
| T13.4 | CI/static check: no `DATABASE_URL` in Modal worker paths (ADR-007) | Config | completed | ADR-007, Phase 2 gate | T6.4 | — |

#### M14: Staging deploy & smoke

**Branch:** `feat/M14-staging-deploy` → `phase/4-integration`

| # | Task | Type | Status | Spec Source | Depends On | Data Deps |
|---|------|------|--------|-------------|------------|-----------|
| T14.1 | DO App specs (multi-app) + Modal deploy scripts | Config | completed | ADR-010, deployment-integration | T13.1 | — |
| T14.2 | Staging secrets matrix doc | Docs | completed | deployment-integration §Secrets | T14.1 | — |
| T14.3 | Deploy staging; run H1–H3 smoke | Config | completed | 15-service-health tiers | T14.1 | D1–D7 |
| T14.4 | Cost monitoring baseline (80%/100% of $50) | Docs | completed | risk-register R1 | T14.3 | — |
| T14.5 | Eval benchmark run (D3): ≥80% relevance on fixture set (AC benchmarks) | Test | completed | acceptance-criteria benchmarks | T2.8, T8.4 | D3 |

#### Phase 4 Gate Check

- [x] Full `pytest` + vitest green in CI (main CI run 2026-05-19; local 53 passed, 3 skipped; vitest 4/4)
- [ ] Staging H1–H3 succeed — **deferred** until deploy URLs exist; operator procedure: [staging-runbook.md](staging-runbook.md) (`scripts/deploy/staging_smoke.sh`, `tests/smoke/test_staging_health.py`)
- [x] Cost estimate documented ≤ $50 (`docs/reference.md#cost-monitoring-baseline-adr-004` pilot ~$42–48/mo)
- [ ] `docs/data-staging-state.md` all required assets `verified` — D1–D5 verified; **D6/D7 pending** (Modal weights on first deploy)

---

### Phase 5: EV-001 — Corpus tags & browse

**Objective:** Tag schema, LLM tagging at ingest, public browse API, admin chunk/tag editor, tag-aware RAG (F19–F22).  
**Evolve cycle:** EV-001  
**Feature IDs:** F19, F20, F21, F22  
**Entry gate:** EV-001 product specs approved (02-verify-plan); tech decisions ADR-015.  
**Exit gate:** UJ-009–UJ-012 E2E pass (local tier); browse GET **H4** CORS + **H5** frontend bundle wiring verified; staging deploy smoke for tag routes (incl. admin PATCH preflight).

#### M15: Tag schema & fixtures

**Goal:** Alembic tag tables, seed vocabulary, tagged corpus fixtures, privacy guardrails.  
**Branch:** `feat/M15-tag-schema` → `evolve/EV-001-corpus-tags`

| # | Task | Type | Status | Spec Source | Depends On | Data Deps | evolve_cycle_id | feature_ids |
|---|------|------|--------|-------------|------------|-----------|-----------------|-------------|
| T15.1 | Test: tag tables have no identity columns (`tests/privacy/test_tag_tables.py`) | Test | completed | test-plan TC-031, ADR-004 | T2.4 | — | EV-001 | F20, F21 |
| T15.2 | Alembic revision: `tags`, `document_tags`, `chunk_tags`; extend `jobs.job_type` | Code | completed | data-management-plan §Schema, ADR-014 | T15.1 | — | EV-001 | F20, F21 |
| T15.3 | Test: tag FK constraints + migration upgrade (`tests/integration/test_tag_schema.py`) | Test | completed | data-management-plan | T15.2 | — | EV-001 | F20 |
| T15.4 | Seed loader for `data/fixtures/tags/seed_tags.json` (D8) | Code | completed | RD-031, config-spec | T15.2 | D8 | EV-001 | F20 |
| T15.5 | Tagged corpus fixtures `data/fixtures/corpus/tagged/` (D9) | Code | completed | test-plan TC-040, TC-044 | T15.4 | D9 | EV-001 | F19, F22 |
| T15.6 | Test: seed tags + tagged corpus load (`tests/integration/test_tag_seed.py`) | Test | completed | test-plan TC-041 | T15.5 | D8, D9 | EV-001 | F19, F20 |

#### M16: Ingest LLM tagging & admin re-tag (F20)

**Goal:** LLM auto-tag after chunk/before embed; internal-write tag upsert; async retag job.  
**Branch:** `feat/M16-ingest-tagging` → `evolve/EV-001-corpus-tags`

| # | Task | Type | Status | Spec Source | Depends On | Data Deps | evolve_cycle_id | feature_ids |
|---|------|------|--------|-------------|------------|-----------|-----------------|-------------|
| T16.1 | Test: LLM tag client mock contract (`tests/unit/test_llm_tag_client.py`) | Test | completed | ADR-015 TP-014 | T9.3 | — | EV-001 | F20, F22 |
| T16.2 | `packages/tagging` — prompt, vocabulary merge, cap enforcement, config validation, RD-030 language | Code | completed | config-spec, RD-028, RD-030 | T16.1 | D8 | EV-001 | F20, F22 |
| T16.3 | Ingest pipeline: tag after chunk, before embed; include tags in DO batch write | Code | completed | ADR-015 TP-010, spec.md §Ingest | T16.2, T6.4, T15.2 | D8 | EV-001 | F20 |
| T16.4 | Internal write API: tag upsert on ingest batch write path only | Code | completed | openapi/internal-write.yaml, ADR-015 TP-010 | T15.2, T4.2 | — | EV-001 | F20 |
| T16.5 | Test: TC-047 ingest LLM auto-tag E2E (`tests/e2e/test_uj002_ingest_tagging.py`) | Test | completed | UJ-002, TC-047, acceptance-criteria AC-T3 | T16.3, T16.4 | D4, D8 | EV-001 | F20 |
| T16.6 | Modal retag worker + `job_type=retag` enqueue | Code | completed | ADR-015 TP-011, TP-012 | T16.2, T6.3 | — | EV-001 | F20, F21 |
| T16.7 | `POST /internal/v1/documents/{id}/retag` → job id; poll `GET /jobs/{id}` | Code | completed | openapi/internal-write.yaml | T16.6, T16.4 | — | EV-001 | F21 |
| T16.8 | Test: admin async retag lifecycle (mock LLM) | Test | completed | UJ-011, ADR-015 | T16.7 | D9 | EV-001 | F21 |

#### M17: Public browse API, tag RAG, ChatRAG UI (F19, F22)

**Goal:** Public GET browse routes, union tag-filter retriever, `/corpus` UI, chat sidebar chips.  
**Branch:** `feat/M17-browse-tag-rag` → `evolve/EV-001-corpus-tags`

| # | Task | Type | Status | Spec Source | Depends On | Data Deps | evolve_cycle_id | feature_ids |
|---|------|------|--------|-------------|------------|-----------|-----------------|-------------|
| T17.1 | Regenerate shared-schemas from OpenAPI 0.2.0 tag/browse models | Code | completed | ADR-011, openapi/chat-rag.yaml | T15.2, T3.4 | — | EV-001 | F19, F22 |
| T17.2 | Test: TC-040, TC-041 browse API integration (red) | Test | completed | UJ-009, test-plan | T17.1, T15.6 | D9 | EV-001 | F19 |
| T17.3 | ChatRAG backend: `GET /api/v1/documents`, `/tags`, `/documents/{id}`; wire browse `VECINITA_*` config | Code | completed | api-contract.md, config-spec, F19 | T17.2 | — | EV-001 | F19 |
| T17.4 | Test: TC-046 CORS preflight on browse GET (`tests/unit/test_cors_policy.py`) | Test | completed | connectivity-gates H4 | T17.3 | — | EV-001 | F19 |
| T17.5 | `packages/rag` tag-filter SQL (union match) + LLM tag inference hook | Code | completed | ADR-015 TP-013, RD-027 | T16.2, T8.4 | D9 | EV-001 | F22 |
| T17.6 | Test: TC-044, TC-045 tag-filtered retrieval unit tests | Test | completed | UJ-012, test-plan, acceptance-criteria AC-T5, AC-T6 | T17.5 | D9 | EV-001 | F22 |
| T17.7 | Wire `AskRequest.tags[]` on ask/stream routes | Code | completed | openapi/chat-rag.yaml | T17.5, T10.4 | — | EV-001 | F22 |
| T17.8 | ChatRAG frontend `/corpus` browse page (tags, search, pagination, external URL) | Code | completed | UJ-009, UJ-010, AC-T2, ADR-015 TP-015 | T17.3, T11.1 | — | EV-001 | F19 |
| T17.9 | Chat sidebar tag filter chips → ask/stream payload | Code | completed | RD-032, UJ-012 | T17.7, T11.2 | — | EV-001 | F22 |
| T17.10 | Vitest: browse list + tag chip + external URL link (TC-048) | Test | completed | UJ-010, AC-T2, test-plan TC-048 | T17.8, T17.9 | — | EV-001 | F19, F22 |
| T17.11 | E2E: UJ-009 browse, UJ-012 tag-filtered ask | Test | completed | acceptance-criteria AC-T1, AC-T5 | T17.8, T17.9 | D9 | EV-001 | F19, F22 |

#### M18: Admin chunk viewer & tag editor (F21)

**Goal:** Admin UI for chunks and tags; human PATCH; retag trigger.  
**Branch:** `feat/M18-admin-tags` → `evolve/EV-001-corpus-tags`

| # | Task | Type | Status | Spec Source | Depends On | Data Deps | evolve_cycle_id | feature_ids |
|---|------|------|--------|-------------|------------|-----------|-----------------|-------------|
| T18.1 | Test: TC-042 admin chunk list (`tests/integration/test_admin_chunks.py`) | Test | completed | UJ-011 | T15.2 | D9 | EV-001 | F21 |
| T18.2 | Test: TC-043 tag cap enforcement (max 10 doc / 5 chunk) | Test | completed | RD-028 | T15.2 | D9 | EV-001 | F21 |
| T18.3 | Internal write API: `GET .../chunks`, PATCH document/chunk tag routes | Code | completed | openapi/internal-write.yaml | T18.1, T18.2 | — | EV-001 | F21 |
| T18.4 | Admin UI: chunk viewer (read-only text per chunk) | Code | completed | UJ-011, F21 | T18.3, T7.1 | — | EV-001 | F21 |
| T18.5 | Admin UI: tag editor + retag job trigger/poll | Code | completed | UJ-011, ADR-015 | T16.7, T18.4 | — | EV-001 | F21 |
| T18.6 | E2E: UJ-011 admin tags (`tests/e2e/test_uj011_admin_tags.py`) | Test | completed | acceptance-criteria AC-T4 | T18.5 | D9 | EV-001 | F21 |
| T18.7 | Test: TC-049 CORS PATCH preflight on admin tag routes (`test_cors_policy.py` + staging) | Test | completed | connectivity-gates H4, test-plan TC-049 | T18.3 | — | EV-001 | F21 |

#### M19: EV-001 deploy & connectivity

**Goal:** Staging secrets, connectivity smoke for new routes, EV-001 deploy validation.  
**Branch:** `feat/M19-ev001-deploy` → `evolve/EV-001-corpus-tags`

| # | Task | Type | Status | Spec Source | Depends On | Data Deps | evolve_cycle_id | feature_ids |
|---|------|------|--------|-------------|------------|-----------|-----------------|-------------|
| T19.1 | Update `docs/staging-secrets-matrix.md` — EV-001 browse uses existing `VITE_VECINITA_CHAT_API_URL` | Docs | completed | 04-tech-plan §Connectivity, deployment-integration | T17.3 | — | EV-001 | F19 |
| T19.2 | Extend `tests/smoke/test_staging_connectivity.py` — browse GET H4 | Test | completed | TC-046, connectivity-gates | T17.4 | — | EV-001 | F19 |
| T19.3 | Extend `scripts/deploy/verify_connectivity.sh` for `/api/v1/tags` preflight (H4) | Config | completed | 04-tech-plan §Connectivity | T19.2 | — | EV-001 | F19 |
| T19.5 | Extend `verify_connectivity.sh` H5 — chat bundle contains chat API host (browse + ask) | Config | completed | connectivity-gates H5 | T19.3, T17.8 | — | EV-001 | F19 |
| T19.4 | Staging deploy EV-001; run H1–H3 + browse/tag smoke | Config | completed | 13-deploy-smoke | T19.5, T18.7, T17.11, T18.6 | D1–D9 | EV-001 | F19–F22 |

#### Phase 5 Gate Check

- [x] All M15–M19 tasks completed
- [x] `alembic upgrade head` includes tag tables on empty DB (CI postgres + revision `20260524_0002`)
- [x] `pytest tests/e2e/test_uj009*.py test_uj011*.py test_uj012*.py -m "e2e and not live"` passes
- [x] Tag privacy tests pass (`tests/privacy/test_tag_tables.py`)
- [x] TC-046 CORS on browse GET passes locally (H0c); live H4 in `verify_connectivity.sh` when staging URLs set
- [x] H5 frontend bundle wiring (TC-048 Vitest; live H5 in `verify_connectivity.sh` when URLs set)
- [x] TC-049 admin PATCH CORS preflight passes locally (H0c); live H4 when staging URLs set
- [x] D8, D9 verified in `docs/data-staging-state.md`
- [x] Cost note: EV-001 LLM tagging within ≤ $50/mo pilot cap (ADR-015 TP-017) — see `docs/reference.md#cost-monitoring-baseline-adr-004`

---

---

### Phase 6: EV-002 Backend — Schema, Audit, Stats, Bulk (F27–F29, F25–F26)

**Objective:** New tables (audit_log, document_versions, document_serving_stats), audit emission helpers, serving stats endpoints, bulk operation endpoints, health aggregator, and stats summary — all on internal-write-api.  
**Entry gate:** EV-002 04-tech-plan approved; Phase 5 gate passed.  
**Exit gate:** All new endpoints pass integration tests; privacy tests pass with 3 new tables in allow-list; audit events emitted correctly.  
**Evolve cycle:** EV-002 (F23–F29)

#### M20: EV-002 Schema migration

**Goal:** Alembic migration for `audit_log`, `document_versions`, `document_serving_stats`; privacy allow-list update.  
**Branch:** `feat/M20-ev002-schema` → `evolve/EV-002-admin-overhaul`

| # | Task | Type | Status | Spec Source | Depends On | Data Deps | evolve_cycle_id | feature_ids |
|---|------|------|--------|-------------|------------|-----------|-----------------|-------------|
| T20.1 | Test: privacy allow-list includes 3 new tables (`tests/privacy/test_ev002_tables.py`) — red | Test | completed | ADR-016, AC-E11 | T15.2 | — | EV-002 | F28, F29 |
| T20.2 | Alembic migration `20260526_0003_ev002_audit_stats.py`: `audit_log`, `document_versions`, `document_serving_stats` | Code | completed | ADR-016 §Schema, api-contract F28/F29 | T20.1 | — | EV-002 | F28, F29 |
| T20.3 | Update privacy allow-list (`vecinita_database/privacy.py`) to include new tables | Code | completed | spec.md §Forbidden schema | T20.2 | — | EV-002 | F28, F29 |
| T20.4 | Test: migration applies cleanly + table structure matches spec (integration) | Test | completed | data-management-plan §Verification | T20.3 | — | EV-002 | F28, F29 |

#### M21: Audit log & version history endpoints (F29)

**Goal:** `emit_audit_event()` helper, version snapshot creation, GET endpoints for audit log and document history.  
**Branch:** `feat/M21-audit-endpoints` → `evolve/EV-002-admin-overhaul`

| # | Task | Type | Status | Spec Source | Depends On | Data Deps | evolve_cycle_id | feature_ids |
|---|------|------|--------|-------------|------------|-----------|-----------------|-------------|
| T21.1 | Test: `emit_audit_event()` inserts audit_log row with correct fields (`tests/unit/test_audit_helpers.py`) — red | Test | pending | api-contract F29, ADR-016 | T20.4 | — | EV-002 | F29 |
| T21.2 | Implement `emit_audit_event()` + `create_document_version()` helpers in internal-write-api | Code | pending | ADR-016, TP-023 (explicit calls) | T21.1 | — | EV-002 | F29 |
| T21.3 | Wire `emit_audit_event()` into existing write endpoints (batch_upsert, delete_document, patch_document_tags, patch_chunk_tags, retag_document) | Code | pending | TP-023, TP-025 | T21.2 | — | EV-002 | F29 |
| T21.4 | Test: existing write ops now emit audit events (`tests/integration/test_audit_emission.py`) | Test | pending | TC-056, AC-E8 | T21.3 | D1 | EV-002 | F29 |
| T21.5 | Implement `GET /internal/v1/audit` — paginated, filterable by event_type/entity_type/date | Code | pending | api-contract §GET /internal/v1/audit | T21.2 | — | EV-002 | F29 |
| T21.6 | Test: audit log pagination + filters (`tests/e2e/test_uj017_audit_log.py`) | Test | pending | UJ-017, TC-056, TC-057, AC-E8 | T21.5 | — | EV-002 | F29 |
| T21.7 | Implement `GET /internal/v1/documents/{id}/history` — version timeline | Code | pending | api-contract §GET /documents/{id}/history | T21.2 | — | EV-002 | F29 |
| T21.8 | Test: document version history (`tests/e2e/test_uj018_document_history.py`) | Test | pending | UJ-018, TC-058, AC-E9 | T21.7, T21.3 | — | EV-002 | F29 |

#### M22: Serving stats endpoints (F28)

**Goal:** `POST /internal/v1/stats/served`, `GET /internal/v1/stats/top-served`, fire-and-forget integration in chat-rag-backend.  
**Branch:** `feat/M22-serving-stats` → `evolve/EV-002-admin-overhaul`

| # | Task | Type | Status | Spec Source | Depends On | Data Deps | evolve_cycle_id | feature_ids |
|---|------|------|--------|-------------|------------|-----------|-----------------|-------------|
| T22.1 | Test: `POST /internal/v1/stats/served` upserts counter (`tests/integration/test_serving_stats.py`) — red | Test | completed | TC-059, AC-E7 | T20.4 | — | EV-002 | F28 |
| T22.2 | Implement `POST /internal/v1/stats/served` (upsert into document_serving_stats) | Code | completed | api-contract §POST /stats/served | T22.1 | — | EV-002 | F28 |
| T22.3 | Test: `GET /internal/v1/stats/top-served` returns ranked list | Test | completed | api-contract §GET /stats/top-served, UJ-019 | T22.2 | — | EV-002 | F28 |
| T22.4 | Implement `GET /internal/v1/stats/top-served` | Code | completed | api-contract §GET /stats/top-served | T22.3 | — | EV-002 | F28 |
| T22.5 | Integrate async fire-and-forget `POST /stats/served` in chat-rag-backend after successful RAG response | Code | completed | TP-022, spec.md §Data Flow step 13 | T22.2, T10.4 | — | EV-002 | F28 |
| T22.6 | Test: chat-rag-backend fires stats POST on successful ask (`tests/unit/test_stats_fire_and_forget.py`) | Test | completed | TP-022 | T22.5 | D1 | EV-002 | F28 |

#### M23: Bulk operations endpoints (F27)

**Goal:** Bulk delete, bulk tag, bulk retag, bulk metadata — partial success, audit emission.  
**Branch:** `feat/M23-bulk-ops` → `evolve/EV-002-admin-overhaul`

| # | Task | Type | Status | Spec Source | Depends On | Data Deps | evolve_cycle_id | feature_ids |
|---|------|------|--------|-------------|------------|-----------|-----------------|-------------|
| T23.1 | Test: `DELETE /internal/v1/documents/bulk` deletes up to 100 + emits audit (`tests/e2e/test_uj015_bulk_delete.py`) — red | Test | completed | UJ-015, TC-053, AC-E5 | T21.3, T20.4 | D1 | EV-002 | F27 |
| T23.2 | Implement bulk delete endpoint (partial success pattern per TP-024) | Code | completed | api-contract §DELETE /documents/bulk, TP-024 | T23.1 | — | EV-002 | F27 |
| T23.3 | Test: `PATCH /internal/v1/documents/bulk/tags` respects max-10 cap + emits audit (`tests/e2e/test_uj016_bulk_tag.py`) — red | Test | completed | UJ-016, TC-055, AC-E6 | T21.3 | D1 | EV-002 | F27 |
| T23.4 | Implement bulk tag endpoint (add + remove; cap enforcement) | Code | completed | api-contract §PATCH /documents/bulk/tags | T23.3 | — | EV-002 | F27 |
| T23.5 | Test: `POST /internal/v1/documents/bulk/retag` enqueues retag jobs — red | Test | completed | api-contract §POST /documents/bulk/retag | T23.2 | — | EV-002 | F27 |
| T23.6 | Implement bulk retag endpoint | Code | completed | api-contract §POST /documents/bulk/retag | T23.5 | — | EV-002 | F27 |
| T23.7 | Test: `PATCH /internal/v1/documents/bulk/metadata` updates title/language + emits audit — red | Test | completed | api-contract §PATCH /documents/bulk/metadata | T21.3 | D1 | EV-002 | F27 |
| T23.8 | Implement bulk metadata endpoint | Code | completed | api-contract §PATCH /documents/bulk/metadata | T23.7 | — | EV-002 | F27 |

#### M24: Health aggregator & stats summary (F25, F26)

**Goal:** `GET /internal/v1/health/all` aggregator, `GET /internal/v1/stats/summary` dashboard endpoint.  
**Branch:** `feat/M24-health-stats` → `evolve/EV-002-admin-overhaul`

| # | Task | Type | Status | Spec Source | Depends On | Data Deps | evolve_cycle_id | feature_ids |
|---|------|------|--------|-------------|------------|-----------|-----------------|-------------|
| T24.1 | Test: `GET /internal/v1/health/all` returns status per service (`tests/unit/test_health_aggregator.py`) — red | Test | completed | UJ-014, TC-052, AC-E4 | T20.4 | — | EV-002 | F26 |
| T24.2 | Implement health aggregator endpoint (httpx parallel polling with VECINITA_HEALTH_TIMEOUT_MS) | Code | completed | feature-list F26, TP-019 | T24.1 | — | EV-002 | F26 |
| T24.3 | Test: `GET /internal/v1/stats/summary` returns aggregated counts (`tests/unit/test_stats_summary.py`) — red | Test | completed | UJ-013, TC-051, AC-E3 | T22.4, T21.5 | — | EV-002 | F25 |
| T24.4 | Implement stats summary endpoint (real-time SQL per TP-020) | Code | completed | api-contract §GET /stats/summary | T24.3 | — | EV-002 | F25 |
| T24.5 | Test: CORS preflight on all new EV-002 endpoints (DELETE, PATCH, GET) from admin origin (`tests/unit/test_cors_ev002.py`) | Test | completed | TC-060, AC-E10 | T23.8, T24.4, T24.2 | — | EV-002 | F23–F29 |
| T24.6 | Extend `configure_cors()` — ensure DELETE + PATCH verbs allowed for internal-write-api | Code | completed | cors-browser-methods.mdc, TP-019 | T24.5 | — | EV-002 | F27 |

#### Phase 6 Gate Check

- [x] All M20–M24 tasks completed (2026-05-26)
- [x] `alembic upgrade head` includes 3 new tables; `pytest tests/privacy/` passes (6/6)
- [x] `pytest tests/e2e/test_uj015*.py test_uj016*.py test_uj017*.py test_uj018*.py` passes (15/15)
- [x] TC-060 CORS preflight on new endpoints passes locally — H0c (9/9)
- [x] Audit emission verified on existing + new write paths (3/3 integration)
- [x] T24.3/T24.4 stats summary endpoint returns aggregated counts — F25 (5/5) <!-- TS-EV002-C07 -->
- [x] T24.1/T24.2 health aggregator polls all 8 services within timeout — F26 (3/3) <!-- TS-EV002-C07 -->
- [x] Cost note: No new cloud resources needed (same DO internal-write-api; no new Modal)

---

### Phase 7: EV-002 Frontend — Admin UI Overhaul (F23, F24, F25, F26, F27, F29)

**Objective:** shadcn/ui migration, React Router navigation, tag display, dashboard, health, bulk ops, audit log UI — all in data-management-frontend.  
**Entry gate:** Phase 6 gate passed (all backend endpoints functional).  
**Exit gate:** All admin pages render; Vitest component tests pass; admin navigation works across all sections.  
**Evolve cycle:** EV-002 (F23–F29)

#### M25: shadcn/ui scaffold + routing (F23)

**Goal:** Install Tailwind v3, shadcn/ui init, React Router v7, layout shell with navigation.  
**Branch:** `feat/M25-shadcn-routing` → `evolve/EV-002-admin-overhaul`

| # | Task | Type | Status | Spec Source | Depends On | Data Deps | evolve_cycle_id | feature_ids |
|---|------|------|--------|-------------|------------|-----------|-----------------|-------------|
| T25.1 | Install Tailwind v3 + PostCSS + autoprefixer in data-management-frontend | Config | completed | dependency-inventory, TP-018 | T7.1 | — | EV-002 | F23 |
| T25.2 | Run `npx shadcn-ui@latest init`; configure `components.json` (New York style, CSS variables) | Config | completed | TP-026 | T25.1 | — | EV-002 | F23 |
| T25.3 | Add shadcn components: Button, Card, Badge, Table, Dialog, Sheet, Tabs, Input, Select, Checkbox | Config | completed | feature-list F23 | T25.2 | — | EV-002 | F23 |
| T25.4 | Install react-router v7; create route structure (/dashboard, /corpus, /health, /audit) | Config | completed | TP-021, UJ-020 | T25.2 | — | EV-002 | F23 |
| T25.5 | Implement layout shell: sidebar navigation, system-preference dark/light theme, responsive | Code | completed | UJ-020, AC-E1 | T25.3, T25.4 | — | EV-002 | F23 |
| T25.6 | Migrate existing JobForm and CorpusList to shadcn/ui components (preserve functionality) | Code | completed | feature-list F23 | T25.5 | — | EV-002 | F23 |
| T25.7 | Test: admin navigation between pages + theme toggle (`tests/frontend/test_admin_nav.test.tsx`) | Test | completed | TC-063, UJ-020 | T25.5 | — | EV-002 | F23 |

#### M26: Tag display + corpus modernization (F24)

**Goal:** Tag chips in corpus list, color-coded by source (LLM vs human), modernized list layout.  
**Branch:** `feat/M26-tag-display` → `evolve/EV-002-admin-overhaul`

| # | Task | Type | Status | Spec Source | Depends On | Data Deps | evolve_cycle_id | feature_ids |
|---|------|------|--------|-------------|------------|-----------|-----------------|-------------|
| T26.1 | Extend corpus list API call to include document tags in response | Code | completed | api-contract, feature-list F24 | T25.6 | — | EV-002 | F24 |
| T26.2 | Implement TagBadge component (color-coded: LLM=blue, human=green) | Code | completed | UJ-021, AC-E2 | T25.3 | — | EV-002 | F24 |
| T26.3 | Render tag chips below document title in CorpusList | Code | completed | UJ-021, AC-E2 | T26.1, T26.2 | — | EV-002 | F24 |
| T26.4 | Test: tag chips render for seeded documents (`tests/frontend/test_tag_chips.test.tsx`) | Test | completed | TC-064, UJ-021 | T26.3 | — | EV-002 | F24 |

#### M27: Dashboard + health pages (F25, F26)

**Goal:** Admin summary dashboard with stat cards; health status grid with polling.  
**Branch:** `feat/M27-dashboard-health` → `evolve/EV-002-admin-overhaul`

| # | Task | Type | Status | Spec Source | Depends On | Data Deps | evolve_cycle_id | feature_ids |
|---|------|------|--------|-------------|------------|-----------|-----------------|-------------|
| T27.1 | Implement Dashboard page — stat cards (documents, chunks, tags, jobs, languages, storage) | Code | completed | UJ-013, feature-list F25, AC-E3 | T25.5, T24.4 | — | EV-002 | F25 |
| T27.2 | Implement "Top Served Documents" widget on Dashboard | Code | completed | UJ-019, feature-list F28 | T27.1, T22.4 | — | EV-002 | F28 |
| T27.3 | Implement "Recent Activity" feed widget from audit log | Code | completed | feature-list F25 | T27.1, T21.5 | — | EV-002 | F25, F29 |
| T27.4 | Test: dashboard renders all stat types with loading/error states (`tests/frontend/test_dashboard.test.tsx`) | Test | completed | TC-051, AC-E3 | T27.3 | — | EV-002 | F25 |
| T27.5 | Implement Health page — service status grid with manual refresh | Code | completed | UJ-014, feature-list F26, AC-E4 | T25.5, T24.2 | — | EV-002 | F26 |
| T27.6 | Test: health page shows up/down per service (`tests/frontend/test_health_page.test.tsx`) | Test | completed | TC-052, AC-E4 | T27.5 | — | EV-002 | F26 |

#### M28: Bulk operations UI (F27)

**Goal:** Multi-select checkbox, bulk action toolbar, confirmation dialogs, partial success feedback.  
**Branch:** `feat/M28-bulk-ops-ui` → `evolve/EV-002-admin-overhaul`

| # | Task | Type | Status | Spec Source | Depends On | Data Deps | evolve_cycle_id | feature_ids |
|---|------|------|--------|-------------|------------|-----------|-----------------|-------------|
| T28.1 | Add multi-select checkboxes to corpus list + "select all" + shift-click | Code | completed | UJ-015, feature-list F27 | T26.3 | — | EV-002 | F27 |
| T28.2 | Implement bulk action toolbar (delete, tag, retag, edit metadata) — appears when selection > 0 | Code | completed | feature-list F27, AC-E5/E6 | T28.1 | — | EV-002 | F27 |
| T28.3 | Implement bulk delete dialog (confirmation + partial success display) | Code | completed | UJ-015, TP-024 | T28.2, T23.2 | — | EV-002 | F27 |
| T28.4 | Implement bulk tag dialog (add/remove tags) | Code | completed | UJ-016 | T28.2, T23.4 | — | EV-002 | F27 |
| T28.5 | Implement bulk metadata edit dialog (title/language) | Code | completed | feature-list F27 | T28.2, T23.8 | — | EV-002 | F27 |
| T28.6 | Test: bulk select + delete flow (`tests/frontend/test_bulk_ops.test.tsx`) | Test | completed | AC-E5, AC-E6 | T28.5 | — | EV-002 | F27 |

#### M29: Audit log + version history UI (F29)

**Goal:** Global audit log page with filters; per-document history timeline in document detail.  
**Branch:** `feat/M29-audit-ui` → `evolve/EV-002-admin-overhaul`

| # | Task | Type | Status | Spec Source | Depends On | Data Deps | evolve_cycle_id | feature_ids |
|---|------|------|--------|-------------|------------|-----------|-----------------|-------------|
| T29.1 | Implement Audit Log page — table with event_type, entity, timestamp, payload summary | Code | completed | UJ-017, feature-list F29, AC-E8 | T25.5, T21.5 | — | EV-002 | F29 |
| T29.2 | Add filters: event_type dropdown, date range picker, entity_id search | Code | completed | UJ-017 | T29.1 | — | EV-002 | F29 |
| T29.3 | Add expandable payload detail (JSON diff viewer) per audit entry | Code | completed | UJ-017 | T29.1 | — | EV-002 | F29 |
| T29.4 | Implement per-document history timeline in document detail view | Code | completed | UJ-018, AC-E9 | T29.1, T21.7 | — | EV-002 | F29 |
| T29.5 | Test: audit log page pagination + filter (`tests/frontend/test_audit_page.test.tsx`) | Test | completed | TC-056, TC-057 | T29.3 | — | EV-002 | F29 |
| T29.6 | Test: document history timeline renders (`tests/frontend/test_doc_history.test.tsx`) | Test | completed | TC-058 | T29.4 | — | EV-002 | F29 |

#### Phase 7 Gate Check

- [x] All M25–M29 tasks completed
- [x] `cd apps/data-management-frontend && npm run lint && npm test` passes (0 errors, 32 tests pass)
- [x] All admin pages accessible via React Router (/dashboard, /corpus, /health, /audit)
- [x] Theme toggle follows system preference; responsive at 768px + 1280px
- [x] Vitest component tests cover all new pages/components (8 test files, 32 tests)

---

### Phase 8: EV-002 Integration & Deploy (F28, F29)

**Objective:** Audit retention background job, CORS + connectivity verification, staging deploy with full validation.  
**Entry gate:** Phase 7 gate passed.  
**Exit gate:** Staging deploy with H1–H5 passing; all EV-002 endpoints operational.  
**Evolve cycle:** EV-002 (F23–F29)

#### M30: Audit retention + integration polish

**Goal:** Background cleanup job for audit retention; OpenAPI spec updates; E2E integration.  
**Branch:** `feat/M30-retention-integration` → `evolve/EV-002-admin-overhaul`

| # | Task | Type | Status | Spec Source | Depends On | Data Deps | evolve_cycle_id | feature_ids |
|---|------|------|--------|-------------|------------|-----------|-----------------|-------------|
| T30.1 | Test: audit cleanup deletes records older than retention period (`tests/unit/test_audit_retention.py`) — red | Test | completed | TC-061, TP-027 | T21.5 | — | EV-002 | F29 |
| T30.2 | Implement `cleanup_audit_log()` function + daily background trigger (Modal cron or DO cron job) | Code | completed | TP-027, feature-list F29 | T30.1 | — | EV-002 | F29 |
| T30.3 | Update `openapi/internal-write.yaml` with all EV-002 endpoints | Docs | completed | ADR-011 | T24.6 | — | EV-002 | F23–F29 |
| T30.4 | Full E2E integration test: ingest → stats increment → audit → bulk delete → verify history (`tests/e2e/test_ev002_integration.py`) | Test | completed | UJ-013–UJ-021 | T29.6, T22.6, T23.2 | D1 | EV-002 | F25–F29 |

#### M31: EV-002 Deploy & connectivity

**Goal:** Staging secrets, CORS, deploy sequence, H1–H5 verification.  
**Branch:** `feat/M31-ev002-deploy` → `evolve/EV-002-admin-overhaul`

| # | Task | Type | Status | Spec Source | Depends On | Data Deps | evolve_cycle_id | feature_ids |
|---|------|------|--------|-------------|------------|-----------|-----------------|-------------|
| T31.1 | Update `docs/staging-secrets-matrix.md` — new env vars (VECINITA_HEALTH_TIMEOUT_MS, VECINITA_STATS_ENABLED, VECINITA_AUDIT_RETENTION_DAYS) | Docs | completed | staging-secrets-matrix, config-spec | T30.3 | — | EV-002 | F25–F29 |
| T31.2 | Extend `tests/smoke/test_staging_connectivity.py` — EV-002 endpoints H4 preflight | Test | completed | TC-060, AC-E10, connectivity-gates | T24.6 | — | EV-002 | F23–F29 |
| T31.3 | Extend `scripts/deploy/verify_connectivity.sh` for EV-002 routes | Config | completed | connectivity-gates H4 | T31.2 | — | EV-002 | F23–F29 |
| T31.4 | Deploy: run Alembic migration (new tables) | Config | completed | TP-029 step 1 | T31.1 | — | EV-002 | F28, F29 |
| T31.5 | Deploy: redeploy internal-write-api (new endpoints) | Config | completed | TP-029 step 2 | T31.4 | — | EV-002 | F25–F29 |
| T31.6 | Deploy: redeploy chat-rag-backend (stats POST integration) | Config | completed | TP-029 step 3 | T31.5 | — | EV-002 | F28 |
| T31.7 | Deploy: redeploy admin frontend (full UI overhaul) | Config | completed | TP-029 step 4 | T31.6 | — | EV-002 | F23–F29 |
| T31.8 | Run H1–H5 staging validation | Config | completed | 13-deploy-smoke | T31.7 | — | EV-002 | F23–F29 |

#### Phase 8 Gate Check

- [x] All M30–M31 tasks completed (184/184)
- [x] Staging deploy successful; H1–H5 passing (2026-05-27)
- [x] Audit retention cleanup verified (cleanup_audit_log function deployed)
- [x] OpenAPI spec matches deployed routes (v0.3.0 updated)
- [x] No new cloud cost (same DO internal-write-api; audit retention runs on existing infra)

---

### Phase 9: EV-004 — Shared frontend i18n/UI + admin bilingual (F31)

**Objective**: Workspace packages `frontend-i18n` + `frontend-ui`; ChatRAG full Tailwind migration;
admin bilingual UI chrome; CI workspace wiring; frontend-only deploy.
**Entry gate**: EV-004 04-tech-plan approved (ADR-021, TP-030–TP-039).
**Exit gate**: Both frontends deployed; H4/H5 regression pass; AC-F1–AC-F7 met; UJ-022 Vitest green.

**Evolve cycle:** EV-004 | **Feature IDs:** F31 | **Branch:** `fix/es-en-full-ui` (TP-030)

#### M32: Workspace scaffold — npm workspaces

**Goal**: Root workspace config; package scaffolds; import resolution smoke tests.
**Acceptance**: Both apps resolve `vecinita-frontend-i18n` and `vecinita-frontend-ui` imports.

| # | Task | Type | Status | Spec Source | Depends On | Data Deps | evolve_cycle_id | feature_ids |
|---|------|------|--------|-------------|------------|-----------|-----------------|-------------|
| T32.1 | Test: `frontend-i18n` strict `t()` keys (package Vitest TC-067) — red | Test | completed | test-plan TC-067, ADR-021 TP-032 | — | D10 | EV-004 | F31 |
| T32.2 | Config: root `package.json` npm workspaces (`apps/*`, `packages/frontend-*`) | Config | completed | ADR-021 TP-035, dependency-inventory | — | — | EV-004 | F31 |
| T32.3 | Config: scaffold `packages/frontend-i18n` + `packages/frontend-ui` (package.json, tsconfig, vitest) | Config | completed | spec.md §Frontend i18n/UI, ADR-019/020 | T32.2 | — | EV-004 | F31 |
| T32.4 | Test: workspace import resolution from both apps (smoke Vitest) | Test | completed | test-plan §EV-004 CI note | T32.3 | — | EV-004 | F31 |

#### M33: frontend-i18n package

**Goal**: Pure TS locale utils + typed EN/ES message tables (`chat.*`, `admin.*`, `shared.*`).
**Acceptance**: TC-067 green; ChatRAG strings migrated from app-local `messages.ts`.

| # | Task | Type | Status | Spec Source | Depends On | Data Deps | evolve_cycle_id | feature_ids |
|---|------|------|--------|-------------|------------|-----------|-----------------|-------------|
| T33.1 | Test: `detectBrowserLocale`, `readStoredLocale`, `LOCALE_STORAGE_KEY` (TC-066 partial) — red | Test | pending | test-plan TC-066, config-spec §Browser locale | T32.1 | D10 | EV-004 | F31 |
| T33.2 | Code: implement `frontend-i18n` — `Locale`, storage, `t()`, message map | Code | pending | ADR-019, ADR-021 TP-032/TP-034 | T33.1 | D10 | EV-004 | F31 |
| T33.3 | Test: admin message key samples per page namespace | Test | pending | feature-list F31, UJ-022 | T33.2 | D10 | EV-004 | F31 |
| T33.4 | Code: migrate ChatRAG strings from `apps/chat-rag-frontend/src/i18n/messages.ts` | Code | pending | ADR-019, TC-069 | T33.2 | D10 | EV-004 | F31 |
| T33.5 | Docs: verify `dependency-inventory.md` workspace package entries | Docs | pending | dependency-inventory §EV-004 | T33.4 | — | EV-004 | F31 |

#### M34: frontend-ui shared components

**Goal**: React + Tailwind shared components per ADR-020; package Vitest with Tailwind.
**Acceptance**: TC-068 green for all exported components.

| # | Task | Type | Status | Spec Source | Depends On | Data Deps | evolve_cycle_id | feature_ids |
|---|------|------|--------|-------------|------------|-----------|-----------------|-------------|
| T34.1 | Test: `LocaleProvider` + `LanguageToggle` (TC-068) — red | Test | pending | test-plan TC-068, UJ-022 | T33.2 | D11 | EV-004 | F31 |
| T34.2 | Code: `LocaleProvider`, `useLocale`, `document.documentElement.lang` sync | Code | pending | ADR-020, config-spec §Browser locale | T34.1 | D11 | EV-004 | F31 |
| T34.3 | Code: `LanguageToggle` — accessible EN/ES pill (`role="group"`) | Code | pending | ADR-020, RD-061 | T34.2 | D11 | EV-004 | F31 |
| T34.4 | Code: `ThemeToggle`, `TagBadge`, `PaginationControls`, `TagFilterChips` | Code | pending | ADR-020 TP-036, RD-067 | T34.2 | D11 | EV-004 | F31 |
| T34.5 | Config: minimal shadcn re-exports in `frontend-ui` (Button, Badge, Input, Label, Dialog) | Config | pending | ADR-020 RD-060 | T34.4 | D11 | EV-004 | F31 |
| T34.6 | Config: `frontend-ui` Vitest + Tailwind/PostCSS test environment | Config | pending | test-plan TC-068, ADR-021 TP-031 | T34.5 | D11 | EV-004 | F31 |
| T34.7 | Test: `ThemeToggle`, `PaginationControls`, `TagBadge` render (TC-068) | Test | pending | test-plan TC-068 | T34.6 | D11 | EV-004 | F31 |

#### M35: ChatRAG migration — Tailwind + shared packages

**Goal**: Full ChatRAG layout Tailwind migration; remove app-local i18n/components.
**Acceptance**: TC-069 green; all chat-rag-frontend Vitest pass including language-toggle bug test.

| # | Task | Type | Status | Spec Source | Depends On | Data Deps | evolve_cycle_id | feature_ids |
|---|------|------|--------|-------------|------------|-----------|-----------------|-------------|
| T35.1 | Test: migrated TC-069 + `test_bug_2026_06_05_language_toggle_i18n` against shared imports — red | Test | pending | test-plan TC-069, UJ-022 | T34.3, T33.4 | — | EV-004 | F31 |
| T35.2 | Config: Tailwind v3 + PostCSS in chat-rag-frontend; content paths include `packages/frontend-ui` | Config | pending | ADR-021 TP-033/TP-031, RD-056 | T32.3 | — | EV-004 | F31 |
| T35.3 | Code: migrate `App.css` layout to Tailwind utilities | Code | pending | ADR-020, RD-056 | T35.2 | — | EV-004 | F31 |
| T35.4 | Code: replace app-local `LocaleContext`, `LanguageToggle`, `messages.ts` with shared packages | Code | pending | ADR-019, TP-030 | T35.1, T34.3 | — | EV-004 | F31 |
| T35.5 | Code: replace app-local `TagFilterChips` with `frontend-ui` import | Code | pending | ADR-020 | T34.4, T35.3 | — | EV-004 | F31 |
| T35.6 | Test: full chat-rag-frontend Vitest suite green | Test | pending | test-plan §Frontend | T35.4, T35.5 | — | EV-004 | F31 |

#### M36: Admin bilingual UI

**Goal**: All admin static strings EN/ES; sidebar language toggle; Intl timestamps.
**Acceptance**: TC-065–TC-071 green; AC-F1, AC-F4, AC-F5.

| # | Task | Type | Status | Spec Source | Depends On | Data Deps | evolve_cycle_id | feature_ids |
|---|------|------|--------|-------------|------------|-----------|-----------------|-------------|
| T36.1 | Test: admin language toggle (`test_admin_language_toggle_i18n.test.tsx` TC-065) — red | Test | pending | test-plan TC-065, UJ-022 | T34.3 | — | EV-004 | F31 |
| T36.2 | Code: wrap admin in `LocaleProvider`; sidebar `LanguageToggle` beside `ThemeToggle` | Code | pending | UJ-022, RD-061 | T36.1 | — | EV-004 | F31 |
| T36.3 | Code: translate `AdminLayout` nav + mobile sheet strings | Code | pending | feature-list F31, ADR-021 TP-037 | T36.2 | D10 | EV-004 | F31 |
| T36.4 | Code: translate `DashboardPage` + `CorpusPage` static strings | Code | pending | ADR-021 TP-037 | T36.3 | D10 | EV-004 | F31 |
| T36.5 | Code: translate `HealthPage` + `AuditPage` static strings | Code | pending | ADR-021 TP-037 | T36.3 | D10 | EV-004 | F31 |
| T36.6 | Code: translate bulk dialogs, `JobForm`, `DocumentAdmin`, `CorpusList` | Code | pending | ADR-021 TP-037 | T36.3 | D10 | EV-004 | F31 |
| T36.7 | Code: `Intl` timestamp/date formatting per UI locale (AC-F4) | Code | pending | config-spec §Date/time, RD-059 | T36.4, T36.5 | — | EV-004 | F31 |
| T36.9 | Test: Intl timestamp formatting per active locale (TC-070, AC-F4) — red | Test | pending | test-plan TC-070 | T36.7 | — | EV-004 | F31 |
| T36.10 | Test: R30 boundary — corpus/tag/API content untranslated (TC-071, AC-F5) — red | Test | pending | test-plan TC-071 | T36.6 | — | EV-004 | F31 |
| T36.8 | Test: TC-066 cross-app locale persistence + admin Vitest suite green | Test | pending | test-plan TC-066 | T36.6, T36.7, T36.9, T36.10 | — | EV-004 | F31 |

#### M37: CI workspace integration

**Goal**: CI installs workspaces from root; both frontends build with shared packages.
**Acceptance**: `ci.yml` frontend matrix green on EV-004 branch.

| # | Task | Type | Status | Spec Source | Depends On | Data Deps | evolve_cycle_id | feature_ids |
|---|------|------|--------|-------------|------------|-----------|-----------------|-------------|
| T37.1 | Config: `ci.yml` — root `npm ci` + workspace-aware frontend matrix | Config | pending | ADR-021 TP-035, test-plan §EV-004 CI | T32.2, T35.6, T36.8 | — | EV-004 | F31 |
| T37.2 | Config: Vite `resolve.alias` + tsconfig `paths` in both frontends | Config | pending | ADR-021 TP-031 | T32.3 | — | EV-004 | F31 |
| T37.3 | Test: root workspace `npm test` / Makefile target for local parity | Test | pending | ci-after-push.mdc | T37.1, T37.2 | — | EV-004 | F31 |

#### M38: EV-004 deploy + connectivity

**Goal**: Deploy both frontends; H4/H5 regression; no backend redeploy.
**Acceptance**: AC-F6, AC-F7; deployment-integration §EV-004.

| # | Task | Type | Status | Spec Source | Depends On | Data Deps | evolve_cycle_id | feature_ids |
|---|------|------|--------|-------------|------------|-----------|-----------------|-------------|
| T38.1 | Test: extend `tests/smoke/test_staging_connectivity.py` — H4/H5 both frontends (AC-F7) | Test | pending | test-plan AC-F7, ADR-021 TP-039 | T37.3 | — | EV-004 | F31 |
| T38.2 | Config: extend `scripts/deploy/verify_connectivity.sh` for EV-004 frontend URLs | Config | pending | connectivity-gates, TP-039 | T38.1 | — | EV-004 | F31 |
| T38.3 | Config: deploy chat-rag-frontend + data-management-frontend (simultaneous per TP-038) | Config | pending | deployment-integration §EV-004, TP-038 | T36.8, T35.6 | — | EV-004 | F31 |
| T38.4 | Config: H1–H5 staging validation post-deploy | Config | pending | 13-deploy-smoke, AC-F7 | T38.3 | — | EV-004 | F31 |

#### Phase 9 Gate Check

- [ ] All M32–M38 tasks completed (222/222)
- [ ] Both frontends deployed; H4/H5 regression pass (AC-F7)
- [ ] No backend/API/Modal redeploy required (AC-F6)
- [ ] ChatRAG app-local i18n removed; shared packages consumed (AC-F3)
- [ ] Admin ~120+ static strings translated EN/ES (AC-F1)
- [ ] `vecinita.locale` shared across frontends (AC-F2)
- [ ] CI frontend matrix uses root npm workspaces (TP-035)

---

### Phase 10: S003 — Browser-local persistent chat history (F33)

**Objective**: `localStorage`-backed conversation store (ADR-025; originally `sessionStorage`
per ADR-023/024); rehydrate the active conversation across refresh/tab-away/tab-close/new-tab;
previous-chats list with new-chat / select / delete / clear; EN/ES i18n; graceful in-memory
fallback. **Frontend-only** in `apps/chat-rag-frontend`.
**Entry gate**: S003 01-requirements complete (F33, ADR-023); 04-tech-plan approved
(ADR-024, TP-S003-01–12).
**Exit gate**: AC-S1–AC-S7 met; TC-072–TC-076 green; UJ-024/UJ-025 covered; full
chat-rag-frontend Vitest suite green; **no API/contract/CORS changes** (AC-S7).

**Session:** S003 (evolve-lite) | **Feature IDs:** F33 | **Branch:** `feat/S003-persistent-chat-history` (TP-S003-04, off `main`)

#### M39: Conversation store — sessionStorage persistence layer

**Goal**: `useConversationStore` — active + previous list, versioned envelope serialize/
deserialize (`vecinita.chat.history.v1`), cap/eviction, graceful fallback.
**Acceptance**: TC-072 (rehydrate), TC-073 (fallback), TC-075 (cap/FIFO) green at hook level.

| # | Task | Type | Status | Spec Source | Depends On | Data Deps | session_id | feature_ids |
|---|------|------|--------|-------------|------------|-----------|------------|-------------|
| T39.1 | Test: store rehydrates active conversation (+sources) from `sessionStorage` after remount (TC-072) — red | Test | completed | test-plan TC-072, ADR-024 | — | — | S003 | F33 |
| T39.2 | Test: graceful fallback to in-memory when `sessionStorage` throws (TC-073) — red | Test | completed | test-plan TC-073, AC-S2 | — | — | S003 | F33 |
| T39.3 | Code: implement `useConversationStore` — envelope schema v1, write-through, try/catch in-memory fallback | Code | completed | ADR-024 TP-S003-01/09/10 | T39.1, T39.2 | — | S003 | F33 |
| T39.4 | Test: cap=10 FIFO eviction at store level (TC-075) — red | Test | completed | test-plan TC-075, RD-070 | T39.3 | — | S003 | F33 |
| T39.5 | Code: store ops — `newChat`/`selectConversation`/`deleteConversation`/`clearAll` + cap/eviction | Code | completed | ADR-024 TP-S003-06/07/08 | T39.4 | — | S003 | F33 |

#### M40: Wire store into shell + active-conversation rehydration

**Goal**: `AppContent` owns the store; `useChatHistory` reads/writes the active slice through
it; rehydrate on mount; preserve Chat ⇄ Corpus state guard (#53).
**Acceptance**: TC-072 at App level (real `App` remount); #53 navigation guard still green.

| # | Task | Type | Status | Spec Source | Depends On | Data Deps | session_id | feature_ids |
|---|------|------|--------|-------------|------------|-----------|------------|-------------|
| T40.1 | Test: real `App` remount rehydrates conversation + sources in order (TC-072, UJ-024) — red | Test | completed | test-plan TC-072, UJ-024 | T39.5 | — | S003 | F33 |
| T40.2 | Code: refactor `useChatHistory` to back onto store active slice (keep public shape + `loading`) | Code | completed | ADR-024 TP-S003-02 | T40.1 | — | S003 | F33 |
| T40.3 | Code: wire store in `AppContent`; pass through to `ChatPanel`; preserve #53 lifting | Code | completed | ADR-024, frontend-session-state-lifting.mdc | T40.2 | — | S003 | F33 |
| T40.4 | Test: regression — Chat ⇄ Corpus navigation state-loss guard (#53) still passes | Test | completed | `test_bug_2026_06_25_chat_corpus_tab_state_loss` | T40.3 | — | S003 | F33 |

#### M41: Previous-chats list UI + new-chat / select / delete / clear

**Goal**: collapsible previous-chats panel in `ChatPanel`; New chat, select-to-restore,
per-item delete, clear-all, clear; labels (first msg ≤60 chars + relative ts); EN/ES i18n.
**Acceptance**: TC-074, TC-076 green; AC-S3, AC-S5.

| # | Task | Type | Status | Spec Source | Depends On | Data Deps | session_id | feature_ids |
|---|------|------|--------|-------------|------------|-----------|------------|-------------|
| T41.1 | Test: "New chat" archives active to list (label = first msg + relative ts) + empties active (TC-074, UJ-025) — red | Test | completed | test-plan TC-074, RD-069/071 | T40.4 | — | S003 | F33 |
| T41.2 | Code: i18n keys (`newChat`, `previousChats`, `clearAllHistory`, `deleteConversation`, `noPreviousChats`) EN/ES in app-local `messages.ts` | Code | completed | TP-S003-04, feature-list F33 | T41.1 | — | S003 | F33 |
| T41.3 | Code: `PreviousChatsList` collapsible panel in `ChatPanel`; label truncation (60) + `Intl.RelativeTimeFormat` | Code | completed | ADR-024 TP-S003-03/05 | T41.2 | — | S003 | F33 |
| T41.4 | Code: New-chat button + clear / clear-all / per-item delete wired to store ops | Code | completed | ADR-024 TP-S003-08, RD-072 | T41.3 | — | S003 | F33 |
| T41.5 | Test: select restores; per-item delete; clear-all; clear active (TC-076, R47) — red→green | Test | completed | test-plan TC-076, AC-S5 | T41.4 | — | S003 | F33 |

#### M42: Rule update, privacy verification, full suite

**Goal**: amend session-state-lifting rule; assert no network/storage leakage; full
chat-rag-frontend Vitest suite green.
**Acceptance**: AC-S6 (no server/DB/log), AC-S7 (no API/CORS), full suite green.

| # | Task | Type | Status | Spec Source | Depends On | Data Deps | session_id | feature_ids |
|---|------|------|--------|-------------|------------|-----------|------------|-------------|
| T42.1 | Config: verify `.cursor/rules/frontend-session-state-lifting.mdc` device-only `sessionStorage` allowance (updated in 04-tech-plan) + its `test_chat_history_persistence` regression-guard reference resolves | Config | completed | TP-S003-11, ADR-024 | T41.5 | — | S003 | F33 |
| T42.2 | Test: AC-S6 — no `POST` carries history; no server session/message row; persistence per-tab | Test | completed | acceptance-criteria AC-S6, ADR-023 | T41.5 | — | S003 | F33 |
| T42.3 | Test: full chat-rag-frontend Vitest suite green incl. existing bug tests | Test | completed | test-plan §Frontend | T41.5, T40.4, T42.2 | — | S003 | F33 |

#### Phase 10 Gate Check

- [x] All M39–M42 tasks completed (239/239)
- [x] TC-072–TC-076 green; UJ-024/UJ-025 covered (Vitest + jsdom `sessionStorage`)
- [x] AC-S1–AC-S7 met
- [x] Graceful fallback verified (TC-073, AC-S2)
- [x] `.cursor/rules/frontend-session-state-lifting.mdc` updated (ADR-023/024)
- [x] No API/contract/CORS changes (AC-S7); no backend/Modal redeploy
- [x] chat-rag-frontend Vitest suite green (incl. #53 navigation guard)

**Phase Gate Log — Phase 10 (2026-06-26):** PASS. M39–M42 complete (T39.1–T42.3).
115 chat-rag-frontend Vitest tests pass; 95% line/branch coverage gate green;
`tsc --noEmit` + ESLint clean; production `vite build` succeeds. TC-072–TC-076,
UJ-024/UJ-025, AC-S1–AC-S7 satisfied; #53 + mid-stream concurrency guards still
green. Frontend-only — no API/contract/CORS or backend/Modal changes (AC-S7).

**Amendment — 2026-06-28 (07-build reopened, ADR-025):** Storage mechanism switched
`sessionStorage` → `localStorage` (durable, cross-tab) at user request. Re-verified:
116 chat-rag-frontend Vitest tests pass; 95% coverage gate green; `tsc --noEmit` +
ESLint clean; `vite build` succeeds. AC-S1/AC-S2/AC-S5/AC-S6 wording updated; still
frontend-only, no API/contract/CORS or backend/Modal changes (AC-S7).

---

### Phase 11: EV-005 — Supabase admin auth (F34)

**Objective**: Add a Supabase-Auth authentication interface for **admin surfaces only** — DM UI,
DM API (Modal `/jobs*`), and internal-write API require a valid Supabase JWT; **ChatRAG stays
anonymous**. Invite-only registration; `admin` + `viewer` roles; identity in Supabase (corpus DB
PII-free); env-sync via Supabase branching + migrations-in-repo. Reverses ADR-004's auth clause for
admin surfaces (ADR-026) and applies the 04-tech-plan tech decisions (ADR-027, TP-S004-01–12).
**Entry gate**: S004 01-requirements complete (F34, ADR-026); 04-tech-plan approved
(ADR-027, TP-S004-01–12). evolve-lite (02/03/05/06/11 skipped).
**Exit gate**: AC-A1–AC-A10 met; TC-077–TC-086 green; UJ-026–UJ-029 covered; privacy tests
(no corpus identity tables; `actor_id` UUID + no PII) green; ChatRAG strict CORS (H0c); full
backend + DM-frontend suites green; OpenAPI `securitySchemes` updated.

**Session:** S004 (evolve-lite) | **Feature IDs:** F34 | **Branch:** `feat/S004-supabase-auth` (TP-S004-12, off `main`)

> Mechanism (TP-S004): HS256 verify with `SUPABASE_JWT_SECRET`; role from `app_metadata.role`;
> shared verifier `vecinita_shared_schemas.auth`; PyJWT `>=2.10,<3`; `@supabase/supabase-js ^2.108.2`.

#### M43: Supabase project + env-sync scaffolding (CLI/branching, invites, bootstrap)

**Goal**: Repo-managed Supabase config: `supabase/` (CLI `config.toml`) with **public sign-up
disabled** + invite/SMTP settings; migrations-in-repo + branching workflow docs; idempotent
first-admin seed script; secrets matrix + operator runbook. **No app runtime code.**
**Acceptance**: `supabase` config asserts signup disabled; seed script idempotent (mocked admin
API); secrets matrix + runbook updated; AC-A10 plan in place.

| # | Task | Type | Status | Spec Source | Depends On | Data Deps | session_id | feature_ids |
|---|------|------|--------|-------------|------------|-----------|------------|-------------|
| T43.1 | Config: `supabase/config.toml` via Supabase CLI — disable public sign-up, enable invite flow, custom-SMTP placeholders; document branching (ephemeral previews) | Config | pending | ADR-027 §6/§7, TP-S004-07/08 | — | — | S004 | F34 |
| T43.2 | Test: first-admin seed script idempotent + sets `app_metadata.role=admin` (mocked admin API) — red | Test | pending | ADR-027 §8, TP-S004-10 | — | — | S004 | F34 |
| T43.3 | Code: `scripts/seed_first_admin.py` using `SUPABASE_SECRET_KEY` (idempotent; reads `SUPABASE_ADMIN_EMAIL/_PASSWORD`) | Code | pending | ADR-027 §8 | T43.2 | — | S004 | F34 |
| T43.4 | Docs: `docs/staging-secrets-matrix.md` + operator runbook — `SUPABASE_JWT_SECRET`, `SUPABASE_URL`, `SUPABASE_SECRET_KEY`, `VITE_SUPABASE_*`, invite/disable/role-change, JWT-secret rotation, branch cleanup (AC-A10) | Docs | pending | config-spec §Admin auth, AC-A10 | T43.1 | — | S004 | F34 |
| T43.5 | CI: `.github/workflows/supabase.yml` — offline validate + gated preview/sync (ADR-027 §6); `scripts/check_supabase_config.sh`; TC-087 | Config | completed | ADR-027 §6, test-plan TC-087 | T43.1 | — | S004 | F34 | 2026-06-29 |

#### M44: Shared JWT verifier — `vecinita_shared_schemas.auth`

**Goal**: HS256 verifier + FastAPI dependencies in `packages/shared-schemas`; principal = opaque
Supabase `sub` UUID + `app_metadata.role`; `require_role("admin")`.
**Acceptance**: TC-077 (valid admin authorizes), TC-078 (missing/invalid/expired → 401), role
extraction unit-tested; basedpyright/ruff clean (no `Any`, ADR-018).

| # | Task | Type | Status | Spec Source | Depends On | Data Deps | session_id | feature_ids |
|---|------|------|--------|-------------|------------|-----------|------------|-------------|
| T44.1 | Test: verify valid HS256 token → principal(sub UUID, role) (TC-077); reject missing/invalid/expired/wrong-`aud` → 401 (TC-078) — red | Test | pending | test-plan TC-077/078, ADR-027 §1 | — | — | S004 | F34 |
| T44.2 | Code: `vecinita_shared_schemas.auth` — `verify_supabase_jwt()` (PyJWT HS256, exp+aud), `get_principal` + `require_role(...)` FastAPI deps; `VECINITA_AUTH_REQUIRED` toggle | Code | pending | ADR-027 §1/§3, config-spec | T44.1 | — | S004 | F34 |
| T44.3 | Test: role gating helper — `viewer` denied, `admin` allowed (TC-079 unit level) — red→green | Test | pending | test-plan TC-079, RD-075 | T44.2 | — | S004 | F34 |
| T44.4 | Config: add **PyJWT `>=2.10,<3`** to `packages/shared-schemas` deps (TP-S004-04) | Config | pending | dependency-inventory §EV-005 | T44.2 | — | S004 | F34 |

#### M45: Backend enforcement — DM API + internal-write API + audit attribution

**Goal**: Apply the verifier as a dependency on DM Modal `/jobs*` (alongside `X-Vecinita-Proxy-Key`)
and internal-write `/internal/v1/*` (JWT operator **or** `VECINITA_INTERNAL_API_KEY` service key);
writes require `admin`; record non-PII `actor_id`/`actor_role`; tighten ChatRAG CORS.
**Acceptance**: TC-077/078/079/081/083 green; Alembic migration adds `actor_id`+`actor_role`;
TC-082 (ChatRAG strict CORS) at H0c.

| # | Task | Type | Status | Spec Source | Depends On | Data Deps | session_id | feature_ids |
|---|------|------|--------|-------------|------------|-----------|------------|-------------|
| T45.1 | Test (TestClient): DM `/jobs*` + internal-write routes reject no/invalid JWT → 401 (TC-078, UJ-028); ChatRAG stays anonymous (TC-083) — red | Test | pending | test-plan TC-078/083, UJ-028 | T44.2 | — | S004 | F34 |
| T45.2 | Code: add JWT dependency to DM backend `/jobs*` (keep proxy header) and internal-write `/internal/v1/*` (JWT operator OR service API key) | Code | pending | ADR-027 §5, TP-S004-05/09 | T45.1 | — | S004 | F34 |
| T45.3 | Test: `viewer` → 403 on write routes; `admin` → success (TC-079, UJ-029) — red | Test | pending | test-plan TC-079, AC-A3 | T45.2 | — | S004 | F34 |
| T45.4 | Code: enforce `require_role("admin")` on write methods (POST/PATCH/DELETE) across internal-write routes | Code | pending | ADR-027 §2/§5 | T45.3 | D5 | S004 | F34 |
| T45.5 | Test: Alembic migration adds nullable `actor_id` (UUID) + `actor_role`; audit attribution is non-PII (TC-081) — red | Test | pending | test-plan TC-081, ADR-016/027 | T45.2 | D5 | S004 | F34 |
| T45.6 | Code: Alembic migration + write handlers set `actor_id`/`actor_role` from verified principal (no email/name) | Code | pending | ADR-027 §2, ADR-016 | T45.5 | D5 | S004 | F34 |
| T45.7 | Code+Test: tighten ChatRAG `VECINITA_CORS_ORIGINS` to frontend origin only; admin APIs allow `Authorization` header — H0c OPTIONS (TC-082) | Code | pending | config-spec §CORS, RD-079, cors-browser-methods.mdc | T45.2 | — | S004 | F34 |

#### M46: DM frontend auth — login, protected routes, role-gated controls

**Goal**: `@supabase/supabase-js` session; login screen; protected routing; surface current user +
logout; send `Authorization: Bearer` to admin APIs; hide/disable writes for `viewer`.
**Acceptance**: TC-084 (protected route + login), TC-085 (viewer write controls hidden) green
(Vitest); H4 preflight includes `Authorization`.

| # | Task | Type | Status | Spec Source | Depends On | Data Deps | session_id | feature_ids |
|---|------|------|--------|-------------|------------|-----------|------------|-------------|
| T46.1 | Test (Vitest): unauthenticated → redirect to login; renders on session; current-user + logout (TC-084, UJ-026) — red | Test | pending | test-plan TC-084, UJ-026 | — | — | S004 | F34 |
| T46.2 | Config: add **`@supabase/supabase-js ^2.108.2`** to `apps/data-management-frontend`; `VITE_SUPABASE_*` wiring | Config | pending | dependency-inventory §EV-005, config-spec | T46.1 | — | S004 | F34 |
| T46.3 | Code: Supabase client + auth context; Login screen (email+password / invite-accept); ProtectedRoute; current-user + logout in shell | Code | pending | ADR-026/027, UJ-026/027 | T46.2 | — | S004 | F34 |
| T46.4 | Code: attach `Authorization: Bearer <jwt>` to admin API fetches (keep proxy header to DM Modal) | Code | pending | api-contract §Authentication, RD-076 | T46.3 | — | S004 | F34 |
| T46.5 | Test+Code: role-gated controls — hide/disable write actions for `viewer` (TC-085, UJ-029) | Test | pending | test-plan TC-085, AC-A5 | T46.3 | — | S004 | F34 |

#### M47: Integration, privacy, OpenAPI & gate

**Goal**: e2e journeys, invite-only assertion, privacy guarantees, OpenAPI `securitySchemes`,
full-suite + config validation.
**Acceptance**: TC-080/086 green; UJ-026–029 covered; AC-A1–A10 satisfied (A8/A10 verified at
12/13); OpenAPI updated; full backend + DM-frontend suites green.

| # | Task | Type | Status | Spec Source | Depends On | Data Deps | session_id | feature_ids |
|---|------|------|--------|-------------|------------|-----------|------------|-------------|
| T47.1 | Test (e2e): `tests/e2e/test_uj028_unauthenticated_admin.py` (401 across admin APIs; ChatRAG anonymous) — green | Test | completed | test-plan TC-078/083, UJ-028 | T45.2, T45.7 | — | S004 | F34 |
| T47.2 | Test (e2e): `tests/e2e/test_uj027_invite_only_registration.py` — public sign-up disabled / unauthorized (TC-080, UJ-027) | Test | completed | test-plan TC-080, UJ-027 | T43.1 | — | S004 | F34 |
| T47.3 | Test (e2e): `tests/e2e/test_uj029_role_gating.py` — viewer 403 / admin 200; audit actor = opaque UUID + role, no PII (TC-079/081) | Test | completed | test-plan TC-079/081, UJ-029 | T45.4, T45.6 | — | S004 | F34 |
| T47.4 | Test (privacy): extend `tests/privacy/` — no `users`/`profiles`/`auth_*`/identity tables in corpus DB; `actor_id` is UUID, no PII columns (TC-086) | Test | completed | test-plan TC-086, ADR-026/027 | T45.6 | — | S004 | F34 |
| T47.5 | Config: update OpenAPI (`openapi/`, `internal-write-api-spec.yaml`) — `bearerAuth` securityScheme on admin routes; keep `apiKeyAuth` for service calls (no request/response schema changes, AC-A9) | Config | completed | api-contract §Authentication, ADR-011 | T45.2 | — | S004 | F34 |
| T47.6 | Test: full backend (pytest unit/integration/e2e/privacy) + DM-frontend Vitest suites green; config validation for `SUPABASE_*` / `VECINITA_AUTH_REQUIRED` | Test | completed | test-plan, acceptance-criteria AC-A1–A10 | T47.1–T47.5, T46.5 | — | S004 | F34 |

#### Phase 11 Gate Check

- [ ] All M43–M47 tasks completed (T43.1–T47.6)
- [ ] TC-077–TC-086 green; UJ-026–UJ-029 covered
- [ ] AC-A1–AC-A10 satisfied (AC-A8 CORS + AC-A10 env-sync/secrets verified at 12-verify-deploy / 13-deploy-smoke)
- [ ] Privacy: no identity/PII tables in corpus DB; `actor_id` UUID + `actor_role` only (TC-086)
- [ ] ChatRAG remains anonymous; strict CORS to frontend origin only (TC-082/083; H0c, H4 live)
- [ ] OpenAPI `securitySchemes` updated; no request/response schema changes (AC-A9)
- [ ] All Supabase secrets via Modal/DO env, never committed; first-admin seed idempotent
- [x] ruff / basedpyright / ESLint clean; full backend + DM-frontend suites green

---

### Phase 12: EV-006 — Admin user management + auth UX (F35)

**Objective**: Extend F34 admin auth with operator-facing user lifecycle management (invite/list/role/
resend/disable/revoke/reset), remember-me login control, and production email via **Resend SMTP** +
repo-versioned stacked-bilingual templates synced by `supabase config push`. Builds on ADR-029
(product) and ADR-030 (implementation: DM Modal backend, httpx Admin API, audit ingest, lockout
guards).
**Entry gate**: S005 01-requirements complete (F35, ADR-029, RD-080–RD-090); 04-tech-plan approved
(ADR-030, TP-S005-01–16). evolve-lite (02/03/05/06/11 skipped).
**Exit gate**: AC-U1–AC-U9 met; TC-088–TC-095 green; UJ-030–UJ-033 covered; user-mgmt audit rows
in corpus `audit_log` (no PII); Resend SMTP + templates synced on `main`; full backend +
DM-frontend suites green; OpenAPI updated.

**Session:** S005 (evolve-lite) | **Feature IDs:** F35 | **Branch:** `feat/S005-user-mgmt-auth` (TP-S005-14, off `main`)

> Mechanism (TP-S005): `/admin/users*` on **DM Modal ASGI**; **httpx** GoTrue Admin REST;
> `SUPABASE_SECRET_KEY` Modal-only; audit via **POST `/internal/v1/audit/event`**; remember-me via
> `auth.storage` adapter; CLI pin **`>=2.70,<3`**; template paths per #5124.

#### M48: Supabase Resend SMTP + versioned email templates + CI sync

**Goal**: Enable custom SMTP (Resend) in `config.toml`; add six stacked-bilingual HTML templates;
extend offline config contract + pin Supabase CLI; update secrets matrix.
**Acceptance**: TC-094/TC-095 green; `check_supabase_config.sh` validates paths + SMTP contract;
`supabase.yml` uses pinned CLI.

| # | Task | Type | Status | Spec Source | Depends On | Data Deps | session_id | feature_ids |
|---|------|------|--------|-------------|------------|-----------|------------|-------------|
| T48.1 | Test: `scripts/check_supabase_config.sh` asserts Resend SMTP enabled, `env(SUPABASE_SMTP_PASS)`, template `content_path` existence + #5124 convention (TC-094, TC-095) — red | Test | pending | test-plan TC-094/095, ADR-030 §8 | — | — | S005 | F35 |
| T48.2 | Config: `supabase/config.toml` — Resend SMTP (`smtp.resend.com:465`), `[auth.rate_limit] email_sent=30`, `otp_expiry=3600`, `minimum_password_length=8`, template blocks | Config | pending | ADR-029/030, config-spec §EV-006, TP-S005-07/08/11 | T48.1 | — | S005 | F35 |
| T48.3 | Config: `supabase/templates/*.html` — six stacked-bilingual templates (invite, recovery, confirmation, magic_link, email_change, notifications) | Config | pending | ADR-029 RD-086, TP-S005-10 | T48.2 | — | S005 | F35 |
| T48.4 | Config: extend `scripts/check_supabase_config.sh` — path lint per TP-S005-08 | Config | pending | ADR-030 §8, TC-095 | T48.1 | — | S005 | F35 |
| T48.5 | CI: pin Supabase CLI `>=2.70,<3` in `supabase.yml`; extend validate job template checks (TP-S005-09, RD-088) | Config | pending | ADR-027/030, dependency-inventory | T48.4 | — | S005 | F35 |
| T48.6 | Docs: `staging-secrets-matrix.md` EV-006 — `SUPABASE_SMTP_PASS`, Modal `SUPABASE_SECRET_KEY`, Resend operator prerequisites + rotation (TP-S005-16) | Docs | pending | staging-secrets-matrix §EV-006, AC-U9 | T48.2 | — | S005 | F35 |

#### M49: Shared Supabase Admin client + audit ingest + lockout guards

**Goal**: Typed httpx GoTrue Admin client; service-to-service audit ingest on internal-write-api;
last-admin + self-action guards.
**Acceptance**: Admin client unit-tested (mocked httpx); audit ingest route accepts service key;
lockout guards return 409.

| # | Task | Type | Status | Spec Source | Depends On | Data Deps | session_id | feature_ids |
|---|------|------|--------|-------------|------------|-----------|------------|-------------|
| T49.1 | Test: `vecinita_shared_schemas.supabase_admin` — invite/list/update/delete/generate_link (mocked httpx) — red | Test | pending | ADR-030 §2, api-contract §Admin user management | — | — | S005 | F35 |
| T49.2 | Code: `vecinita_shared_schemas.supabase_admin` — httpx GoTrue Admin REST + Pydantic models | Code | pending | ADR-030 §2, TP-S005-02 | T49.1 | — | S005 | F35 |
| T49.3 | Test: `POST /internal/v1/audit/event` — service API key only; writes `audit_log` row (TC-092 partial) — red | Test | pending | ADR-030 §3, RD-089 | — | D5 | S005 | F35 |
| T49.4 | Code: audit ingest route on internal-write-api + `emit_audit_event` reuse | Code | pending | ADR-030 §3, ADR-007 | T49.3 | D5 | S005 | F35 |
| T49.5 | Test: lockout guards — self-delete/disable/demote + last-admin → 409 — red | Test | pending | ADR-030 §4 | T49.2 | — | S005 | F35 |
| T49.6 | Code: `UserAdminService` lockout guard helpers | Code | pending | ADR-030 §4, TP-S005-04 | T49.5 | — | S005 | F35 |

#### M50: DM backend `/admin/users*` routes

**Goal**: Mount admin user-management API on DM Modal ASGI; wire `SUPABASE_SECRET_KEY`; CORS +
invite rate limit.
**Acceptance**: TC-088/089 green (TestClient); CORS H0c for PATCH/DELETE; Modal secret documented.

| # | Task | Type | Status | Spec Source | Depends On | Data Deps | session_id | feature_ids |
|---|------|------|--------|-------------|------------|-----------|------------|-------------|
| T50.1 | Test (TestClient): `/admin/users*` — list, invite, role, resend, disable, enable, delete, reset; viewer → 403 (TC-088, TC-089) — red | Test | completed | test-plan TC-088/089, UJ-030 | T49.2, T49.6 | — | S005 | F35 |
| T50.2 | Code: `/admin/users*` routes on DM backend; admin-only deps; audit emit via write API | Code | completed | api-contract §Admin user management, ADR-030 §1/3 | T50.1, T49.4 | — | S005 | F35 |
| T50.3 | Config: Modal `SUPABASE_SECRET_KEY`; `infra/modal/` + deploy sync scripts | Config | completed | ADR-030 §1, staging-secrets-matrix | T50.2 | — | S005 | F35 |
| T50.4 | Code+Test: CORS preflight PATCH/DELETE/POST on `/admin/users*` (TP-S005-15, cors-browser-methods.mdc) | Code | completed | test-plan, connectivity-gates | T50.2 | — | S005 | F35 |
| T50.5 | Test: invite endpoint app-level rate limit (10/h per admin JWT) — red | Test | completed | ADR-030 §7, TP-S005-07 | T50.2 | — | S005 | F35 |
| T50.6 | Code: sliding-window invite rate limiter on `POST /admin/users/invite` | Code | completed | ADR-030 §7 | T50.5 | — | S005 | F35 |

#### M51: DM frontend — Users page + remember-me + password reset flows

**Goal**: `/users` admin page; remember-me checkbox; forgot/reset/accept-invite routes.
**Acceptance**: TC-091/093 Vitest green; viewer cannot access user mgmt UI (TC-089).

| # | Task | Type | Status | Spec Source | Depends On | Data Deps | session_id | feature_ids |
|---|------|------|--------|-------------|------------|-----------|------------|-------------|
| T51.1 | Test (Vitest): UsersPage — list users, invite form, action buttons (TC-088) — red | Test | completed | test-plan TC-088, UJ-030/031 | — | — | S005 | F35 |
| T51.2 | Test (Vitest): viewer blocked from `/users` nav + API calls (TC-089) — red | Test | completed | test-plan TC-089 | — | — | S005 | F35 |
| T51.3 | Code: `/users` route, sidebar nav, UsersPage (table + invite modal + actions) | Code | completed | ADR-029, user-journeys UJ-030/031 | T51.1, T50.2 | — | S005 | F35 |
| T51.4 | Test (Vitest): remember-me routes session to localStorage vs sessionStorage (TC-091) — red | Test | completed | test-plan TC-091, UJ-032, RD-084 | — | — | S005 | F35 |
| T51.5 | Code: remember-me checkbox; `createRoutingStorage`; `resetSupabaseClient` before sign-in (TP-S005-06) | Code | completed | ADR-029/030 §6 | T51.4 | — | S005 | F35 |
| T51.6 | Test (Vitest): forgot-password + reset-password + accept-invite flows (TC-093) — red | Test | completed | test-plan TC-093, UJ-033, RD-083 | — | — | S005 | F35 |
| T51.7 | Code: `/forgot-password`, `/reset-password`, `/accept-invite` routes + login link | Code | completed | ADR-030 §5, UJ-033 | T51.6 | — | S005 | F35 |

#### M52: Integration, OpenAPI, privacy & gate

**Goal**: E2E journeys, OpenAPI update, full-suite green, operator runbook.
**Acceptance**: TC-088–TC-095 green; UJ-030–033 covered; AC-U1–AC-U9; OpenAPI `data-management.yaml` updated.

| # | Task | Type | Status | Spec Source | Depends On | Data Deps | session_id | feature_ids |
|---|------|------|--------|-------------|------------|-----------|------------|-------------|
| T52.1 | Test (e2e): `tests/e2e/test_uj030_user_management.py` (TC-088, TC-089, TC-092) | Test | completed | test-plan TC-088/089/092, UJ-030 | T50.2, T51.3 | — | S005 | F35 |
| T52.2 | Test (e2e): `tests/e2e/test_uj031_invite_from_page.py` (TC-090) | Test | completed | test-plan TC-090, UJ-031 | T50.2, T51.3 | — | S005 | F35 |
| T52.3 | Test: `tests/smoke/test_supabase_ci_contract.py` extended for TC-094/095 | Test | completed | test-plan TC-094/095 | T48.4 | — | S005 | F35 |
| T52.4 | Config: OpenAPI `openapi/data-management.yaml` — `/admin/users*` paths + schemas | Config | completed | api-contract §Admin user management, ADR-011 | T50.2 | — | S005 | F35 |
| T52.5 | Test: full backend pytest + DM Vitest green; AC-U1–AC-U9 checklist | Test | completed | acceptance-criteria AC-U1–U9 | T52.1–T52.4, T51.5, T51.7 | — | S005 | F35 |
| T52.6 | Docs: operator runbook delta — Resend domain verify, invite/resend workflow, secret rotation | Docs | completed | staging-runbook, TP-S005-16 | T48.6 | — | S005 | F35 |

#### M53: Auth UX hardening — idle timeout, log-out-everywhere, force sign-out, deliverability test-send, audit viewer

**Goal**: The four scope additions (ADR-031, TP-S005-17–24). Builds on M48–M52.
**Acceptance**: TC-096–TC-103 green; UJ-034–UJ-038 covered; AC-U10–AC-U16; OpenAPI updated for the two new routes + `q`.

| # | Task | Type | Status | Spec Source | Depends On | Data Deps | session_id | feature_ids |
|---|------|------|--------|-------------|------------|-----------|------------|-------------|
| T53.1 | Test (Vitest): idle timeout warns + signs out locally; activity resets (TC-096) — red | Test | completed | test-plan TC-096, UJ-034, ADR-031 §17 | — | — | S005 | F35 |
| T53.2 | Code: `useIdleTimeout` + warning modal in always-mounted shell; `VITE_VECINITA_IDLE_TIMEOUT_MIN/_WARNING_SEC` | Code | completed | ADR-031 §17, frontend-session-state-lifting.mdc | T53.1 | — | S005 | F35 |
| T53.3 | Test (Vitest): "log out of all devices" → global `signOut()`; standard logout → local (TC-097) — red | Test | completed | test-plan TC-097, UJ-035 | — | — | S005 | F35 |
| T53.4 | Code: account-menu "Log out of all devices" action (global scope) | Code | completed | ADR-031 §18, UJ-035 | T53.3 | — | S005 | F35 |
| T53.5 | Config: `admin_delete_user_sessions` RPC migration under `supabase/migrations/` + runbook one-time-apply note | Config | completed | ADR-031 §19, staging-secrets-matrix | — | — | S005 | F35 |
| T53.6 | Test (TestClient): `POST /admin/users/{id}/signout` — admin 202 + `user.signed_out` audit; viewer 403; RPC-absent 503 (TC-098) — red | Test | completed | test-plan TC-098, UJ-036 | T49.2, T49.4 | — | S005 | F35 |
| T53.7 | Code: force-signout route (RPC call via service key) + audit emit + lockout-guard parity | Code | completed | ADR-031 §19, api-contract | T53.6, T53.5 | — | S005 | F35 |
| T53.8 | Test (Vitest): Users-page "Force sign-out" row action + 503 disable-fallback (TC-098) — red | Test | completed | test-plan TC-098, UJ-036 | — | 2026-06-30 | S005 | F35 |
| T53.9 | Code: Users-page "Force sign-out" action wired to endpoint | Code | completed | UJ-036, ADR-031 §19 | T53.8, T53.7 | 2026-06-30 | S005 | F35 |
| T53.10 | Test (TestClient): `POST /admin/email/test` — admin 202 + `message_id`; viewer 403; 429; 503 unconfigured; audit domain-only (TC-099) — red | Test | completed | test-plan TC-099, UJ-037 | T50.2 | — | S005 | F35 |
| T53.11 | Code: test-send route via Resend REST (`RESEND_API_KEY`/`RESEND_SENDER_EMAIL`) + 5/h rate limit + audit | Code | completed | ADR-031 §22, api-contract | T53.10 | — | S005 | F35 |
| T53.12 | Test (Vitest): "Send test email" UI → endpoint; success/`503` checklist link (TC-099) — red | Test | completed | test-plan TC-099, UJ-037 | — | 2026-06-30 | S005 | F35 |
| T53.13 | Code: "Send test email" UI control | Code | completed | UJ-037, ADR-031 §22 | T53.12, T53.11 | 2026-06-30 | S005 | F35 |
| T53.14 | Test (backend + Vitest): `GET /admin/users?q=` ≥3-char guard → GoTrue `filter`; pagination (TC-100) — red | Test | completed | test-plan TC-100, UJ-030, ADR-031 §20 | T49.2 | 2026-06-30 | S005 | F35 |
| T53.15 | Code: `q` param on `/admin/users` + search box + shared `PaginationControls` on Users page | Code | completed | ADR-031 §20, api-contract | T53.14, T50.2, T51.3 | 2026-06-30 | S005 | F35 |
| T53.16 | Test (Vitest): AuditPage `entity_type` "Users" filter + `user.*`/`email.*` labels + per-user link (TC-101) — red | Test | completed | test-plan TC-101, UJ-038, ADR-031 §21 | — | 2026-06-30 | S005 | F35 |
| T53.17 | Code: AuditPage entity-type filter + i18n labels (EN/ES) + Users-row "View activity" link; ensure events emit `entity_type="user"` | Code | completed | ADR-031 §21, F29 AuditPage | T53.16, T50.2 | 2026-06-30 | S005 | F35 |
| T53.18 | Test: privacy — idle/remember/log-out-everywhere send nothing extra to server (TC-102); CORS+audit parity for new routes (TC-103) — red | Test | completed | test-plan TC-102/103, ADR-026 | T53.7, T53.11 | 2026-06-30 | S005 | F35 |
| T53.19 | Code+Test: CORS preflight POST on `/admin/users/{id}/signout` + `/admin/email/test` (cors-browser-methods.mdc) | Code | completed | test-plan TC-103, connectivity-gates | T53.7, T53.11 | 2026-06-30 | S005 | F35 |
| T53.20 | Test (e2e): `tests/e2e/test_uj036_force_signout.py`, `tests/e2e/test_uj037_email_test_send.py` | Test | completed | test-plan TC-098/099 | T53.7, T53.11 | 2026-06-30 | S005 | F35 |
| T53.21 | Config: OpenAPI `openapi/data-management.yaml` — `/signout`, `/admin/email/test`, `q` param | Config | completed | api-contract, ADR-011 | T53.7, T53.11, T53.15 | 2026-06-30 | S005 | F35 |
| T53.22 | Docs: staging runbook — SPF/DKIM/DMARC checklist, force-signout RPC apply, test-send workflow; AC-U10–U16 checklist | Docs | completed | staging-runbook, TP-S005-23, ADR-031 | T53.5 | 2026-06-30 | S005 | F35 |

#### Phase 12 Gate Check

- [x] All M48–M53 tasks completed (T48.1–T53.22)
- [x] TC-088–TC-103 green; UJ-030–UJ-038 covered (unit + frontend suites green at close-out; integration/e2e green at 08-verify-build interim)
- [ ] AC-U1–AC-U16 satisfied (live Resend delivery + test-send verified at 13-deploy-smoke) — **deferred to 13**
- [ ] User-mgmt audit rows in corpus `audit_log` with UUID `actor_id` only, `entity_type="user"` (TC-092, TC-101) — **live-verified at 13**; covered by tests at build
- [ ] `SUPABASE_SECRET_KEY` + `RESEND_API_KEY`/`RESEND_SENDER_EMAIL` on Modal DM only; never in browser or internal-write-api — **deploy-config, verified at 12/13**
- [ ] Resend SMTP + templates synced via `supabase config push` on `main`; SPF/DKIM/DMARC documented — **deploy-time at 13** (checklist in staging runbook, T53.22)
- [x] CORS preflight covers PATCH/DELETE/POST on `/admin/users*`, `/admin/users/{id}/signout`, `/admin/email/test` (T53.19, TC-103)
- [x] Idle timeout / remember-me / log-out-everywhere send nothing extra to the server (TC-102)
- [x] `admin_delete_user_sessions` RPC apply documented; `503` fallback path covered (TC-098, T53.22)
- [x] ruff / basedpyright / ESLint clean; full backend + DM-frontend suites green (`make check` PASS; 496 unit + frontend suites green 2026-06-30)

### Phase 13: EV-007 — Invite acceptance flow (F35 ext, #109)

> **Session:** S006-invite-acceptance · **Evolve cycle:** EV-007 · **Feature IDs:** F35.12–F35.15  
> **ADR:** ADR-032 · **Branch:** `feat/S006-invite-acceptance` · **PR:** PR-49

Closes the production onboarding gap: backend `redirect_to`, Supabase redirect config,
frontend auth callback, retract invitation, template polish, live invite smoke (T3).

#### M54: Supabase redirect config + admin frontend URL env

| Task | Description | Type | Status | Spec Source | Depends On | Completed | Session | Feature |
|------|-------------|------|--------|-------------|------------|-----------|---------|---------|
| T54.1 | Test (smoke): TC-109 — `config.toml` staging-first `site_url` + full-path `additional_redirect_urls` — red | Test | completed | test-plan TC-109, ADR-032 §4 | — | 2026-06-30 | S006 | F35 |
| T54.2 | Config: Update `supabase/config.toml` — staging admin `site_url`, redirect allowlist with `/accept-invite` + `/reset-password` paths + local dev origins | Config | completed | ADR-032 §4, deployment-integration §EV-007 | T54.1 | 2026-06-30 | S006 | F35 |
| T54.3 | Test (unit): `AdminRedirectConfig` / redirect URL builder — env unset → error; valid origin → correct paths — red | Test | completed | ADR-032 §2–3, config-spec | — | 2026-06-30 | S006 | F35 |
| T54.4 | Config: Wire `VECINITA_ADMIN_FRONTEND_URL` on Modal DM backend + extend `scripts/check_secrets.sh` / staging-secrets-matrix | Config | completed | ADR-032 §2, staging-secrets-matrix §EV-007 | T54.3 | 2026-06-30 | S006 | F35 |

#### M55: Backend redirect_to + revoke-invite

| Task | Description | Type | Status | Spec Source | Depends On | Completed | Session | Feature |
|------|-------------|------|--------|-------------|------------|-----------|---------|---------|
| T54.5 | Test (TestClient): TC-104 — invite + resend include `redirect_to={origin}/accept-invite` on GoTrue outbound — red | Test | completed | test-plan TC-104, UJ-031, ADR-032 §3 | T54.4 | 2026-06-30 | S006 | F35 |
| T54.6 | Test (TestClient): TC-105 — admin recovery includes `redirect_to={origin}/reset-password` — red | Test | completed | test-plan TC-105, UJ-033, ADR-032 §3 | T54.4 | 2026-06-30 | S006 | F35 |
| T54.7 | Test (TestClient): TC-108 — `POST /admin/users/{id}/revoke-invite` invited-only + `user.invite_revoked` audit; active → 409 — red | Test | completed | test-plan TC-108, UJ-030, ADR-032 §7 | T49.2 | 2026-06-30 | S006 | F35 |
| T54.8 | Code: `build_auth_redirect_path` helper + wire invite/resend/recovery routes with `redirect_to` | Code | completed | ADR-032 §3, api-contract | T54.5, T54.6 | 2026-06-30 | S006 | F35 |
| T54.9 | Code: `POST /admin/users/{id}/revoke-invite` route + invited-only guard + audit emit | Code | completed | ADR-032 §7, api-contract | T54.7 | 2026-06-30 | S006 | F35 |
| T54.10 | Test (unit): `supabase_admin` asserts `redirect_to` query param on httpx outbound invite/recovery — red | Test | completed | test-plan TC-104/105, ADR-032 §3 | — | 2026-06-30 | S006 | F35 |
| T54.11 | Code: Implement `redirect_to` passthrough in `supabase_admin` call sites (if test-only gap) | Code | completed | ADR-032 §3 | T54.10, T54.8 | 2026-06-30 | S006 | F35 |

#### M56: Frontend auth callback pages

| Task | Description | Type | Status | Spec Source | Depends On | Completed | Session | Feature |
|------|-------------|------|--------|-------------|------------|-----------|---------|---------|
| T54.12 | Test (Vitest): TC-106 — accept-invite hash/code session bootstrap, `#error=otp_expired` UX, form gated on session — red | Test | completed | test-plan TC-106, UJ-031, ADR-032 §5 | — | 2026-06-30 | S006 | F35 |
| T54.13 | Test (Vitest): TC-107 — reset-password callback + expired link UX — red | Test | completed | test-plan TC-107, UJ-033, ADR-032 §5 | — | 2026-06-30 | S006 | F35 |
| T54.14 | Code: `useAuthLinkCallback` hook — hash/query parse, `exchangeCodeForSession`, session wait, error states | Code | completed | ADR-032 §5–6 | T54.12, T54.13 | 2026-06-30 | S006 | F35 |
| T54.15 | Code: Integrate hook into `SetPasswordPage` (invite + reset variants); loading + error panels | Code | completed | ADR-032 §5–6, UJ-031/033 | T54.14 | 2026-06-30 | S006 | F35 |
| T54.16 | Code: Bilingual i18n keys for expired/invalid link states (EN/ES) | Code | completed | ADR-032 §6, AC-U20 | T54.14 | 2026-06-30 | S006 | F35 |

#### M57: Admin UI invitation lifecycle

| Task | Description | Type | Status | Spec Source | Depends On | Completed | Session | Feature |
|------|-------------|------|--------|-------------|------------|-----------|---------|---------|
| T54.17 | Test (Vitest): Users page "Retract invitation" visible only for `status=invited`; calls revoke endpoint (TC-108 UI) — red | Test | completed | test-plan TC-108, UJ-030 | — | 2026-06-30 | S006 | F35 |
| T54.18 | Test (Vitest): pending rows show `invited_at` + "~1h expiry" hint (RD-096) — red | Test | completed | test-plan TC-106, ADR-032 §9 | — | 2026-06-30 | S006 | F35 |
| T54.19 | Code: UsersPage retract action + invite metadata columns + distinct label from delete | Code | completed | ADR-032 §7/§9, UJ-030 | T54.17, T54.18, T54.9 | 2026-06-30 | S006 | F35 |
| T54.20 | Code+Test: CORS preflight POST on `/admin/users/{id}/revoke-invite` (TC-103 extend) | Code | completed | test-plan TC-103, ADR-032 §11 | T54.9 | 2026-06-30 | S006 | F35 |
| T54.21 | Config: OpenAPI `openapi/data-management.yaml` — `/revoke-invite`, redirect_to docs | Config | completed | api-contract, ADR-011 | T54.9, T54.8 | 2026-06-30 | S006 | F35 |

#### M58: Templates, e2e, runbook + Phase 13 gate

| Task | Description | Type | Status | Spec Source | Depends On | Completed | Session | Feature |
|------|-------------|------|--------|-------------|------------|-----------|---------|---------|
| T54.22 | Config: Polish `supabase/templates/invite.html` + `recovery.html` — CTA, expiry copy, branding (TC-110) | Config | completed | test-plan TC-110, ADR-032 §14 | T54.2 | 2026-06-30 | S006 | F35 |
| T54.23 | Test (e2e): Extend `test_uj031_invite_from_page.py` — assert `redirect_to` query param (TC-104) | Test | completed | test-plan TC-104, UJ-031 | T54.8 | 2026-06-30 | S006 | F35 |
| T54.24 | Docs: staging runbook — Dashboard Auth URL verification step; EV-007 redeploy order; AC-U17–U21 checklist | Docs | completed | deployment-integration §EV-007, ADR-032 §13 | T54.2, T54.4 | 2026-06-30 | S006 | F35 |

#### Phase 13 Gate Check

- [x] All M54–M58 tasks completed (T54.1–T54.24)
- [x] TC-104–TC-110 green; UJ-031/033 callback + retract covered (T2)
- [ ] AC-U3/U5 revised criteria satisfied at T2; AC-U17–U21 pending live verify at 13-deploy-smoke (T3)
- [x] `VECINITA_ADMIN_FRONTEND_URL` on Modal DM; Supabase `site_url` + redirect allowlist synced
- [x] CORS preflight covers POST on `/admin/users/{id}/revoke-invite`
- [ ] ruff / basedpyright / ESLint clean; full backend + DM-frontend suites green

---

### Phase 14: EV-008 — Admin RAG evaluation (F36, #99)

> **Session:** S007-rag-eval · **Evolve cycle:** EV-008 · **Feature IDs:** F36  
> **Branch:** `feat/S007-rag-eval` → `main` (PR-50) · **ADR:** ADR-033 · **Tooling:** LlamaIndex evaluators + custom harness (no new deps)

**Objective:** Golden-set eval harness, Postgres run persistence, internal-write-api routes, admin `/evaluation` tab.  
**Entry gate:** 04-tech-plan approved (ADR-033, TP-S007-01–16).  
**Exit gate:** TC-111–TC-116 green; AC-E12–AC-E16 satisfied at T2; live staging eval run informational at T3.

#### M59: Eval schema + `packages/eval` scaffold

**Goal:** Alembic tables, privacy guardrails, golden-set loader, retrieval scorer foundation.  
**Branch:** `feat/S007-rag-eval`

| # | Task | Type | Status | Spec Source | Depends On | Data Deps | Session | Feature |
|---|------|------|--------|-------------|------------|-----------|---------|---------|
| T59.1 | Test: `tests/privacy/test_eval_tables.py` — eval tables have no PII columns — red | Test | completed | ADR-004, ADR-033 §3 | — | — | S007 | F36 |
| T59.2 | Test: `tests/eval/test_eval_edge_cases.py` — TC-113 abstain/ambiguous/empty — red | Test | completed | test-plan TC-113, eval-golden-set.md | — | D3 | S007 | F36 |
| T59.3 | Code: Alembic migration `eval_runs` + `eval_run_items` | Code | completed | ADR-033 §3, api-contract §EV-008 | T59.1 | — | S007 | F36 |
| T59.4 | Config: Scaffold `packages/eval` (`vecinita-eval`) — golden loader + `retrieval_expectation` scorer | Code | completed | ADR-033 §2, feature-list F36 | T59.3 | D3 | S007 | F36 |
| T59.5 | Test: Extend `tests/eval/test_eval_retrieval_relevance.py` — TC-111 `hit`/`any_of` aggregate ≥80% — red | Test | completed | test-plan TC-111, RD-106 | T59.4 | D3 | S007 | F36 |

#### M60: Eval harness — LlamaIndex judges + runner

**Goal:** Full RAG path per golden row; faithfulness + answer relevancy; #84 adapter stub.  
**Branch:** `feat/S007-rag-eval`

| # | Task | Type | Status | Spec Source | Depends On | Data Deps | Session | Feature |
|---|------|------|--------|-------------|------------|-----------|---------|---------|
| T60.1 | Test: `tests/eval/test_eval_answer_quality.py` — TC-112 faithfulness + answer relevancy (mocked judge) — red | Test | completed | test-plan TC-112, RD-107/108 | T59.4 | D3 | S007 | F36 |
| T60.2 | Code: `packages/eval/runner.py` — orchestrate RAG + per-row metrics + aggregates | Code | completed | ADR-033 §2/§4, feature-list F36 | T59.4 | D3 | S007 | F36 |
| T60.3 | Code: `packages/eval/judges.py` — LlamaIndex `FaithfulnessEvaluator` + `AnswerRelevancyEvaluator` via Modal LLM HTTP | Code | completed | ADR-033 §1, RD-109 | T60.2 | D3, D7 | S007 | F36 |
| T60.4 | Code: `packages/eval/groundedness.py` — `GroundednessScorer` protocol + LlamaIndex default (#84 swap stub) | Code | completed | ADR-033 §9, #84 | T60.3 | — | S007 | F36 |
| T60.5 | Code: Implement TC-111 retrieval + TC-113 edge + TC-112 answer quality — green | Code | completed | test-plan TC-111–TC-113 | T59.5, T59.2, T60.1, T60.3, T60.4 | D3 | S007 | F36 |

#### M61: internal-write-api eval routes

**Goal:** Admin-triggered async runs; history + drill-down API; viewer denied.  
**Branch:** `feat/S007-rag-eval`

| # | Task | Type | Status | Spec Source | Depends On | Data Deps | Session | Feature |
|---|------|------|--------|-------------|------------|-----------|---------|---------|
| T61.1 | Code: Pydantic models `EvalRun*` in `vecinita_shared_schemas` | Code | completed | api-contract §EV-008, ADR-011 | T59.3 | — | S007 | F36 |
| T61.2 | Test: TC-115 — viewer JWT → 403 on `POST` + `GET /internal/v1/eval/runs` — red | Test | completed | test-plan TC-115, RD-110 | — | — | S007 | F36 |
| T61.3 | Test: `tests/e2e/test_uj039_eval_run_trigger.py` — TC-114 admin trigger + poll — red | Test | completed | test-plan TC-114, UJ-039 | T60.5 | D3 | S007 | F36 |
| T61.4 | Code: Eval routes on internal-write-api + `BackgroundTasks` runner wiring | Code | completed | ADR-033 §4/§7, api-contract §EV-008 | T61.1, T60.5 | D3 | S007 | F36 |
| T61.5 | Config: OpenAPI `openapi/internal-write.yaml` — eval routes | Config | completed | ADR-011, api-contract §EV-008 | T61.4 | — | S007 | F36 |
| T61.6 | Test: Extend `tests/unit/test_cors_policy.py` — OPTIONS preflight on `POST /internal/v1/eval/runs` | Test | completed | ADR-033 §11, connectivity-gates | T61.4 | — | S007 | F36 |
| T61.7 | Code: TC-114/TC-115 green | Code | completed | test-plan TC-114/115 | T61.2, T61.3, T61.4 | D3 | S007 | F36 |

#### M62: Admin Evaluation tab

**Goal:** `/evaluation` route, run trigger UI, history + drill-down, bilingual chrome.  
**Branch:** `feat/S007-rag-eval`

| # | Task | Type | Status | Spec Source | Depends On | Data Deps | Session | Feature |
|---|------|------|--------|-------------|------------|-----------|---------|---------|
| T62.1 | Test (Vitest): `test_evaluation_page.test.tsx` — TC-116 history + drill-down — red | Test | completed | test-plan TC-116, UJ-040 | — | — | S007 | F36 |
| T62.2 | Code: `EvaluationPage` — summary, run button, polling, per-metric thresholds | Code | completed | user-journeys UJ-039/040, ADR-033 §8 | T61.7 | — | S007 | F36 |
| T62.3 | Code: `AdminLayout` nav + `App.tsx` route `/evaluation` + i18n `admin.nav.evaluation` (en/es) | Code | completed | feature-list F36, ADR-019 | T62.2 | D10 | S007 | F36 |
| T62.4 | Code: TC-116 Vitest green | Code | completed | test-plan TC-116 | T62.1, T62.2, T62.3 | — | S007 | F36 |

#### M63: Deploy docs + Phase 14 gate

**Goal:** Secrets matrix, redeploy checklist, acceptance criteria wiring.  
**Branch:** `feat/S007-rag-eval`

| # | Task | Type | Status | Spec Source | Depends On | Data Deps | Session | Feature |
|---|------|------|--------|-------------|------------|-----------|---------|---------|
| T63.1 | Config: `docs/staging-secrets-matrix.md` — `VECINITA_EVAL_*` on internal-write-api | Config | completed | config-spec §RAG evaluation, ADR-033 §13 | T61.4 | — | S007 | F36 |
| T63.2 | Docs: `docs/eval-golden-set.md` — link ADR-033; baseline run instructions | Docs | completed | eval-golden-set.md, ADR-033 | T60.5 | — | S007 | F36 |
| T63.3 | Docs: Mark AC-E12–AC-E16 build-complete in acceptance-criteria when green | Docs | completed | acceptance-criteria AC-E12–E16 | T62.4, T61.7, T60.5 | — | S007 | F36 |
| T63.4 | Docs: Session report + Phase 14 gate checklist | Docs | completed | 08-verify-build | T63.1–T63.3 | — | S007 | F36 |

#### M64: Interactive eval dashboard

**Goal:** Time-series charts, pivot explore, collapsible panels, custom criteria (ADR-034).  
**Branch:** `feat/S007-rag-eval`

| # | Task | Type | Status | Spec Source | Depends On | Data Deps | Session | Feature |
|---|------|------|--------|-------------|------------|-----------|---------|---------|
| T64.1 | Test: `tests/integration/test_eval_dashboard_routes.py` — TC-120/122 — red | Test | completed | ADR-034, test-plan TC-120/122 | T61.7 | — | S007 | F36 |
| T64.2 | Code: Alembic `eval_criteria` + privacy guardrails | Code | completed | ADR-034 §Schema | T64.1 | — | S007 | F36 |
| T64.3 | Code: Timeseries + criteria API on internal-write-api | Code | completed | ADR-034 §API | T64.2 | — | S007 | F36 |
| T64.4 | Code: `packages/eval` custom criteria scorer hook | Code | completed | ADR-034 | T64.3 | — | S007 | F36 |
| T64.5 | Test (Vitest): `test_evaluation_dashboard.test.tsx` — TC-117–119/121 — red | Test | completed | UJ-041–043, TC-117–121 | — | — | S007 | F36 |
| T64.6 | Code: Dashboard + Explore + Criteria tabs (`recharts`) | Code | completed | ADR-034 §UI, UJ-041–043 | T64.3 | D10 | S007 | F36 |
| T64.7 | Code: TC-117–121 Vitest + TC-120/122 integration green | Code | completed | test-plan | T64.4–T64.6 | — | S007 | F36 |
| T64.8 | Docs: ADR-034, scope-addition report, feature-list F36 extension | Docs | completed | ADR-034 | T64.7 | — | S007 | F36 |

#### Phase 14 Gate Check (updated)

- [x] All M59–M63 tasks completed (T59.1–T63.4)
- [x] All M64 tasks completed (T64.1–T64.8)
- [x] TC-111–TC-116 green; UJ-039/040 covered (T2)
- [x] TC-117–TC-122 green; UJ-041–043 covered
- [x] AC-E12–AC-E16 satisfied at T2; live staging eval run informational at 13-deploy-smoke (T3)
- [ ] AC-E17–AC-E21 satisfied (dashboard scope)
- [x] `eval_runs` / `eval_run_items` migration applied; privacy test green
- [x] `eval_criteria` migration applied; privacy test green
- [x] No new Python runtime dependencies (ADR-033 §15); **recharts** FE dep per ADR-034
- [x] CORS preflight covers `POST /internal/v1/eval/runs`
- [x] CORS preflight covers eval criteria routes
- [ ] ruff / basedpyright / ESLint clean; full backend + DM-frontend suites green

---

#### Phase 14 Gate Check (baseline — superseded by M64 update above)

- [x] All M59–M63 tasks completed (T59.1–T63.4)
- [x] TC-111–TC-116 green; UJ-039/040 covered (T2)
- [x] AC-E12–AC-E16 satisfied at T2; live staging eval run informational at 13-deploy-smoke (T3)
- [x] `eval_runs` / `eval_run_items` migration applied; privacy test green
- [x] No new runtime dependencies (ADR-033 §15)
- [x] CORS preflight covers `POST /internal/v1/eval/runs`
- [x] ruff / basedpyright / ESLint clean; full backend + DM-frontend suites green

---

### Phase 15: EV-009 — Eval UX polish + playground (F36 follow-ons + F37)

> **Session:** S008-eval-ux-playground · **Evolve cycle:** EV-009 · **Feature IDs:** F36 (M65–M67), F37 (M68–M70)  
> **Branch:** `feat/S008-eval-ux-playground` → `main` (PR-51) · **ADR:** ADR-035 · **Build order:** M65→M70

**Objective:** Fix eval page UX nits, unify eval runs on Jobs tab, enrich dashboard charts, deliver
Playground with versioned presets and super-admin runtime promote to ChatRAG.  
**Entry gate:** 04-tech-plan approved (ADR-035, TP-S008-01–16).  
**Exit gate:** TC-123–TC-133 green; UJ-044–047 covered; AC-E22–AC-E26 satisfied at T2; live promote smoke at T3.

#### M65: Optimistic eval run list + poll UX

**Goal:** New eval run appears in history immediately; status updates live while polling.  
**Branch:** `feat/S008-eval-ux-playground`

| # | Task | Type | Status | Spec Source | Depends On | Data Deps | Session | Feature |
|---|------|------|--------|-------------|------------|-----------|---------|---------|
| T65.1 | Test (Vitest): `test_evaluation_page.test.tsx` — TC-123 optimistic prepend — red | Test | completed | test-plan TC-123, UJ-039, ADR-035 §2 | — | — | S008 | F36 |
| T65.2 | Code: `EvaluationPage` — prepend pending run on create; update status in list during `pollRun` | Code | completed | ADR-035 §2, RD-115 | T65.1 | — | S008 | F36 |
| T65.3 | Code: TC-123 Vitest green | Code | completed | test-plan TC-123 | T65.1, T65.2 | — | S008 | F36 |

#### M66: Unified jobs API + Jobs tab eval rows

**Goal:** `GET /jobs` includes `job_type=eval`; Jobs tab shows eval runs with status.  
**Branch:** `feat/S008-eval-ux-playground`

| # | Task | Type | Status | Spec Source | Depends On | Data Deps | Session | Feature |
|---|------|------|--------|-------------|------------|-----------|---------|---------|
| T66.1 | Test: `tests/e2e/test_uj044_eval_jobs_tab.py` — TC-124 — red | Test | completed | test-plan TC-124, UJ-044, ADR-035 §3 | — | D3 | S008 | F36 |
| T66.2 | Test (Vitest): `test_jobs_page.test.tsx` — eval row + nav — red | Test | completed | UJ-044, RD-138 | — | — | S008 | F36 |
| T66.3 | Code: DM backend `list_jobs` — HTTP aggregate eval runs from internal-write-api | Code | completed | ADR-035 §3, api-contract §EV-009 | — | — | S008 | F36 |
| T66.4 | Code: Extend `JobType` + `JobsPage` — eval badge, click → `/evaluation?run=<id>` | Code | completed | UJ-044, RD-138 | T66.3 | — | S008 | F36 |
| T66.5 | Test (Playwright): `tests/ui/admin/uj044-eval-jobs-tab.spec.ts` — T0-ui | Test | pending | test-plan, connectivity-gates | T66.4 | — | S008 | F36 |
| T66.6 | Code: TC-124 E2E + Vitest green | Code | completed | test-plan TC-124 | T66.1, T66.2, T66.3, T66.4 | D3 | S008 | F36 |

#### M67: Dashboard scatter + time-range presets

**Goal:** Scatter chart type; presets 1D/7D/10D/1M/1Y/custom; FE filter on timeseries.  
**Branch:** `feat/S008-eval-ux-playground`

| # | Task | Type | Status | Spec Source | Depends On | Data Deps | Session | Feature |
|---|------|------|--------|-------------|------------|-----------|---------|---------|
| T67.1 | Test (Vitest): `test_evaluation_dashboard.test.tsx` — TC-125/126 — red | Test | completed | test-plan TC-125/126, UJ-041, ADR-035 §4 | — | — | S008 | F36 |
| T67.2 | Code: `EvalMetricChart` — scatter type + dynamic x-axis granularity | Code | completed | ADR-035 §4, RD-117 | T67.1 | — | S008 | F36 |
| T67.3 | Code: `EvaluationDashboardTab` — time-range presets + custom date picker + client filter | Code | completed | ADR-035 §4, RD-117 | T67.2 | — | S008 | F36 |
| T67.4 | Test (Playwright): extend `uj041-eval-dashboard-tabs.spec.ts` — scatter + presets | Test | pending | test-plan, connectivity-gates | T67.3 | — | S008 | F36 |
| T67.5 | Code: TC-125/126 Vitest green | Code | completed | test-plan | T67.1, T67.2, T67.3 | — | S008 | F36 |

#### M68: Config schema + preset API + DB

**Goal:** `eval_config_presets`, `rag_production_config`, extended eval run create with overrides.  
**Branch:** `feat/S008-eval-ux-playground`

| # | Task | Type | Status | Spec Source | Depends On | Data Deps | Session | Feature |
|---|------|------|--------|-------------|------------|-----------|---------|---------|
| T68.1 | Test: `tests/privacy/test_eval_config_tables.py` — no PII columns — red | Test | completed | ADR-004, ADR-035 §5 | — | — | S008 | F37 |
| T68.2 | Code: Alembic — `eval_config_presets`, `rag_production_config`, `eval_runs` extensions | Code | completed | ADR-035 §5, api-contract §EV-009 | T68.1 | — | S008 | F37 |
| T68.3 | Code: Pydantic `EvalConfig*`, preset models in `vecinita_shared_schemas` | Code | completed | ADR-035 §5, config-spec §EvalConfig | T68.2 | — | S008 | F37 |
| T68.4 | Test: `tests/integration/test_eval_config_presets.py` — TC-127 — red | Test | completed | test-plan TC-127, UJ-045 | T68.3 | — | S008 | F37 |
| T68.5 | Code: Preset CRUD routes on internal-write-api | Code | completed | api-contract §EV-009 | T68.3 | — | S008 | F37 |
| T68.6 | Code: Extend `POST /eval/runs` — `mode`, `config`, `preset_id`; `config_snapshot` persist | Code | completed | api-contract §EV-009, ADR-035 §6 | T68.3, T61.4 | D3 | S008 | F37 | 2026-07-02 |
| T68.7 | Code: `packages/eval` runner — accept per-run config overrides (sandbox) | Code | completed | ADR-035 §6, feature-list F37 | T68.6, T60.5 | D3 | S008 | F37 | 2026-07-02 |
| T68.8 | Config: OpenAPI `internal-write.yaml` — EV-009 routes | Config | pending | ADR-011, api-contract §EV-009 | T68.5, T68.6 | — | S008 | F37 |
| T68.9 | Code: TC-127 integration green | Code | pending | test-plan TC-127 | T68.4, T68.5, T68.7 | — | S008 | F37 |
| T68.10 | Test: `tests/integration/test_ollama_models_list.py` — TC-134 — red | Test | pending | test-plan TC-134, RD-139–141 | T68.3 | — | S008 | F37 |
| T68.11 | Code: Modal Ollama model list + pull job routes (`GET /models/ollama`, `POST /models/ollama/pull`) | Code | pending | ADR-035 §6, RD-140–141 | T68.3 | D3 | S008 | F37 |
| T68.12 | Code: Eval runner + ChatRAG — route LLM calls via selected `model_id` (Ollama SDK) | Code | pending | ADR-035 §6–7, RD-139, RD-142 | T68.7, T68.11 | D3 | S008 | F37 |
| T68.13 | Code: TC-134 integration green | Code | pending | test-plan TC-134 | T68.10, T68.11, T68.12 | — | S008 | F37 |

#### M69: Playground UI (golden + ad-hoc + compare)

**Goal:** `/evaluation?tab=playground` two-column UI; golden + ad-hoc runs; compare view.  
**Branch:** `feat/S008-eval-ux-playground`

| # | Task | Type | Status | Spec Source | Depends On | Data Deps | Session | Feature |
|---|------|------|--------|-------------|------------|-----------|---------|---------|
| T69.1 | Test (Vitest): `test_evaluation_playground.test.tsx` — TC-128/129 — red | Test | pending | test-plan TC-128/129, UJ-045 | — | — | S008 | F37 |
| T69.2 | Test (Vitest): `test_evaluation_compare.test.tsx` — TC-130 — red | Test | pending | test-plan TC-130, UJ-046 | — | — | S008 | F37 |
| T69.3 | Code: `EvaluationPlaygroundTab` — two-column layout, defaults + Ollama model picker (RD-137, RD-139) | Code | pending | ADR-035 §8, UJ-045, RD-136 | T68.13 | D10 | S008 | F37 |
| T69.4 | Code: Preset save/load/version UI + share-read clone | Code | pending | ADR-035 §8, RD-121 | T69.3, T68.5 | — | S008 | F37 |
| T69.5 | Code: Compare runs view — side-by-side metrics + per-question diff | Code | pending | UJ-046, RD-130 | T69.3 | — | S008 | F37 |
| T69.6 | Code: Runs tab **Run evaluation** → Playground with last preset (RD-129) | Code | pending | UJ-039, RD-129 | T69.3 | — | S008 | F37 |
| T69.7 | Test: `tests/e2e/test_uj045_eval_playground.py` — TC-128/129 — red | Test | pending | test-plan, UJ-045 | T68.7 | D3 | S008 | F37 |
| T69.8 | Test (Playwright): `tests/ui/admin/uj045-eval-playground.spec.ts` — T0-ui | Test | pending | test-plan, connectivity-gates | T69.6 | — | S008 | F37 |
| T69.9 | Code: TC-128/129/130 Vitest + E2E green | Code | pending | test-plan | T69.1–T69.8 | D3 | S008 | F37 |

#### M70: Super-admin promote + ChatRAG config reader

**Goal:** `super-admin` role; promote endpoint; ChatRAG reads active production config from DB.  
**Branch:** `feat/S008-eval-ux-playground`

| # | Task | Type | Status | Spec Source | Depends On | Data Deps | Session | Feature |
|---|------|------|--------|-------------|------------|-----------|---------|---------|
| T70.1 | Code: Super-admin bootstrap — `VECINITA_SUPER_ADMIN_EMAIL` seed in auth layer | Code | pending | ADR-035 §9, config-spec, RD-127 | — | — | S008 | F37 |
| T70.2 | Test: `tests/e2e/test_uj047_eval_promote_config.py` — TC-131/132 — red | Test | pending | test-plan TC-131/132, UJ-047 | T70.1 | — | S008 | F37 |
| T70.3 | Code: `POST /rag/config/promote` + `GET /rag/config/active` on internal-write-api | Code | pending | api-contract §EV-009, ADR-035 §10 | T68.2, T70.1 | — | S008 | F37 |
| T70.4 | Code: `chat-rag-backend` — read `rag_production_config` with env fallback (RD-134) | Code | pending | ADR-035 §11, config-spec | T68.2 | — | S008 | F37 |
| T70.5 | Test: `tests/integration/test_rag_production_config.py` — TC-133 — red | Test | pending | test-plan TC-133, UJ-047 | T70.4 | — | S008 | F37 |
| T70.6 | Code: Playground promote button (super-admin only) + confirm dialog | Code | pending | UJ-047, ADR-035 §10 | T70.3, T69.4 | — | S008 | F37 |
| T70.7 | Config: `docs/staging-secrets-matrix.md` — `VECINITA_SUPER_ADMIN_EMAIL` | Config | pending | config-spec §Eval playground | T70.1 | — | S008 | F37 |
| T70.8 | Docs: Phase 15 gate checklist + session 04-tech-plan report | Docs | pending | 08-verify-build | T65.3–T70.6 | — | S008 | F37 |

#### Phase 15 Gate Check

- [ ] All M65–M70 tasks completed (T65.1–T70.8)
- [ ] TC-123–TC-133 green; UJ-044–047 covered (T2)
- [ ] AC-E22–AC-E26 satisfied at T2; live promote smoke at 13-deploy-smoke (T3)
- [ ] `eval_config_presets` / `rag_production_config` migrations applied; privacy tests green
- [ ] No new Python runtime dependencies (ADR-035 §15)
- [ ] CORS preflight covers new EV-009 routes
- [ ] ruff / basedpyright / ESLint clean; full backend + DM-frontend suites green

---

## Git Strategy

### Commit rules

Atomic commits per task: `[T1.1] type: description`. Post-commit: ruff, basedpyright, full pytest (see `docs/typing-policy.md`).

### Branch workflow

```
main
 └── phase/1-foundation
      ├── feat/M1-monorepo-scaffold
      ├── feat/M2-database-privacy
      └── feat/M3-openapi-schemas
 └── phase/2-data-management
      ├── feat/M4-internal-write-api
      ├── feat/M5-fastembed-modal
      ├── feat/M6-modal-ingest
      └── feat/M7-data-mgmt-frontend
 └── phase/3-chatrag
      ├── feat/M8-packages-rag
      ├── feat/M9-vllm-modal
      ├── feat/M10-chat-rag-backend
      └── feat/M11-chat-rag-frontend
 └── phase/4-integration
      ├── feat/M12-local-dev
      ├── feat/M13-ci
      └── feat/M14-staging-deploy
 └── evolve/EV-001-corpus-tags (from main)
      ├── feat/M15-tag-schema
      ├── feat/M16-ingest-tagging
      ├── feat/M17-browse-tag-rag
      ├── feat/M18-admin-tags
      └── feat/M19-ev001-deploy
 └── evolve/EV-002-admin-overhaul (from main)
      ├── feat/M20-ev002-schema
      ├── feat/M21-audit-endpoints
      ├── feat/M22-serving-stats
      ├── feat/M23-bulk-ops
      ├── feat/M24-health-stats
      ├── feat/M25-shadcn-routing
      ├── feat/M26-tag-display
      ├── feat/M27-dashboard-health
      ├── feat/M28-bulk-ops-ui
      ├── feat/M29-audit-ui
      ├── feat/M30-retention-integration
      └── feat/M31-ev002-deploy
 └── evolve/EV-004-admin-i18n (from main; active: fix/es-en-full-ui per TP-030)
      ├── feat/M32-workspace-scaffold
      ├── feat/M33-frontend-i18n
      ├── feat/M34-frontend-ui
      ├── feat/M35-chatrag-migration
      ├── feat/M36-admin-i18n
      ├── feat/M37-ci-workspaces
      └── feat/M38-ev004-deploy
```

### PR Plan

| PR | Type | Milestone/Phase | Branch | Target | Status |
|----|------|-----------------|--------|--------|--------|
| PR-1 | Minor | M1 | feat/M1-monorepo-scaffold | phase/1-foundation | merged — https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/20 |
| PR-2 | Minor | M2 | feat/M2-database-privacy | phase/1-foundation | merged — https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/21 |
| PR-3 | Minor | M3 | feat/M3-openapi-schemas | phase/1-foundation | merged — https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/22 |
| PR-4 | Major | Phase 1 | phase/1-foundation | main | pending |
| PR-5 | Minor | M4 | feat/M4-internal-write-api | phase/2-data-management | merged — https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/23 |
| PR-6 | Minor | M5 | feat/M5-fastembed-modal | phase/2-data-management | merged — https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/24 |
| PR-7 | Minor | M6 | feat/M6-modal-ingest | main | merged — https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/25 |
| PR-8 | Minor | M7 | feat/M7-data-mgmt-frontend | main | merged — https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/26 |
| PR-9 | Major | Phase 2 | phase/2-data-management | main | pending |
| PR-10 | Minor | M8 | feat/M8-packages-rag | main | merged — https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/27 |
| PR-11 | Minor | M9 | feat/M9-vllm-modal | main | merged — https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/28 |
| PR-12 | Minor | M10 | feat/M10-chat-rag-backend | main | merged — https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/29 |
| PR-13 | Minor | M11 | feat/M11-chat-rag-frontend | main | merged — https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/30 |
| PR-14 | Major | Phase 3 | phase/3-chatrag | main | pending |
| PR-15 | Minor | M12 | feat/M12-local-dev | main | merged — https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/31 |
| PR-16 | Minor | M13 | feat/M13-ci | main | merged — https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/32 |
| PR-17 | Minor | M14 | feat/M14-staging-deploy | main | merged — https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/33 |
| PR-18 | Major | Phase 4 | phase/4-integration | main | pending |
| PR-19 | Minor | M15 | feat/M15-tag-schema | evolve/EV-001-corpus-tags | merged — https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/38 |
| PR-20 | Minor | M16 | feat/M16-ingest-tagging | evolve/EV-001-corpus-tags | merged — https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/39 |
| PR-21 | Minor | M17 | feat/M17-browse-tag-rag | evolve/EV-001-corpus-tags | merged — https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/40 |
| PR-22 | Minor | M18 | feat/M18-admin-tags | evolve/EV-001-corpus-tags | merged |
| PR-23 | Minor | M19 | feat/M19-ev001-deploy | evolve/EV-001-corpus-tags | merged |
| PR-24 | Major | Phase 5 / EV-001 | evolve/EV-001-corpus-tags | main | merged |
| PR-25 | Minor | M20 | feat/M20-ev002-schema | evolve/EV-002-admin-overhaul | pending |
| PR-26 | Minor | M21 | feat/M21-audit-endpoints | evolve/EV-002-admin-overhaul | pending |
| PR-27 | Minor | M22 | feat/M22-serving-stats | evolve/EV-002-admin-overhaul | pending |
| PR-28 | Minor | M23 | feat/M23-bulk-ops | evolve/EV-002-admin-overhaul | pending |
| PR-29 | Minor | M24 | feat/M24-health-stats | evolve/EV-002-admin-overhaul | pending |
| PR-30 | Minor | M25 | feat/M25-shadcn-routing | evolve/EV-002-admin-overhaul | pending |
| PR-31 | Minor | M26 | feat/M26-tag-display | evolve/EV-002-admin-overhaul | pending |
| PR-32 | Minor | M27 | feat/M27-dashboard-health | evolve/EV-002-admin-overhaul | pending |
| PR-33 | Minor | M28 | feat/M28-bulk-ops-ui | evolve/EV-002-admin-overhaul | pending |
| PR-34 | Minor | M29 | feat/M29-audit-ui | evolve/EV-002-admin-overhaul | pending |
| PR-35 | Minor | M30 | feat/M30-retention-integration | evolve/EV-002-admin-overhaul | merged (local) |
| PR-36 | Minor | M31 | feat/M31-ev002-deploy | evolve/EV-002-admin-overhaul | merged (local) |
| PR-37 | Major | Phase 6–8 / EV-002 | evolve/EV-002-admin-overhaul | main | pending |
| PR-38 | Minor | M32 | feat/M32-workspace-scaffold | fix/es-en-full-ui | pending |
| PR-39 | Minor | M33 | feat/M33-frontend-i18n | fix/es-en-full-ui | pending |
| PR-40 | Minor | M34 | feat/M34-frontend-ui | fix/es-en-full-ui | pending |
| PR-41 | Minor | M35 | feat/M35-chatrag-migration | fix/es-en-full-ui | pending |
| PR-42 | Minor | M36 | feat/M36-admin-i18n | fix/es-en-full-ui | pending |
| PR-43 | Minor | M37 | feat/M37-ci-workspaces | fix/es-en-full-ui | pending |
| PR-44 | Minor | M38 | feat/M38-ev004-deploy | fix/es-en-full-ui | pending |
| PR-45 | Major | Phase 9 / EV-004 | fix/es-en-full-ui | main | pending |
| PR-46 | Major | Phase 10 / S003 | feat/S003-persistent-chat-history | main | open ([#96](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/96)) |
| PR-47 | Major | Phase 11 / S004 (EV-005) | feat/S004-supabase-auth | main | merged ([#100](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/100)) |
| PR-48 | Major | Phase 12 / S005 (EV-006) | feat/S005-user-mgmt-auth | main | pending ([#75](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/75)) |
| PR-49 | Major | Phase 13 / S006 (EV-007) | feat/S006-invite-acceptance | main | open ([#109](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/109), [PR #110](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/110)) |
| PR-50 | Major | Phase 14 / S007 (EV-008) | feat/S007-rag-eval | main | pending ([#99](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/99)) |
| PR-51 | Major | Phase 15 / S008 (EV-009) | feat/S008-eval-ux-playground | main | pending (F37 eval UX + playground) |

S003 is evolve-lite + frontend-only: M39–M42 land as atomic commits on the single
`feat/S003-persistent-chat-history` branch (one PR to `main`, PR-46), matching the S002 pattern.

S004 (EV-005) is evolve-lite: M43–M47 land as atomic commits on the single
`feat/S004-supabase-auth` branch (one PR to `main`, PR-47), matching the S002/S003 pattern.

S005 (EV-006) is evolve-lite: M48–M53 land as atomic commits on the single
`feat/S005-user-mgmt-auth` branch (one PR to `main`, PR-48), matching the S002/S003/S004 pattern.
M53 (auth UX hardening, ADR-031) was appended after the user extended scope on 2026-06-29.

S006 (EV-007) is evolve-lite: M54–M58 land as atomic commits on the single
`feat/S006-invite-acceptance` branch (one PR to `main`, PR-49), closing #109 invite acceptance gap.

S007 (EV-008) is evolve-lite: M59–M63 land as atomic commits on the single
`feat/S007-rag-eval` branch (one PR to `main`, PR-50), closing #99 RAG evaluation tab + golden harness.

S008 (EV-009) is evolve-lite: M65–M70 land as atomic commits on the single
`feat/S008-eval-ux-playground` branch (one PR to `main`, PR-51), delivering F36 follow-ons + F37 playground.

## Task Tracking

Statuses: `pending` | `in_progress` | `completed` | `blocked` | `deferred`

| Task | Milestone | Phase | Type | Status | Blocked By | Data Deps | Completed |
|------|-----------|-------|------|--------|------------|-----------|-----------|
| T1.1 | M1 | 1 | Config | completed | — | — | 2026-05-19 |
| T1.2 | M1 | 1 | Config | completed | T1.1 | — | 2026-05-19 |
| T1.3 | M1 | 1 | Config | completed | T1.2 | — | 2026-05-19 |
| T1.4 | M1 | 1 | Test | completed | T1.3 | — | 2026-05-19 |
| T1.5 | M1 | 1 | Config | completed | T1.2 | — | 2026-05-19 |
| T1.6 | M1 | 1 | Config | completed | T1.1 | — | 2026-05-19 |
| T2.1 | M2 | 1 | Test | completed | T1.4 | — | 2026-05-19 |
| T2.2 | M2 | 1 | Code | completed | T2.1 | — | 2026-05-19 |
| T2.3 | M2 | 1 | Test | completed | T2.2 | — | 2026-05-19 |
| T2.4 | M2 | 1 | Code | completed | T2.3 | — | 2026-05-19 |
| T2.5 | M2 | 1 | Code | completed | T2.4 | D1, D2 | 2026-05-19 |
| T2.6 | M2 | 1 | Test | completed | T2.5 | D1, D2 | 2026-05-19 |
| T2.7 | M2 | 1 | Config | completed | T2.5 | D1–D4 | 2026-05-19 |
| T2.8 | M2 | 1 | Code | completed | T2.5 | D3 | 2026-05-19 |
| T2.9 | M2 | 1 | Code | completed | T2.5 | D4 | 2026-05-19 |
| T3.1 | M3 | 1 | Docs | completed | T1.1 | — | 2026-05-19 |
| T3.2 | M3 | 1 | Docs | completed | T1.1 | — | 2026-05-19 |
| T3.3 | M3 | 1 | Docs | completed | T2.2 | — | 2026-05-19 |
| T3.4 | M3 | 1 | Code | completed | T3.1–T3.3 | — | 2026-05-19 |
| T3.5 | M3 | 1 | Test | completed | T3.4 | — | 2026-05-19 |
| T3.6 | M3 | 1 | Code | completed | T3.5 | — | 2026-05-19 |
| T3.7 | M3 | 1 | Code | completed | T1.3 | — | 2026-05-19 |
| T4.1 | M4 | 2 | Test | completed | T3.4, T2.4 | D1 | 2026-05-19 |
| T4.2 | M4 | 2 | Code | completed | T4.1 | — | 2026-05-19 |
| T4.3 | M4 | 2 | Code | completed | T4.2 | — | 2026-05-19 |
| T4.4 | M4 | 2 | Test | completed | T4.3 | D1 | 2026-05-19 |
| T5.1 | M5 | 2 | Test | completed | T1.3 | — | 2026-05-19 |
| T5.2 | M5 | 2 | Code | completed | T5.1 | — | 2026-05-19 |
| T5.3 | M5 | 2 | Code | completed | T5.2 | D6 | 2026-05-19 |
| T5.4 | M5 | 2 | Test | completed | T5.3 | D6 | 2026-05-19 |
| T6.1 | M6 | 2 | Test | completed | T1.3 | D4 | 2026-05-19 |
| T6.2 | M6 | 2 | Code | completed | T6.1 | — | 2026-05-19 |
| T6.3 | M6 | 2 | Code | completed | T3.2, T4.2 | — | 2026-05-19 |
| T6.4 | M6 | 2 | Code | completed | T6.2, T5.2, T4.2 | D4, D6 | 2026-05-19 |
| T6.5 | M6 | 2 | Test | completed | T6.4 | D4 | 2026-05-19 |
| T6.6 | M6 | 2 | Test | completed | T6.4 | — | 2026-05-19 |
| T6.7 | M6 | 2 | Test | completed | T6.3 | — | 2026-05-19 |
| T7.1 | M7 | 2 | Config | completed | T1.1 | — | 2026-05-19 |
| T7.2 | M7 | 2 | Code | completed | T6.3, T7.1 | — | 2026-05-19 |
| T7.3 | M7 | 2 | Code | completed | T4.3, T7.2 | — | 2026-05-19 |
| T7.4 | M7 | 2 | Test | completed | T7.2 | — | 2026-05-19 |
| T7.5 | M7 | 2 | Test | completed | T4.3, T7.3 | D1 | 2026-05-19 |
| T8.1 | M8 | 3 | Config | completed | T1.2 | — | 2026-05-19 |
| T8.2 | M8 | 3 | Test | completed | T2.6, T8.1 | D1 | 2026-05-19 |
| T8.3 | M8 | 3 | Test | completed | T8.2 | — | 2026-05-19 |
| T8.4 | M8 | 3 | Code | completed | T8.3 | — | 2026-05-19 |
| T8.5 | M8 | 3 | Test | completed | T8.4 | D2 | 2026-05-19 |
| T9.1 | M9 | 3 | Config | completed | T1.1 | D7 | 2026-05-19 |
| T9.2 | M9 | 3 | Code | completed | T9.1 | D7 | 2026-05-19 |
| T9.3 | M9 | 3 | Test | completed | T9.2 | — | 2026-05-19 |
| T10.1 | M10 | 3 | Test | completed | T8.4, T5.2, T9.3 | D1 | 2026-05-19 |
| T10.2 | M10 | 3 | Test | completed | T10.1 | D1 | 2026-05-19 |
| T10.3 | M10 | 3 | Code | completed | T10.2 | — | 2026-05-19 |
| T10.4 | M10 | 3 | Code | completed | T10.3 | — | 2026-05-19 |
| T10.5 | M10 | 3 | Test | completed | T3.6, T10.4 | — | 2026-05-19 |
| T10.6 | M10 | 3 | Test | completed | T10.4, T11.2 | D1 | 2026-05-19 |
| T10.7 | M10 | 3 | Test | completed | T10.4 | D1 | 2026-05-19 |
| T11.1 | M11 | 3 | Config | completed | T1.1 | — | 2026-05-19 |
| T11.2 | M11 | 3 | Code | completed | T10.3, T11.1 | — | 2026-05-19 |
| T11.3 | M11 | 3 | Code | completed | T11.2 | — | 2026-05-19 |
| T11.4 | M11 | 3 | Test | completed | T11.2 | — | 2026-05-19 |
| T12.1 | M12 | 4 | Test | completed | T10.3, T6.3 | D1–D5 | 2026-05-19 |
| T12.2 | M12 | 4 | Docs | completed | T12.1 | — | 2026-05-19 |
| T12.3 | M12 | 4 | Docs | completed | T12.2 | — | 2026-05-19 |
| T13.1 | M13 | 4 | Config | completed | T1.5 | — | 2026-05-19 |
| T13.2 | M13 | 4 | Config | completed | T7.1, T11.1 | — | 2026-05-19 |
| T13.3 | M13 | 4 | Config | completed | T13.1 | — | 2026-05-19 |
| T13.4 | M13 | 4 | Config | completed | T6.4 | — | 2026-05-19 |
| T14.1 | M14 | 4 | Config | completed | T13.1 | — | 2026-05-19 |
| T14.2 | M14 | 4 | Docs | completed | T14.1 | — | 2026-05-19 |
| T14.3 | M14 | 4 | Config | completed | T14.1 | D1–D7 | 2026-05-19 |
| T14.4 | M14 | 4 | Docs | completed | T14.3 | — | 2026-05-19 |
| T14.5 | M14 | 4 | Test | completed | T2.8, T8.4 | D3 | 2026-05-19 |
| T15.1 | M15 | 5 | Test | completed | T2.4 | — | EV-001 | 2026-05-24 |
| T15.2 | M15 | 5 | Code | completed | T15.1 | — | EV-001 | 2026-05-24 |
| T15.3 | M15 | 5 | Test | completed | T15.2 | — | EV-001 | 2026-05-24 |
| T15.4 | M15 | 5 | Code | completed | T15.2 | D8 | EV-001 | 2026-05-24 |
| T15.5 | M15 | 5 | Code | completed | T15.4 | D9 | EV-001 | 2026-05-24 |
| T15.6 | M15 | 5 | Test | completed | T15.5 | D8, D9 | EV-001 | 2026-05-24 |
| T16.1 | M16 | 5 | Test | completed | T9.3 | — | EV-001 | 2026-05-24 |
| T16.2 | M16 | 5 | Code | completed | T16.1 | D8 | EV-001 | 2026-05-24 |
| T16.3 | M16 | 5 | Code | completed | T16.2, T6.4, T15.2 | D8 | EV-001 | 2026-05-24 |
| T16.4 | M16 | 5 | Code | completed | T15.2, T4.2 | — | EV-001 | 2026-05-24 |
| T16.5 | M16 | 5 | Test | completed | T16.3, T16.4 | D4, D8 | EV-001 | 2026-05-24 |
| T16.6 | M16 | 5 | Code | completed | T16.2, T6.3 | — | EV-001 | 2026-05-24 |
| T16.7 | M16 | 5 | Code | completed | T16.6, T16.4 | — | EV-001 | 2026-05-24 |
| T16.8 | M16 | 5 | Test | completed | T16.7 | D9 | EV-001 | 2026-05-24 |
| T17.1 | M17 | 5 | Code | completed | T15.2, T3.4 | — | EV-001 | 2026-05-24 |
| T17.2 | M17 | 5 | Test | completed | T17.1, T15.6 | D9 | EV-001 | 2026-05-24 |
| T17.3 | M17 | 5 | Code | completed | T17.2 | — | EV-001 | 2026-05-24 |
| T17.4 | M17 | 5 | Test | completed | T17.3 | — | EV-001 | 2026-05-24 |
| T17.5 | M17 | 5 | Code | completed | T16.2, T8.4 | D9 | EV-001 | 2026-05-24 |
| T17.6 | M17 | 5 | Test | completed | T17.5 | D9 | EV-001 | 2026-05-24 |
| T17.7 | M17 | 5 | Code | completed | T17.5, T10.4 | — | EV-001 | 2026-05-24 |
| T17.8 | M17 | 5 | Code | completed | T17.3, T11.1 | — | EV-001 | 2026-05-24 |
| T17.9 | M17 | 5 | Code | completed | T17.7, T11.2 | — | EV-001 | 2026-05-24 |
| T17.10 | M17 | 5 | Test | completed | T17.8, T17.9 | — | EV-001 | 2026-05-24 |
| T17.11 | M17 | 5 | Test | completed | T17.8, T17.9 | D9 | EV-001 | 2026-05-24 |
| T18.1 | M18 | 5 | Test | completed | T15.2 | D9 | EV-001 | 2026-05-24 |
| T18.2 | M18 | 5 | Test | completed | T15.2 | D9 | EV-001 | 2026-05-24 |
| T18.3 | M18 | 5 | Code | completed | T18.1, T18.2 | — | EV-001 | 2026-05-24 |
| T18.4 | M18 | 5 | Code | completed | T18.3, T7.1 | — | EV-001 | 2026-05-24 |
| T18.5 | M18 | 5 | Code | completed | T16.7, T18.4 | — | EV-001 | 2026-05-24 |
| T18.6 | M18 | 5 | Test | completed | T18.5 | D9 | EV-001 | 2026-05-24 |
| T18.7 | M18 | 5 | Test | completed | T18.3 | — | EV-001 | 2026-05-24 |
| T19.1 | M19 | 5 | Docs | completed | T17.3 | — | EV-001 | 2026-05-24 |
| T19.2 | M19 | 5 | Test | completed | T17.4 | — | EV-001 | 2026-05-24 |
| T19.3 | M19 | 5 | Config | completed | T19.2 | — | EV-001 | 2026-05-24 |
| T19.5 | M19 | 5 | Config | completed | T19.3, T17.8 | — | EV-001 | 2026-05-24 |
| T19.4 | M19 | 5 | Config | completed | T19.5, T18.7, T17.11, T18.6 | D1–D9 | EV-001 | 2026-05-24 |
| T20.1 | M20 | 6 | Test | completed | T15.2 | — | EV-002 | 2026-05-26 |
| T20.2 | M20 | 6 | Code | completed | T20.1 | — | EV-002 | 2026-05-26 |
| T20.3 | M20 | 6 | Code | completed | T20.2 | — | EV-002 | 2026-05-26 |
| T20.4 | M20 | 6 | Test | completed | T20.3 | — | EV-002 | 2026-05-26 |
| T21.1 | M21 | 6 | Test | completed | T20.4 | — | EV-002 | 2026-05-26 |
| T21.2 | M21 | 6 | Code | completed | T21.1 | — | EV-002 | 2026-05-26 |
| T21.3 | M21 | 6 | Code | completed | T21.2 | — | EV-002 | 2026-05-26 |
| T21.4 | M21 | 6 | Test | completed | T21.3 | D1 | EV-002 | 2026-05-26 |
| T21.5 | M21 | 6 | Code | completed | T21.2 | — | EV-002 | 2026-05-26 |
| T21.6 | M21 | 6 | Test | completed | T21.5 | — | EV-002 | 2026-05-26 |
| T21.7 | M21 | 6 | Code | completed | T21.2 | — | EV-002 | 2026-05-26 |
| T21.8 | M21 | 6 | Test | completed | T21.7, T21.3 | — | EV-002 | 2026-05-26 |
| T22.1 | M22 | 6 | Test | completed | T20.4 | — | EV-002 | 2026-05-26 |
| T22.2 | M22 | 6 | Code | completed | T22.1 | — | EV-002 | 2026-05-26 |
| T22.3 | M22 | 6 | Test | completed | T22.2 | — | EV-002 | 2026-05-26 |
| T22.4 | M22 | 6 | Code | completed | T22.3 | — | EV-002 | 2026-05-26 |
| T22.5 | M22 | 6 | Code | completed | T22.2, T10.4 | — | EV-002 | 2026-05-26 |
| T22.6 | M22 | 6 | Test | completed | T22.5 | D1 | EV-002 | 2026-05-26 |
| T23.1 | M23 | 6 | Test | completed | T21.3, T20.4 | D1 | EV-002 | 2026-05-26 |
| T23.2 | M23 | 6 | Code | completed | T23.1 | — | EV-002 | 2026-05-26 |
| T23.3 | M23 | 6 | Test | completed | T21.3 | D1 | EV-002 | 2026-05-26 |
| T23.4 | M23 | 6 | Code | completed | T23.3 | — | EV-002 | 2026-05-26 |
| T23.5 | M23 | 6 | Test | completed | T23.2 | — | EV-002 | 2026-05-26 |
| T23.6 | M23 | 6 | Code | completed | T23.5 | — | EV-002 | 2026-05-26 |
| T23.7 | M23 | 6 | Test | completed | T21.3 | D1 | EV-002 | 2026-05-26 |
| T23.8 | M23 | 6 | Code | completed | T23.7 | — | EV-002 | 2026-05-26 |
| T24.1 | M24 | 6 | Test | completed | T20.4 | — | EV-002 | 2026-05-26 |
| T24.2 | M24 | 6 | Code | completed | T24.1 | — | EV-002 | 2026-05-26 |
| T24.3 | M24 | 6 | Test | completed | T22.4, T21.5 | — | EV-002 | 2026-05-26 |
| T24.4 | M24 | 6 | Code | completed | T24.3 | — | EV-002 | 2026-05-26 |
| T24.5 | M24 | 6 | Test | completed | T23.8, T24.4, T24.2 | — | EV-002 | 2026-05-26 |
| T24.6 | M24 | 6 | Code | completed | T24.5 | — | EV-002 | 2026-05-26 |
| T25.1 | M25 | 7 | Config | pending | T7.1 | — | EV-002 | — |
| T25.2 | M25 | 7 | Config | pending | T25.1 | — | EV-002 | — |
| T25.3 | M25 | 7 | Config | pending | T25.2 | — | EV-002 | — |
| T25.4 | M25 | 7 | Config | pending | T25.2 | — | EV-002 | — |
| T25.5 | M25 | 7 | Code | pending | T25.3, T25.4 | — | EV-002 | — |
| T25.6 | M25 | 7 | Code | pending | T25.5 | — | EV-002 | — |
| T25.7 | M25 | 7 | Test | pending | T25.5 | — | EV-002 | — |
| T26.1 | M26 | 7 | Code | pending | T25.6 | — | EV-002 | — |
| T26.2 | M26 | 7 | Code | pending | T25.3 | — | EV-002 | — |
| T26.3 | M26 | 7 | Code | pending | T26.1, T26.2 | — | EV-002 | — |
| T26.4 | M26 | 7 | Test | pending | T26.3 | — | EV-002 | — |
| T27.1 | M27 | 7 | Code | completed | T25.5, T24.4 | — | EV-002 | — |
| T27.2 | M27 | 7 | Code | completed | T27.1, T22.4 | — | EV-002 | — |
| T27.3 | M27 | 7 | Code | completed | T27.1, T21.5 | — | EV-002 | — |
| T27.4 | M27 | 7 | Test | completed | T27.3 | — | EV-002 | — |
| T27.5 | M27 | 7 | Code | completed | T25.5, T24.2 | — | EV-002 | — |
| T27.6 | M27 | 7 | Test | completed | T27.5 | — | EV-002 | — |
| T28.1 | M28 | 7 | Code | completed | T26.3 | — | EV-002 | — |
| T28.2 | M28 | 7 | Code | completed | T28.1 | — | EV-002 | — |
| T28.3 | M28 | 7 | Code | completed | T28.2, T23.2 | — | EV-002 | — |
| T28.4 | M28 | 7 | Code | completed | T28.2, T23.4 | — | EV-002 | — |
| T28.5 | M28 | 7 | Code | completed | T28.2, T23.8 | — | EV-002 | — |
| T28.6 | M28 | 7 | Test | completed | T28.5 | — | EV-002 | — |
| T29.1 | M29 | 7 | Code | completed | T25.5, T21.5 | — | EV-002 | — |
| T29.2 | M29 | 7 | Code | completed | T29.1 | — | EV-002 | — |
| T29.3 | M29 | 7 | Code | completed | T29.1 | — | EV-002 | — |
| T29.4 | M29 | 7 | Code | completed | T29.1, T21.7 | — | EV-002 | — |
| T29.5 | M29 | 7 | Test | completed | T29.3 | — | EV-002 | — |
| T29.6 | M29 | 7 | Test | completed | T29.4 | — | EV-002 | — |
| T30.1 | M30 | 8 | Test | completed | T21.5 | — | EV-002 | — |
| T30.2 | M30 | 8 | Code | completed | T30.1 | — | EV-002 | — |
| T30.3 | M30 | 8 | Docs | completed | T24.6 | — | EV-002 | — |
| T30.4 | M30 | 8 | Test | completed | T29.6, T22.6, T23.2 | D1 | EV-002 | — |
| T31.1 | M31 | 8 | Docs | completed | T30.3 | — | EV-002 | — |
| T31.2 | M31 | 8 | Test | completed | T24.6 | — | EV-002 | — |
| T31.3 | M31 | 8 | Config | completed | T31.2 | — | EV-002 | — |
| T31.4 | M31 | 8 | Config | completed | T31.1 | — | EV-002 | — |
| T31.5 | M31 | 8 | Config | completed | T31.4 | — | EV-002 | — |
| T31.6 | M31 | 8 | Config | completed | T31.5 | — | EV-002 | — |
| T31.7 | M31 | 8 | Config | completed | T31.6 | — | EV-002 | — |
| T31.8 | M31 | 8 | Config | completed | T31.7 | — | EV-002 | — |
| T32.1 | M32 | 9 | Test | completed | — | D10 | EV-004 | F31 |
| T32.2 | M32 | 9 | Config | completed | — | — | EV-004 | F31 |
| T32.3 | M32 | 9 | Config | completed | T32.2 | — | EV-004 | F31 |
| T32.4 | M32 | 9 | Test | completed | T32.3 | — | EV-004 | F31 |
| T33.1 | M33 | 9 | Test | pending | T32.1 | D10 | EV-004 | F31 |
| T33.2 | M33 | 9 | Code | pending | T33.1 | D10 | EV-004 | F31 |
| T33.3 | M33 | 9 | Test | pending | T33.2 | D10 | EV-004 | F31 |
| T33.4 | M33 | 9 | Code | pending | T33.2 | D10 | EV-004 | F31 |
| T33.5 | M33 | 9 | Docs | pending | T33.4 | — | EV-004 | F31 |
| T34.1 | M34 | 9 | Test | pending | T33.2 | D11 | EV-004 | F31 |
| T34.2 | M34 | 9 | Code | pending | T34.1 | D11 | EV-004 | F31 |
| T34.3 | M34 | 9 | Code | pending | T34.2 | D11 | EV-004 | F31 |
| T34.4 | M34 | 9 | Code | pending | T34.2 | D11 | EV-004 | F31 |
| T34.5 | M34 | 9 | Config | pending | T34.4 | D11 | EV-004 | F31 |
| T34.6 | M34 | 9 | Config | pending | T34.5 | D11 | EV-004 | F31 |
| T34.7 | M34 | 9 | Test | pending | T34.6 | D11 | EV-004 | F31 |
| T35.1 | M35 | 9 | Test | pending | T34.3, T33.4 | — | EV-004 | F31 |
| T35.2 | M35 | 9 | Config | pending | T32.3 | — | EV-004 | F31 |
| T35.3 | M35 | 9 | Code | pending | T35.2 | — | EV-004 | F31 |
| T35.4 | M35 | 9 | Code | pending | T35.1, T34.3 | — | EV-004 | F31 |
| T35.5 | M35 | 9 | Code | pending | T34.4, T35.3 | — | EV-004 | F31 |
| T35.6 | M35 | 9 | Test | pending | T35.4, T35.5 | — | EV-004 | F31 |
| T36.1 | M36 | 9 | Test | pending | T34.3 | — | EV-004 | F31 |
| T36.2 | M36 | 9 | Code | pending | T36.1 | — | EV-004 | F31 |
| T36.3 | M36 | 9 | Code | pending | T36.2 | D10 | EV-004 | F31 |
| T36.4 | M36 | 9 | Code | pending | T36.3 | D10 | EV-004 | F31 |
| T36.5 | M36 | 9 | Code | pending | T36.3 | D10 | EV-004 | F31 |
| T36.6 | M36 | 9 | Code | pending | T36.3 | D10 | EV-004 | F31 |
| T36.7 | M36 | 9 | Code | pending | T36.4, T36.5 | — | EV-004 | F31 |
| T36.9 | M36 | 9 | Test | pending | T36.7 | — | EV-004 | F31 |
| T36.10 | M36 | 9 | Test | pending | T36.6 | — | EV-004 | F31 |
| T36.8 | M36 | 9 | Test | pending | T36.6, T36.7, T36.9, T36.10 | — | EV-004 | F31 |
| T37.1 | M37 | 9 | Config | pending | T32.2, T35.6, T36.8 | — | EV-004 | F31 |
| T37.2 | M37 | 9 | Config | pending | T32.3 | — | EV-004 | F31 |
| T37.3 | M37 | 9 | Test | pending | T37.1, T37.2 | — | EV-004 | F31 |
| T38.1 | M38 | 9 | Test | pending | T37.3 | — | EV-004 | F31 |
| T38.2 | M38 | 9 | Config | pending | T38.1 | — | EV-004 | F31 |
| T38.3 | M38 | 9 | Config | pending | T36.8, T35.6 | — | EV-004 | F31 |
| T38.4 | M38 | 9 | Config | pending | T38.3 | — | EV-004 | F31 |
| T39.1 | M39 | 10 | Test | completed | — | — | S003 | F33 |
| T39.2 | M39 | 10 | Test | completed | — | — | S003 | F33 |
| T39.3 | M39 | 10 | Code | completed | T39.1, T39.2 | — | S003 | F33 |
| T39.4 | M39 | 10 | Test | completed | T39.3 | — | S003 | F33 |
| T39.5 | M39 | 10 | Code | completed | T39.4 | — | S003 | F33 |
| T40.1 | M40 | 10 | Test | completed | T39.5 | — | S003 | F33 |
| T40.2 | M40 | 10 | Code | completed | T40.1 | — | S003 | F33 |
| T40.3 | M40 | 10 | Code | completed | T40.2 | — | S003 | F33 |
| T40.4 | M40 | 10 | Test | completed | T40.3 | — | S003 | F33 |
| T41.1 | M41 | 10 | Test | completed | T40.4 | — | S003 | F33 |
| T41.2 | M41 | 10 | Code | completed | T41.1 | — | S003 | F33 |
| T41.3 | M41 | 10 | Code | completed | T41.2 | — | S003 | F33 |
| T41.4 | M41 | 10 | Code | completed | T41.3 | — | S003 | F33 |
| T41.5 | M41 | 10 | Test | completed | T41.4 | — | S003 | F33 |
| T42.1 | M42 | 10 | Config | completed | — | — | S003 | F33 |
| T42.2 | M42 | 10 | Test | completed | T41.5 | — | S003 | F33 |
| T42.3 | M42 | 10 | Test | completed | T41.5, T40.4, T42.2 | — | S003 | F33 |
| T43.1 | M43 | 11 | Config | pending | — | — | S004 | F34 |
| T43.2 | M43 | 11 | Test | pending | — | — | S004 | F34 |
| T43.3 | M43 | 11 | Code | pending | T43.2 | — | S004 | F34 |
| T43.4 | M43 | 11 | Docs | pending | T43.1 | — | S004 | F34 |
| T44.1 | M44 | 11 | Test | pending | — | — | S004 | F34 |
| T44.2 | M44 | 11 | Code | pending | T44.1 | — | S004 | F34 |
| T44.3 | M44 | 11 | Test | pending | T44.2 | — | S004 | F34 |
| T44.4 | M44 | 11 | Config | pending | T44.2 | — | S004 | F34 |
| T45.1 | M45 | 11 | Test | pending | T44.2 | — | S004 | F34 |
| T45.2 | M45 | 11 | Code | pending | T45.1 | — | S004 | F34 |
| T45.3 | M45 | 11 | Test | pending | T45.2 | — | S004 | F34 |
| T45.4 | M45 | 11 | Code | pending | T45.3 | D5 | S004 | F34 |
| T45.5 | M45 | 11 | Test | pending | T45.2 | D5 | S004 | F34 |
| T45.6 | M45 | 11 | Code | pending | T45.5 | D5 | S004 | F34 |
| T45.7 | M45 | 11 | Code | pending | T45.2 | — | S004 | F34 |
| T46.1 | M46 | 11 | Test | pending | — | — | S004 | F34 |
| T46.2 | M46 | 11 | Config | pending | T46.1 | — | S004 | F34 |
| T46.3 | M46 | 11 | Code | pending | T46.2 | — | S004 | F34 |
| T46.4 | M46 | 11 | Code | pending | T46.3 | — | S004 | F34 |
| T46.5 | M46 | 11 | Test | pending | T46.3 | — | S004 | F34 |
| T47.1 | M47 | 11 | Test | completed | T45.2, T45.7 | — | S004 | F34 |
| T47.2 | M47 | 11 | Test | completed | T43.1 | — | S004 | F34 |
| T47.3 | M47 | 11 | Test | completed | T45.4, T45.6 | — | S004 | F34 |
| T47.4 | M47 | 11 | Test | completed | T45.6 | — | S004 | F34 |
| T47.5 | M47 | 11 | Config | completed | T45.2 | — | S004 | F34 |
| T47.6 | M47 | 11 | Test | completed | T47.1, T47.2, T47.3, T47.4, T47.5, T46.5 | — | S004 | F34 |
| T48.1 | M48 | 12 | Test | completed | — | — | S005 | F35 |
| T48.2 | M48 | 12 | Config | completed | T48.1 | — | S005 | F35 |
| T48.3 | M48 | 12 | Config | completed | T48.2 | — | S005 | F35 |
| T48.4 | M48 | 12 | Config | completed | T48.1 | — | S005 | F35 |
| T48.5 | M48 | 12 | Config | completed | T48.4 | — | S005 | F35 |
| T48.6 | M48 | 12 | Docs | completed | T48.2 | — | S005 | F35 |
| T49.1 | M49 | 12 | Test | completed | — | — | S005 | F35 |
| T49.2 | M49 | 12 | Code | completed | T49.1 | — | S005 | F35 |
| T49.3 | M49 | 12 | Test | completed | — | D5 | S005 | F35 |
| T49.4 | M49 | 12 | Code | completed | T49.3 | D5 | S005 | F35 |
| T49.5 | M49 | 12 | Test | completed | T49.2 | — | S005 | F35 |
| T49.6 | M49 | 12 | Code | completed | T49.5 | — | S005 | F35 |
| T50.1 | M50 | 12 | Test | completed | T49.2, T49.6 | — | S005 | F35 |
| T50.2 | M50 | 12 | Code | completed | T50.1, T49.4 | — | S005 | F35 |
| T50.3 | M50 | 12 | Config | completed | T50.2 | — | S005 | F35 |
| T50.4 | M50 | 12 | Code | completed | T50.2 | — | S005 | F35 |
| T50.5 | M50 | 12 | Test | completed | T50.2 | — | S005 | F35 |
| T50.6 | M50 | 12 | Code | completed | T50.5 | — | S005 | F35 |
| T51.1 | M51 | 12 | Test | completed | — | — | S005 | F35 |
| T51.2 | M51 | 12 | Test | completed | — | — | S005 | F35 |
| T51.3 | M51 | 12 | Code | completed | T51.1, T50.2 | — | S005 | F35 |
| T51.4 | M51 | 12 | Test | completed | — | — | S005 | F35 |
| T51.5 | M51 | 12 | Code | completed | T51.4 | — | S005 | F35 |
| T51.6 | M51 | 12 | Test | completed | — | — | S005 | F35 |
| T51.7 | M51 | 12 | Code | completed | T51.6 | — | S005 | F35 |
| T52.1 | M52 | 12 | Test | completed | T50.2, T51.3 | — | S005 | F35 |
| T52.2 | M52 | 12 | Test | completed | T50.2, T51.3 | — | S005 | F35 |
| T52.3 | M52 | 12 | Test | completed | T48.4 | — | S005 | F35 |
| T52.4 | M52 | 12 | Config | completed | T50.2 | — | S005 | F35 |
| T52.5 | M52 | 12 | Test | completed | T52.1–T52.4, T51.5, T51.7 | — | S005 | F35 |
| T52.6 | M52 | 12 | Docs | completed | T48.6 | — | S005 | F35 |
| T53.1 | M53 | 12 | Test | completed | — | — | S005 | F35 |
| T53.2 | M53 | 12 | Code | completed | T53.1 | — | S005 | F35 |
| T53.3 | M53 | 12 | Test | completed | — | — | S005 | F35 |
| T53.4 | M53 | 12 | Code | completed | T53.3 | — | S005 | F35 |
| T53.5 | M53 | 12 | Config | completed | — | — | S005 | F35 |
| T53.6 | M53 | 12 | Test | completed | T49.2, T49.4 | — | S005 | F35 |
| T53.7 | M53 | 12 | Code | completed | T53.6, T53.5 | — | S005 | F35 |
| T53.8 | M53 | 12 | Test | completed | — | 2026-06-30 | S005 | F35 |
| T53.9 | M53 | 12 | Code | completed | T53.8, T53.7 | 2026-06-30 | S005 | F35 |
| T53.10 | M53 | 12 | Test | completed | T50.2 | — | S005 | F35 |
| T53.11 | M53 | 12 | Code | completed | T53.10 | — | S005 | F35 |
| T53.12 | M53 | 12 | Test | completed | — | 2026-06-30 | S005 | F35 |
| T53.13 | M53 | 12 | Code | completed | T53.12, T53.11 | 2026-06-30 | S005 | F35 |
| T53.14 | M53 | 12 | Test | completed | T49.2 | 2026-06-30 | S005 | F35 |
| T53.15 | M53 | 12 | Code | completed | T53.14, T50.2, T51.3 | 2026-06-30 | S005 | F35 |
| T53.16 | M53 | 12 | Test | completed | — | 2026-06-30 | S005 | F35 |
| T53.17 | M53 | 12 | Code | completed | T53.16, T50.2 | 2026-06-30 | S005 | F35 |
| T53.18 | M53 | 12 | Test | completed | T53.7, T53.11 | 2026-06-30 | S005 | F35 |
| T53.19 | M53 | 12 | Code | completed | T53.7, T53.11 | 2026-06-30 | S005 | F35 |
| T53.20 | M53 | 12 | Test | completed | T53.7, T53.11 | 2026-06-30 | S005 | F35 |
| T53.21 | M53 | 12 | Config | completed | T53.7, T53.11, T53.15 | 2026-06-30 | S005 | F35 |
| T53.22 | M53 | 12 | Docs | completed | T53.5 | 2026-06-30 | S005 | F35 |
| T54.1 | M54 | 13 | Test | completed | — | 2026-06-30 | S006 | F35 |
| T54.2 | M54 | 13 | Config | completed | T54.1 | 2026-06-30 | S006 | F35 |
| T54.3 | M54 | 13 | Test | completed | — | 2026-06-30 | S006 | F35 |
| T54.4 | M54 | 13 | Config | completed | T54.3 | 2026-06-30 | S006 | F35 |
| T54.5 | M55 | 13 | Test | completed | T54.4 | 2026-06-30 | S006 | F35 |
| T54.6 | M55 | 13 | Test | completed | T54.4 | 2026-06-30 | S006 | F35 |
| T54.7 | M55 | 13 | Test | completed | T49.2 | 2026-06-30 | S006 | F35 |
| T54.8 | M55 | 13 | Code | completed | T54.5, T54.6 | 2026-06-30 | S006 | F35 |
| T54.9 | M55 | 13 | Code | completed | T54.7 | 2026-06-30 | S006 | F35 |
| T54.10 | M55 | 13 | Test | completed | — | 2026-06-30 | S006 | F35 |
| T54.11 | M55 | 13 | Code | completed | T54.10, T54.8 | 2026-06-30 | S006 | F35 |
| T54.12 | M56 | 13 | Test | completed | — | 2026-06-30 | S006 | F35 |
| T54.13 | M56 | 13 | Test | completed | — | 2026-06-30 | S006 | F35 |
| T54.14 | M56 | 13 | Code | completed | T54.12, T54.13 | 2026-06-30 | S006 | F35 |
| T54.15 | M56 | 13 | Code | completed | T54.14 | 2026-06-30 | S006 | F35 |
| T54.16 | M56 | 13 | Code | completed | T54.14 | 2026-06-30 | S006 | F35 |
| T54.17 | M57 | 13 | Test | completed | — | 2026-06-30 | S006 | F35 |
| T54.18 | M57 | 13 | Test | completed | — | 2026-06-30 | S006 | F35 |
| T54.19 | M57 | 13 | Code | completed | T54.17, T54.18, T54.9 | 2026-06-30 | S006 | F35 |
| T54.20 | M57 | 13 | Code | completed | T54.9 | 2026-06-30 | S006 | F35 |
| T54.21 | M57 | 13 | Config | completed | T54.9, T54.8 | 2026-06-30 | S006 | F35 |
| T54.22 | M58 | 13 | Config | completed | T54.2 | 2026-06-30 | S006 | F35 |
| T54.23 | M58 | 13 | Test | completed | T54.8 | 2026-06-30 | S006 | F35 |
| T54.24 | M58 | 13 | Docs | completed | T54.2, T54.4 | 2026-06-30 | S006 | F35 |
| T59.1 | M59 | 14 | Test | completed | — | — | S007 | F36 |
| T59.2 | M59 | 14 | Test | completed | — | D3 | S007 | F36 |
| T59.3 | M59 | 14 | Code | completed | T59.1 | — | S007 | F36 |
| T59.4 | M59 | 14 | Code | completed | T59.3 | D3 | S007 | F36 |
| T59.5 | M59 | 14 | Test | completed | T59.4 | D3 | S007 | F36 |
| T60.1 | M60 | 14 | Test | completed | T59.4 | D3 | S007 | F36 |
| T60.2 | M60 | 14 | Code | completed | T59.4 | D3 | S007 | F36 |
| T60.3 | M60 | 14 | Code | completed | T60.2 | D3, D7 | S007 | F36 |
| T60.4 | M60 | 14 | Code | completed | T60.3 | — | S007 | F36 |
| T60.5 | M60 | 14 | Code | completed | T59.5, T59.2, T60.1, T60.3, T60.4 | D3 | S007 | F36 |
| T61.1 | M61 | 14 | Code | completed | T59.3 | — | S007 | F36 |
| T61.2 | M61 | 14 | Test | completed | — | — | S007 | F36 |
| T61.3 | M61 | 14 | Test | completed | T60.5 | D3 | S007 | F36 |
| T61.4 | M61 | 14 | Code | completed | T61.1, T60.5 | D3 | S007 | F36 |
| T61.5 | M61 | 14 | Config | completed | T61.4 | — | S007 | F36 |
| T61.6 | M61 | 14 | Test | completed | T61.4 | — | S007 | F36 |
| T61.7 | M61 | 14 | Code | completed | T61.2, T61.3, T61.4 | D3 | S007 | F36 |
| T62.1 | M62 | 14 | Test | completed | — | — | S007 | F36 |
| T62.2 | M62 | 14 | Code | completed | T61.7 | — | S007 | F36 |
| T62.3 | M62 | 14 | Code | completed | T62.2 | D10 | S007 | F36 |
| T62.4 | M62 | 14 | Code | completed | T62.1, T62.2, T62.3 | — | S007 | F36 |
| T63.1 | M63 | 14 | Config | completed | T61.4 | — | S007 | F36 |
| T63.2 | M63 | 14 | Docs | completed | T60.5 | — | S007 | F36 |
| T63.3 | M63 | 14 | Docs | completed | T62.4, T61.7, T60.5 | — | S007 | F36 |
| T63.4 | M63 | 14 | Docs | completed | T63.1–T63.3 | — | S007 | F36 |
| T64.1 | M64 | 14 | Test | completed | T61.7 | — | S007 | F36 |
| T64.2 | M64 | 14 | Code | completed | T64.1 | — | S007 | F36 |
| T64.3 | M64 | 14 | Code | completed | T64.2 | — | S007 | F36 |
| T64.4 | M64 | 14 | Code | completed | T64.3 | — | S007 | F36 |
| T64.5 | M64 | 14 | Test | completed | — | — | S007 | F36 |
| T64.6 | M64 | 14 | Code | completed | T64.3 | D10 | S007 | F36 |
| T64.7 | M64 | 14 | Code | completed | T64.4–T64.6 | — | S007 | F36 |
| T64.8 | M64 | 14 | Docs | completed | T64.7 | — | S007 | F36 |
| T65.1 | M65 | 15 | Test | pending | — | — | S008 | F36 |
| T65.2 | M65 | 15 | Code | pending | T65.1 | — | S008 | F36 |
| T65.3 | M65 | 15 | Code | pending | T65.1, T65.2 | — | S008 | F36 |
| T66.1 | M66 | 15 | Test | pending | — | D3 | S008 | F36 |
| T66.2 | M66 | 15 | Test | pending | — | — | S008 | F36 |
| T66.3 | M66 | 15 | Code | pending | — | — | S008 | F36 |
| T66.4 | M66 | 15 | Code | pending | T66.3 | — | S008 | F36 |
| T66.5 | M66 | 15 | Test | pending | T66.4 | — | S008 | F36 |
| T66.6 | M66 | 15 | Code | pending | T66.1–T66.4 | D3 | S008 | F36 |
| T67.1 | M67 | 15 | Test | pending | — | — | S008 | F36 |
| T67.2 | M67 | 15 | Code | pending | T67.1 | — | S008 | F36 |
| T67.3 | M67 | 15 | Code | pending | T67.2 | — | S008 | F36 |
| T67.4 | M67 | 15 | Test | pending | T67.3 | — | S008 | F36 |
| T67.5 | M67 | 15 | Code | pending | T67.1–T67.3 | — | S008 | F36 |
| T68.1 | M68 | 15 | Test | pending | — | — | S008 | F37 |
| T68.2 | M68 | 15 | Code | pending | T68.1 | — | S008 | F37 |
| T68.3 | M68 | 15 | Code | pending | T68.2 | — | S008 | F37 |
| T68.4 | M68 | 15 | Test | pending | T68.3 | — | S008 | F37 |
| T68.5 | M68 | 15 | Code | pending | T68.3 | — | S008 | F37 |
| T68.6 | M68 | 15 | Code | completed | T68.3, T61.4 | D3 | S008 | F37 |
| T68.7 | M68 | 15 | Code | completed | T68.6, T60.5 | D3 | S008 | F37 | 2026-07-02 |
| T68.8 | M68 | 15 | Config | pending | T68.5, T68.6 | — | S008 | F37 |
| T68.9 | M68 | 15 | Code | pending | T68.4, T68.5, T68.7 | — | S008 | F37 |
| T69.1 | M69 | 15 | Test | pending | — | — | S008 | F37 |
| T69.2 | M69 | 15 | Test | pending | — | — | S008 | F37 |
| T69.3 | M69 | 15 | Code | pending | T68.9 | D10 | S008 | F37 |
| T69.4 | M69 | 15 | Code | pending | T69.3, T68.5 | — | S008 | F37 |
| T69.5 | M69 | 15 | Code | pending | T69.3 | — | S008 | F37 |
| T69.6 | M69 | 15 | Code | pending | T69.3 | — | S008 | F37 |
| T69.7 | M69 | 15 | Test | pending | T68.7 | D3 | S008 | F37 |
| T69.8 | M69 | 15 | Test | pending | T69.6 | — | S008 | F37 |
| T69.9 | M69 | 15 | Code | pending | T69.1–T69.8 | D3 | S008 | F37 |
| T70.1 | M70 | 15 | Code | pending | — | — | S008 | F37 |
| T70.2 | M70 | 15 | Test | pending | T70.1 | — | S008 | F37 |
| T70.3 | M70 | 15 | Code | pending | T68.2, T70.1 | — | S008 | F37 |
| T70.4 | M70 | 15 | Code | pending | T68.2 | — | S008 | F37 |
| T70.5 | M70 | 15 | Test | pending | T70.4 | — | S008 | F37 |
| T70.6 | M70 | 15 | Code | pending | T70.3, T69.4 | — | S008 | F37 |
| T70.7 | M70 | 15 | Config | pending | T70.1 | — | S008 | F37 |
| T70.8 | M70 | 15 | Docs | pending | T65.3–T70.6 | — | S008 | F37 |

## Phase Gate Log

| Phase | Gate Check Date | Result | Notes |
|-------|----------------|--------|-------|
| 1 | 2026-05-19 | **pass** | M1–M3 complete; alembic head; 12 pytest smoke/privacy/seed; ruff/pyright; OpenAPI in repo + api-contract.md |
| 2 | 2026-05-19 | **pass** | E2E UJ-002/006/008 (4 tests incl. UJ-003); ruff/pyright clean; 36 pytest; Modal README + apps; no DATABASE_URL in Modal paths |
| 3 | — | — | — |
| 4 | 2026-05-19 | **partial** | Automation PASS (CI main green, ruff/pyright/pytest/vitest, UJ-004 bootstrap, eval ≥80%). **Deferred:** live staging H1–H3 (no deploy URLs); D6/D7 Modal weights until first `modal deploy`. |
| 5 | 2026-05-24 | **pass** | EV-001 merged PR-24; CI main green (run 26373983464); UJ-009/011/012 E2E; TC-046/049 H0c; TC-048 Vitest; D8/D9 verified. **Deferred:** live staging H3b/H4/H5 — operator post-deploy per staging-runbook. |
| 12 | 2026-06-30 | **partial (build PASS)** | EV-006/F35 07-build close-out. Build criteria PASS: M48–M53 (T48.1–T53.22) complete; `make check` green (ruff/basedpyright/ESLint + Prettier); 496 pytest unit + all frontend Vitest suites green; TC-088–TC-103 covered; CORS preflight (T53.19) + privacy (TC-102) + 503 fallback (TC-098) covered. **Deferred to 13-deploy-smoke:** AC-U1–U16 live Resend delivery, live audit_log rows, secret placement on Modal DM, SMTP/SPF/DKIM/DMARC sync. Fixed typecheck blocker in DM user-admin unit test (private-helper import → shared `tests.helpers.user_admin_mocks`). |

## Hook Configuration

| Hook | Event | Tool | Config | Purpose |
|------|-------|------|--------|---------|
| Lint/format | afterFileEdit | Ruff | `pyproject.toml` | Style + lint |
| Typecheck | afterFileEdit | basedpyright | `pyrightconfig.json` / `[tool.basedpyright]` | No `Any` (ADR-018) |
| Scope | afterFileEdit | scope_check.py | `.cursor/hooks/` | Plan drift |

CI: `.github/workflows/ci.yml` (06-tech-tooling). Cursor hooks: lint, format, basedpyright, template-check, pre-task, post-test-sync, pr-checklist. Typing policy: `docs/typing-policy.md`.

## Modal test tiers (ADR-004 / test-plan)

| Tier | When | Tasks |
|------|------|-------|
| T0 | Unit | All packages — mocked I/O |
| T1 | Integration | DO APIs + test Postgres — mocked Modal HTTP |
| T2 | Local E2E | UJ-001–012 — docker-compose + mocks |
| T3 | Live staging | Post T14.3 / T19.4 — 10-e2e / 15-service-health |

## Open Questions

- [x] Gateway R6 — deferred (direct URLs)
- [x] vLLM model — Qwen2.5-1.5B-Instruct on T4
- [x] Cost gate — pilot fits ≤ $50 with scale-to-zero; consolidate DO if overrun
- [x] EV-005 JWT verification — HS256 shared secret `SUPABASE_JWT_SECRET` (TP-S004-01, ADR-027)
- [x] EV-005 role source — `app_metadata.role`, read from verified JWT (TP-S004-02)
- [x] EV-005 deps — PyJWT `>=2.10,<3`; `@supabase/supabase-js ^2.108.2` (TP-S004-04)
- [x] EV-005 env sync — Supabase Pro + ephemeral branching + CLI migrations-in-repo (TP-S004-07)
- [x] EV-005 cost cap — raised to ~$75/mo, supersedes ADR-004 (TP-S004-06, ADR-027)
- [x] EV-005 invites / first-admin — `inviteUserByEmail` + custom SMTP; idempotent seed script (TP-S004-08/10)
- [x] EV-001 ingest tagging step — after chunk, before embed (TP-010)
- [x] EV-001 admin retag — async Modal job via `jobs.job_type=retag` (TP-011, TP-012)
- [x] EV-001 retrieval SQL — union match document OR chunk (TP-013)
- [x] EV-001 tag inference — same vLLM (TP-014)
- [ ] Exact LlamaIndex patch versions — pin at T8.1 during build
- [x] EV-002 Tailwind version — v3 (TP-018)
- [x] EV-002 Health dashboard architecture — aggregator on internal-write-api (TP-019)
- [x] EV-002 Stats refresh — real-time SQL (TP-020)
- [x] EV-002 React Router — v7 (TP-021)
- [x] EV-002 Serving stats — async fire-and-forget (TP-022)
- [x] EV-002 Audit emission — explicit helper calls (TP-023)
- [x] EV-002 Bulk transactions — partial success (TP-024)
- [x] EV-002 Version snapshots — on audit event (TP-025)
- [x] EV-002 shadcn/ui — npx init (TP-026)
- [x] EV-002 Audit retention — background cleanup job (TP-027)
- [x] EV-002 Frontend testing — Vitest + Testing Library (TP-028)
- [x] EV-002 Deploy order — migration → write-api → chat-rag → frontend (TP-029)
- [x] EV-004 git branch — continue `fix/es-en-full-ui` (TP-030)
- [x] EV-004 package consumption — source imports via npm workspaces (TP-031)
- [x] EV-004 message typing — strict TypeScript keys (TP-032)
- [x] EV-004 ChatRAG Tailwind — full layout migration (TP-033)
- [x] EV-004 locale default — ES fallback (TP-034)
- [x] EV-004 CI — root npm workspaces (TP-035)
- [x] EV-004 component extraction — full ADR-020 surface (TP-036)
- [x] EV-004 admin strings — all pages ~120+ keys (TP-037)
- [x] EV-004 deploy order — simultaneous both frontends (TP-038)
- [x] EV-004 connectivity — extend H4/H5 smoke (TP-039)
- [x] S003 storage key + schema — `vecinita.chat.history.v1`, versioned envelope (TP-S003-01, ADR-024)
- [x] **S003 storage mechanism — `localStorage`** (durable, cross-tab) per **ADR-025** (2026-06-28, 07-build reopened); reverses the `sessionStorage` choice in ADR-023/024 (R41/R43) at the user's request. Frontend-only; no API/contract/CORS change.
- [x] S003 persistence architecture — `useConversationStore` in shell (TP-S003-02, ADR-024)
- [x] S003 previous-chats UI — collapsible panel in ChatPanel (TP-S003-03, ADR-024)
- [x] S003 label — first user msg ≤60 chars + `Intl.RelativeTimeFormat` (TP-S003-05)
- [x] S003 failure mode — degrade silently to in-memory (TP-S003-09, TC-073)
- [ ] **S003/EV-004 i18n merge coordination** — new chat-history keys added app-local; port to `packages/frontend-i18n` on second merge (TP-S003-04)
- [x] EV-008 eval tooling — LlamaIndex evaluators + custom harness; no Langfuse/Ragas/DeepEval v1 (TP-S007-01, ADR-033)
- [x] EV-008 runner placement — DO BackgroundTasks on internal-write-api; not new Modal app v1 (TP-S007-04)
- [x] EV-008 viewer policy — admin-only eval routes; viewer → 403 (TP-S007-06, RD-110)
- [x] EV-008 #84 coordination — `GroundednessScorer` adapter stub; FaithfulnessEvaluator default (TP-S007-09)
- [x] EV-009 build order — M65→M70 UX first, playground last (TP-S008-01, R70)
- [x] EV-009 unified jobs — DM backend HTTP aggregate eval runs (TP-S008-03, RD-116)
- [x] EV-009 playground model — fixed Modal LLM; no picker v1 (TP-S008-06, RD-132)
- [x] EV-009 ChatRAG config — direct Postgres read + env fallback (TP-S008-12, RD-134)
- [x] EV-009 super-admin — `VECINITA_SUPER_ADMIN_EMAIL` seed (TP-S008-10, RD-127)
