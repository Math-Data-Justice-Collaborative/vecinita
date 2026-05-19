# Execution Plan

> **Project**: Vecinita  
> **Generated**: 2026-05-19  
> **Skill**: 04-tech-plan  
> **Specs consumed**: feature-list.md, spec.md, user-journeys.md, test-plan.md, config-spec.md, api-contract.md, data-management-plan.md, deployment-integration.md, dependency-inventory.md, acceptance-criteria.md, ADR-001–013

## Current State

| Field | Value |
|-------|-------|
| **Active phase** | Phase 3: ChatRAG |
| **Active milestone** | Phase 4 complete (gate partial) |
| **Active task** | 11-verify-impl / deploy when ready |
| **Tasks completed** | 72 / 73 |
| **Last updated** | 2026-05-19 |

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
| Linter | **Ruff** | hooks + 03-plan-tooling | test-plan.md |
| Formatter | **Ruff format** | hooks | test-plan.md |
| Typechecker | **Pyright** | 04-tech-plan; `.cursor/hooks/typecheck.py` | test-plan.md (supersedes mypy) |
| Test runner | **pytest** | test-plan.md | §Test Strategy |
| Frontend tests | **Vitest** | test-plan.md | Frontends |
| Package manager | **uv** | hooks (`uv run`) | monorepo workspace |
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

**Data management gate:** Assets must be `verified` in `docs/data-staging-state.md` before dependent tasks start.

## Implementation Phases

### Phase 1: Foundation

**Objective:** Monorepo scaffold, database schema, privacy guardrails, OpenAPI skeletons, dev tooling baseline.  
**Entry gate:** Execution plan approved (04-tech-plan Phase 4).  
**Exit gate:** Migrations apply on empty DB; privacy tests pass; ruff + pyright clean on scaffold; pytest runs (smoke).

#### M1: Monorepo scaffold

**Goal:** `apps/*`, `packages/*`, `infra/`, `tests/` layout per template-conformance.mdc.  
**Branch:** `feat/M1-monorepo-scaffold` → `phase/1-foundation`

| # | Task | Type | Status | Spec Source | Depends On | Data Deps |
|---|------|------|--------|-------------|------------|-----------|
| T1.1 | Create directory layout (`apps/*` incl. `internal-write-api`, `packages/`, `openapi/`, `tests/`) | Config | completed | spec.md §Component Overview, ADR-010 | — | — |
| T1.2 | Root `pyproject.toml` uv workspace + Python 3.11 pin | Config | completed | dependency-inventory.md | T1.1 | — |
| T1.3 | Placeholder `__init__.py` / package stubs per app | Config | completed | ADR-012 | T1.2 | — |
| T1.4 | Test: smoke import all packages (`tests/smoke/test_imports.py`) | Test | completed | test-plan.md §Smoke | T1.3 | — |
| T1.5 | Configure ruff + pyright (`pyproject.toml`, `pyrightconfig.json`) | Config | completed | 04-tech-plan | T1.2 | — |
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
- [x] ruff + pyright clean
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
- [ ] Coverage ≥ 80% on `packages/rag`, `packages/ingest`, backends (per test-plan)
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
| T13.1 | GitHub Actions: ruff, pyright, pytest, pip-audit (blocking) | Config | completed | test-plan §CI/CD | T1.5 | — |
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
- [ ] Staging `/health` and sample ask succeed — **deferred**: no `VECINITA_STAGING_*` URLs; run `scripts/deploy/staging_smoke.sh` after DO/Modal deploy
- [x] Cost estimate documented ≤ $50 (`docs/cost-monitoring.md` pilot ~$42–48/mo)
- [ ] `docs/data-staging-state.md` all required assets `verified` — D1–D5 verified; **D6/D7 pending** (Modal weights on first deploy)

---

## Git Strategy

### Commit rules

Atomic commits per task: `[T1.1] type: description`. Post-commit: ruff, pyright, full pytest.

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

## Phase Gate Log

| Phase | Gate Check Date | Result | Notes |
|-------|----------------|--------|-------|
| 1 | 2026-05-19 | **pass** | M1–M3 complete; alembic head; 12 pytest smoke/privacy/seed; ruff/pyright; OpenAPI in repo + api-contract.md |
| 2 | 2026-05-19 | **pass** | E2E UJ-002/006/008 (4 tests incl. UJ-003); ruff/pyright clean; 36 pytest; Modal README + apps; no DATABASE_URL in Modal paths |
| 3 | — | — | — |
| 4 | 2026-05-19 | **partial** | Automation PASS (CI main green, ruff/pyright/pytest/vitest, UJ-004 bootstrap, eval ≥80%). **Deferred:** live staging H1–H3 (no deploy URLs); D6/D7 Modal weights until first `modal deploy`. |

## Hook Configuration

| Hook | Event | Tool | Config | Purpose |
|------|-------|------|--------|---------|
| Lint/format | afterFileEdit | Ruff | `pyproject.toml` | Style + lint |
| Typecheck | afterFileEdit | Pyright | `pyrightconfig.json` | Types |
| Scope | afterFileEdit | scope_check.py | `.cursor/hooks/` | Plan drift |

CI: `.github/workflows/ci.yml` (06-tech-tooling). Cursor hooks: lint, format, pyright, template-check, pre-task, post-test-sync, pr-checklist.

## Modal test tiers (ADR-004 / test-plan)

| Tier | When | Tasks |
|------|------|-------|
| T0 | Unit | All packages — mocked I/O |
| T1 | Integration | DO APIs + test Postgres — mocked Modal HTTP |
| T2 | Local E2E | UJ-001–008 — docker-compose + mocks |
| T3 | Live staging | Post T14.3 — 10-e2e / 15-service-health |

## Open Questions

- [x] Gateway R6 — deferred (direct URLs)
- [x] vLLM model — Qwen2.5-1.5B-Instruct on T4
- [x] Cost gate — pilot fits ≤ $50 with scale-to-zero; consolidate DO if overrun
- [ ] Exact LlamaIndex patch versions — pin at T8.1 during build
- [x] DO App Platform component YAML — finalize at T14.1
