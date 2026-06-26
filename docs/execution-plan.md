# Execution Plan

> **Project**: Vecinita  
> **Generated**: 2026-05-19 (EV-001 delta 2026-05-24; EV-002 delta 2026-05-26; EV-004 delta 2026-06-13; S003 delta 2026-06-26)  
> **Skill**: 04-tech-plan  
> **Specs consumed**: feature-list.md, spec.md, user-journeys.md, test-plan.md, config-spec.md, api-contract.md, data-management-plan.md, deployment-integration.md, dependency-inventory.md, acceptance-criteria.md, ADR-001–021

## Current State

| Field | Value |
|-------|-------|
| **Active phase** | Phase 9: EV-004 shared frontend i18n/UI |
| **Active milestone** | M32: Workspace scaffold |
| **Active task** | M33 / T33.1 |
| **Tasks completed** | 201 / 239 |
| **Last updated** | 2026-06-26 |
| **Evolve cycle** | EV-004 (F31) — **in_progress** |
| **Git branch** | `feat/M32-workspace-scaffold` |
| **Active session** | S003-persistent-chat-history (Phase 10, F33) — 07-build **in progress**: M39–M41 complete (store + rehydration + previous-chats UI/i18n; 113 FE tests + 95% coverage green); next M42 privacy/full-suite; on `feat/S003-persistent-chat-history` |

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
| Language (Node) | **20 LTS** | dependency-inventory.md | Frontends |
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
- [x] Cost estimate documented ≤ $50 (`docs/cost-monitoring.md` pilot ~$42–48/mo)
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
- [x] Cost note: EV-001 LLM tagging within ≤ $50/mo pilot cap (ADR-015 TP-017) — see `docs/cost-monitoring.md`

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

**Objective**: `sessionStorage`-backed conversation store; rehydrate the active conversation
across refresh/tab-away; previous-chats list with new-chat / select / delete / clear;
EN/ES i18n; graceful in-memory fallback. **Frontend-only** in `apps/chat-rag-frontend`.
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
| T42.1 | Config: verify `.cursor/rules/frontend-session-state-lifting.mdc` device-only `sessionStorage` allowance (updated in 04-tech-plan) + its `test_chat_history_persistence` regression-guard reference resolves | Config | pending | TP-S003-11, ADR-024 | T41.5 | — | S003 | F33 |
| T42.2 | Test: AC-S6 — no `POST` carries history; no server session/message row; persistence per-tab | Test | pending | acceptance-criteria AC-S6, ADR-023 | T41.5 | — | S003 | F33 |
| T42.3 | Test: full chat-rag-frontend Vitest suite green incl. existing bug tests | Test | pending | test-plan §Frontend | T41.5, T40.4, T42.2 | — | S003 | F33 |

#### Phase 10 Gate Check

- [ ] All M39–M42 tasks completed (239/239)
- [ ] TC-072–TC-076 green; UJ-024/UJ-025 covered (Vitest + jsdom `sessionStorage`)
- [ ] AC-S1–AC-S7 met
- [ ] Graceful fallback verified (TC-073, AC-S2)
- [ ] `.cursor/rules/frontend-session-state-lifting.mdc` updated (ADR-023/024)
- [ ] No API/contract/CORS changes (AC-S7); no backend/Modal redeploy
- [ ] chat-rag-frontend Vitest suite green (incl. #53 navigation guard)

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
| PR-46 | Major | Phase 10 / S003 | feat/S003-persistent-chat-history | main | pending |

S003 is evolve-lite + frontend-only: M39–M42 land as atomic commits on the single
`feat/S003-persistent-chat-history` branch (one PR to `main`, PR-46), matching the S002 pattern.

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
| T42.1 | M42 | 10 | Config | pending | — | — | S003 | F33 |
| T42.2 | M42 | 10 | Test | pending | T41.5 | — | S003 | F33 |
| T42.3 | M42 | 10 | Test | pending | T41.5, T40.4, T42.2 | — | S003 | F33 |

## Phase Gate Log

| Phase | Gate Check Date | Result | Notes |
|-------|----------------|--------|-------|
| 1 | 2026-05-19 | **pass** | M1–M3 complete; alembic head; 12 pytest smoke/privacy/seed; ruff/pyright; OpenAPI in repo + api-contract.md |
| 2 | 2026-05-19 | **pass** | E2E UJ-002/006/008 (4 tests incl. UJ-003); ruff/pyright clean; 36 pytest; Modal README + apps; no DATABASE_URL in Modal paths |
| 3 | — | — | — |
| 4 | 2026-05-19 | **partial** | Automation PASS (CI main green, ruff/pyright/pytest/vitest, UJ-004 bootstrap, eval ≥80%). **Deferred:** live staging H1–H3 (no deploy URLs); D6/D7 Modal weights until first `modal deploy`. |
| 5 | 2026-05-24 | **pass** | EV-001 merged PR-24; CI main green (run 26373983464); UJ-009/011/012 E2E; TC-046/049 H0c; TC-048 Vitest; D8/D9 verified. **Deferred:** live staging H3b/H4/H5 — operator post-deploy per staging-runbook. |

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
- [x] S003 persistence architecture — `useConversationStore` in shell (TP-S003-02, ADR-024)
- [x] S003 previous-chats UI — collapsible panel in ChatPanel (TP-S003-03, ADR-024)
- [x] S003 label — first user msg ≤60 chars + `Intl.RelativeTimeFormat` (TP-S003-05)
- [x] S003 failure mode — degrade silently to in-memory (TP-S003-09, TC-073)
- [ ] **S003/EV-004 i18n merge coordination** — new chat-history keys added app-local; port to `packages/frontend-i18n` on second merge (TP-S003-04)
