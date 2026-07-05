# Audits

Consolidated product and technical plan audit reports.

## Product plan audit report

> **Stage**: 02-verify-plan  
> **Started**: 2026-05-19  
> **Status**: completed (2026-06-13 EV-004 F31 delta)  
> **Partial re-run**: 2026-05-24 (EV-001 F19–F22 delta audit)

## Document inventory

| # | Document | Path | Sections (approx) | Statements | Status |
|---|----------|------|-------------------|------------|--------|
| 1 | Feature List | docs/feature-list.md | 4 | 22 | Pass 1 done |
| 2 | Spec | docs/spec.md | 6 | 14 | Pass 1 done |
| 3 | User Journeys | docs/user-journeys.md | 2 | 8 | Pass 1 done |
| 4 | Test Plan | docs/test-plan.md | 6 | 6 | Pass 1 done |
| 5 | Config Spec | docs/config-spec.md | 5 | 6 | Pass 1 done |
| 6 | API Contract | docs/api-contract.md | 4 | 4 | Pass 1 done |
| 7 | Acceptance Criteria | docs/acceptance-criteria.md | 4 | 4 | Pass 1 done |
| 8 | Deployment Integration | docs/deployment-integration.md | 5 | 4 | Pass 1 done |
| 9 | Data Management Plan | docs/data-management-plan.md | 4 | 3 | Pass 1 done |
| 10 | Dependency Inventory | docs/dependency-inventory.md | 3 | 3 | Pass 1 done |
| 11 | Roadmap | docs/sessions/S000-internal-docs-archive/reference.md#roadmap | 2 | 2 | Pass 1 done |
| 12 | Glossary | docs/sessions/S000-internal-docs-archive/reference.md#glossary | 1 | 2 | Pass 1 done |
| 13 | Risk Register | docs/sessions/S000-internal-docs-archive/reference.md#risk-register | 2 | 3 | Pass 1 done |

Skipped (reference input): `docs/decisions.md#requirements-decisions-01-requirements`, `context-brief.md`.

---

## Pass 1 — Auto-approved (high confidence)

**Count: 28** — derived directly from `docs/decisions.md#requirements-decisions-01-requirements` and interview ADRs.

| Stmt ID | Section | Statement (summary) | Source |
|---------|---------|---------------------|--------|
| S1.1 | F1 | Bilingual community Q&A (EN/ES) in v1 | RD-002 |
| S1.2 | F2 | Streaming query responses | RD-002 |
| S1.3 | F3 | Stateless chat — no server-side history | RD-002, ADR-004 |
| S1.4 | F4 | LlamaIndex RAG orchestration in `packages/rag` | RD-005, ADR-006 |
| S1.5 | F5 | pgvector retrieval on DO Postgres | RD-002, ADR-005 |
| S1.6 | F7 | URL scrape → chunk → embed → store pipeline | RD-003 |
| S1.7 | F8 | Ingest job queue & status API | RD-003 |
| S1.8 | F9 | Corpus list/delete for operators | RD-003 |
| S1.9 | F10 | FastEmbed 384-dim on Modal | RD-007 |
| S1.10 | F11 | ChatRAG React/Vite frontend | RD-004 |
| S1.11 | F12 | Data management admin SPA | RD-004 |
| S1.12 | F13 | Alembic migrations + pgvector | RD-009 |
| S1.15 | F15 | Privacy schema guardrails + CI tests | ADR-004 |
| S1.16 | F16 | Infra-only protection for data-mgmt APIs | ADR-004 |
| S1.17 | F17 | Basic observability; no raw prompts in persistent logs | RD-010 |
| S1.18 | F18 | Local dev: docker-compose + Modal serve | RD-011 |
| S2.1 | Overview | Five-application monorepo, hybrid Modal + DO | ADR-001, ADR-002 |
| S2.2 | Architecture | Only DO backends hold `DATABASE_URL` | RD-016, ADR-007 |
| S2.3 | ChatRAG | Routes `POST /api/v1/ask` and `/ask/stream` | RD-018 |
| S2.4 | ChatRAG | p95 latency target < 15s (excl. cold start) | RD-017 |
| S2.5 | Data mgmt | Modal ASGI with `requires_proxy_auth` | RD-019 |
| S2.6 | Constraints H5 | Zero personal data — forbidden tables list | ADR-004 |
| S2.7 | Constraints H6 | No paid third-party LLM/embed as default | ADR-004 |
| S2.8 | Constraints H7 | Cost ≤ $50/mo cap, $25 target | ADR-004, RD budget |
| S2.9 | Constraints H2 | US-only regions (nyc1/sfo3) | R10a interview |
| S2.10 | Constraints H3 | OpenAPI required in repo | RD-020 |
| S2.11 | Package rule | `packages/*` must not import `apps/*` | RD-014 |
| S2.12 | Modal LLM | vLLM primary on Modal (ADR-009) | RD-021 |
| S3.1–S3.8 | Journey index | UJ-001 through UJ-008 defined | Feature matrix |
| S4.1 | E2E tier | v1 E2E is local only with mocked Modal | User journeys header |
| S4.2 | Coverage | ≥ 80% on packages + backends | test-plan §Metrics |
| S5.1 | Config | `VECINITA_TOP_K` default 5 | RD interview |
| S5.2 | Config | `VECINITA_CHUNK_SIZE_TOKENS` default 256 | RD interview |
| S5.3 | Config | Embedding dimension 384 | RD-007 |
| S6.1 | ChatRAG API | Public `/ask` — no auth | RD-002 |
| S8.1 | Deploy | vLLM on Modal `vecinita-llm` | RD-021 |
| S8.2 | Deploy | Multi-app DO topology selected | RD-022 |
| S10.1 | Deps | LlamaIndex core; LangGraph excluded v1 | RD-005 |
| S10.2 | Deps | vLLM primary LLM package | RD-021 |

---

## Consistency check results

| Check | Result | Notes |
|-------|--------|-------|
| Feature ↔ Spec | **Pass** | F1–F18 map to spec components |
| Feature ↔ Journey | **Pass** | All in-scope features covered by UJ-001–008 |
| Journey ↔ Test | **Pass** | Each UJ has planned `tests/e2e/` module + TC IDs |
| Feature ↔ Test | **Pass** | TC-001–031 cover feature areas |
| Spec ↔ Config | **Pass** | `VECINITA_LLM_BACKEND` default `vllm` (C1 resolved) |
| Test ↔ Acceptance | **Pass** | AC-* reference TC/UJ IDs |
| Cross-doc naming | **Minor** | "internal write API" consistent; path prefix TBD |
| Scope boundaries | **Pass** | Out-of-scope aligned across feature-list + spec |
| Template (api+worker) | **Pass** | DO HTTP APIs + Modal workers/GPU; not utility-only |

### Contradictions surfaced

| ID | Statements | Issue |
|----|------------|-------|
| **C1** | S5.4 vs S2.12 | ~~config-spec default `ollama`~~ → **resolved**: default `vllm` |
| **C2** | S1.6 vs S2.12 | ~~F6 TBD~~ → **resolved**: vLLM primary in feature-list |
| **C3** | S2.13 vs S2.12 | ~~spec overview TBD~~ → **resolved**: vLLM primary in spec |
| **C4** | ADR-001 vs S1.4 | ~~ADR-001 LangGraph~~ → **resolved**: LlamaIndex in ADR-001 |

---

## Reviewed (medium / low) — all verdicts recorded

See [decisions.md#Product decisions](decisions.md#product-decisions-02-verify-plan). Contradictions C1–C4 resolved 2026-05-19.

## Partial re-run (2026-05-19) — post-audit drift

**Scope:** Re-checked all 13 audited product-plan docs (untracked in git; no file-level diff since initial audit). Cross-doc consistency + leftover stale text.

| ID | Finding | Action |
|----|---------|--------|
| **D1** | feature-list F14 summary still said "pending"; F1 params still "TBD in config-spec" | Fixed → config-spec defaults + S1.13 source |
| **D2** | deployment-integration checklist "seed corpus staging only" vs data-management-plan prod fixtures (S9.2) | Fixed checklist wording |
| **D3** | ADR-001 data-mgmt frontend listed "tags, invites" vs ADR-004 forbidden `invites` | Fixed → corpus/jobs/status only |
| **D4** | requirements-decisions RD-006 read as open choice after RD-021 | Clarified vLLM default in RD-006 row |

**Consistency (partial):** All 9 checks **Pass** after D1–D4. Deferred items unchanged: R6 gateway (ISS-003), vLLM GPU sizing (04-tech-plan), cost proof ≤ $50/mo.

---

## Summary

| Metric | Count |
|--------|-------|
| Documents audited | 13 |
| Total statements | 52 |
| Auto-approved (high) | 28 (54%) |
| User-approved (medium/low) | 19 (37%) |
| Modified | 6 (12%) |
| Denied | 0 |
| Skipped | 0 |
| Contradictions found | 4 |
| Contradictions resolved | 4 |

**Source documents updated:** 11 files — initial 8 + partial re-run (`feature-list.md`, `deployment-integration.md`, `adr/ADR-001-five-app-architecture.md`, `docs/decisions.md#requirements-decisions-01-requirements`).

**Next step:** [03-plan-tooling](.cursor/skills/03-plan-tooling/SKILL.md) — rewrite stale RFantibody `.cursor/rules/` (ISS-001).

---

## EV-001 delta audit (2026-05-24)

**Scope:** F19–F22 product docs updated in 01-requirements (ADR-014). Full consistency pass across 13 spec documents; focus on new journeys UJ-009–UJ-012 and tag/browse connectivity.

### Auto-approved (high confidence) — 14 statements

Derived from `docs/decisions.md#requirements-decisions-01-requirements` RD-024–RD-033 and ADR-014:

| Stmt ID | Statement (summary) | Source |
|---------|---------------------|--------|
| S-EV1.1 | F19 public corpus browse + tag filter on ChatRAG | RD-033 |
| S-EV1.2 | F20 LLM auto-tag at ingest + admin re-tag | RD-033 |
| S-EV1.3 | F21 admin chunk viewer & tag editor | RD-033 |
| S-EV1.4 | F22 tag-aware RAG (user filter + LLM inference) | RD-033 |
| S-EV1.5 | Chunk tags union with document tags at retrieval | RD-025 |
| S-EV1.6 | Browse opens external source URL only (no in-app reader) | RD-026 |
| S-EV1.7 | User-selected tags only when set; LLM infers when none | RD-027 |
| S-EV1.8 | Max 10 document / 5 chunk tags | RD-028 |
| S-EV1.9 | Browse: tags + title/URL search; 20 per page | RD-029 |
| S-EV1.10 | Tag labels match `document.language` (en/es) | RD-030 |
| S-EV1.11 | Seed tag vocabulary in fixtures/DB | RD-031 |
| S-EV1.12 | Tag filter chips in chat sidebar | RD-032 |
| S-EV1.13 | Public read routes on chat-rag-backend only | ADR-014 |
| S-EV1.14 | UJ-009–UJ-012 mapped to F19–F22 | Feature matrix |

### Consistency check (EV-001)

| Check | Result | Notes |
|-------|--------|-------|
| Feature ↔ Spec | **Pass** | F19–F22 in spec.md components + data flow |
| Feature ↔ Journey | **Pass** | UJ-009–012 cover F19–F22 |
| Journey ↔ Test | **Pass** (after C2 fix) | UJ-009–012 have planned e2e modules + TC IDs |
| Feature ↔ Test | **Pass** (after C1 fix) | TC-040–047 cover EV-001 |
| Spec ↔ Config | **Pass** | `VECINITA_BROWSE_PAGE_SIZE`, tag caps in config-spec |
| Test ↔ Acceptance | **Pass** (after C1 fix) | AC-T1–T7 reference TC/UJ IDs |
| Connectivity | **Pass** | deployment-integration EV-001 H4; TC-046; redeploy order documented |
| Scope boundaries | **Pass** | No public write paths; admin via internal-write only |

### Contradictions resolved (EV-001)

| ID | Issue | Resolution |
|----|-------|------------|
| **C1** | AC-T3 cited TC-043 (admin limits) for ingest LLM tags | Added **TC-047**; AC-T3 → TC-047 |
| **C2** | test-plan E2E table said UJ-001–008 only | Fixed → **UJ-001–012** |

### Reviewed (medium / low)

| Stmt ID | Verdict | Action |
|---------|---------|--------|
| S-EV1.15 | approved | Admin `VITE_VECINITA_CORPUS_API_KEY` acceptable v1 (ADR-014 known weakness) |

**Deferred to 04-tech-plan (not blocking):** admin retag sync vs async; SQL union semantics for chunk tag overrides (requirements-decisions unresolved list).

### EV-001 summary

| Metric | Count |
|--------|-------|
| New statements audited | 17 |
| Auto-approved (high) | 14 |
| User-approved / modified | 3 |
| Contradictions found | 2 |
| Contradictions resolved | 2 |
| Source documents updated | 2 (`test-plan.md`, `acceptance-criteria.md`) |

**Next step (EV-001 routing):** [04-tech-plan](.cursor/skills/04-tech-plan/SKILL.md) — 03-plan-tooling skipped for EV-001.

---

## EV-002 Delta Audit (2026-05-26)

### Scope

Features F23–F29: Admin UI overhaul, tag display, summary dashboard, health dashboard,
bulk operations, serving statistics, audit log & version history.

### Auto-approved (high confidence): 14 statements

All derived directly from user interview (RD-034–RD-052):

| Stmt ID | Feature | Statement | Source |
|---------|---------|-----------|--------|
| S-EV2.1 | F23 | Admin UI uses shadcn/ui (Tailwind + Radix) | RD-035 |
| S-EV2.2 | F23 | System-preference light/dark theme | RD-036 |
| S-EV2.3 | F24 | Tag chips inline below document title, color-coded by source | RD-037 |
| S-EV2.4 | F25 | Dashboard shows 8 stat types | RD-038 |
| S-EV2.5 | F26 | Health dashboard monitors 8 services, manual refresh | RD-039 |
| S-EV2.6 | F26 | Frontend-direct calls to /health | RD-040 |
| S-EV2.7 | F27 | Bulk ops: delete, tag, retag, metadata; checkboxes + shift+click | RD-041 |
| S-EV2.8 | F27 | No inline content editing; re-ingest required | RD-042 |
| S-EV2.9 | F28 | Document-level only serving stats | RD-043 |
| S-EV2.10 | F28 | Async fire-and-forget POST from chat-rag-backend | RD-044 |
| S-EV2.11 | F29 | 7 event types in audit log | RD-046 |
| S-EV2.12 | F29 | Version history: metadata + tags only | RD-047 |
| S-EV2.13 | F29 | Global audit log page + per-document history | RD-048 |
| S-EV2.14 | F29 | Configurable retention, default 365 days | RD-049 |

### Contradiction resolved

| ID | Issue | User verdict | Resolution |
|----|-------|-------------|------------|
| S-EV2.C1 | User requested "by what IP and where" but ADR-016 rejects IP storage (ADR-004 compliance) | **Approved ADR-016** | No IP stored; request_id only. Platform access logs provide IP outside Vecinita boundary. |

### Reviewed (medium / low)

| Stmt ID | Confidence | Verdict | Action |
|---------|------------|---------|--------|
| S-EV2.15 | Medium | approved | 9 new API endpoints on internal-write-api follow /internal/v1/ convention |
| S-EV2.16 | Medium | approved | Bulk delete hard-delete, max 100, audit record preserved |
| S-EV2.17 | Medium | approved | document_serving_stats table; async fire-and-forget; dashboard-only display |
| S-EV2.18 | Medium | approved | Health: manual refresh, frontend-direct, Postgres proxied via internal-write-api |
| S-EV2.19 | Medium | approved | CORS on all new EV-002 endpoints for admin frontend origin |
| S-EV2.20 | Medium | approved | 3 new tables in allow-list; privacy tests updated |
| S-EV2.21 | Low | approved | New VITE_VECINITA_*_HEALTH_URL env vars + timeout (5000ms default) |
| S-EV2.22 | Low | added | Acceptance criteria for F23-F29 (AC-E1 through AC-E11) |
| S-EV2.23 | Medium | modified | F23 and F24 each get a dedicated UJ (UJ-020, UJ-021) |

### Consistency check (EV-002)

| Check | Result | Action |
|-------|--------|--------|
| Feature ↔ Spec | **Pass** | F23–F29 mapped to spec §DO internal write API, §Data Flow |
| Feature ↔ Journey | **Pass** (after fix) | Added UJ-020 (F23), UJ-021 (F24) per user request |
| Journey ↔ Test | **Pass** (after fix) | Added TC-062, TC-063 (UJ-020), TC-064 (UJ-021) |
| Feature ↔ Test | **Pass** | TC-050–TC-064 cover F23–F29 |
| Feature ↔ Acceptance | **Pass** (after fix) | Added AC-E1 through AC-E11 |
| Spec ↔ Config | **Pass** | New env vars documented in config-spec |
| Cross-doc naming | **Pass** | Consistent: audit_log, document_versions, document_serving_stats |
| Scope boundaries | **Pass** | No privacy violations; ADR-016 approved |
| Template conformance | **Pass** | api+worker template; new endpoints on internal-write-api (DO) |

### EV-002 summary

| Metric | Count |
|--------|-------|
| New statements audited | 24 |
| Auto-approved (high) | 14 |
| User-approved (medium/low) | 9 |
| Modified | 1 (UJ-020/UJ-021 added) |
| Contradictions found | 1 |
| Contradictions resolved | 1 |
| Source documents updated | 3 (`acceptance-criteria.md`, `user-journeys.md`, `test-plan.md`) |

**Next step (EV-002 routing):** 04-tech-plan — 03-plan-tooling skipped for EV-002.

---

## EV-004 Delta Audit (2026-06-13)

### Scope

Feature F31: Admin + shared frontend bilingual UI (en/es); workspace packages
`frontend-i18n` and `frontend-ui`; ChatRAG migration to shared packages + full Tailwind.

### Auto-approved (high confidence): 15 statements

All derived directly from user interview (RD-053–RD-066, RD-067 partial):

| Stmt ID | Feature | Statement | Source |
|---------|---------|-----------|--------|
| S-EV4.1 | F31 | Admin full en/es UI + shared packages; migrate ChatRAG; no backend changes | RD-053 |
| S-EV4.2 | F31 | UI chrome only — corpus titles, tags, URLs, audit JSON, API errors unchanged | RD-054 |
| S-EV4.3 | F31 | Two packages: pure TS `frontend-i18n` + React `frontend-ui` | RD-055 |
| S-EV4.4 | F31 | ChatRAG full Tailwind layout migration in EV-004 | RD-056 |
| S-EV4.5 | F31 | Root npm workspaces for `apps/*` + `packages/frontend-*` | RD-057 |
| S-EV4.6 | F31 | Dot-prefixed message keys: `chat.*`, `admin.*`, `shared.*` | RD-058 |
| S-EV4.7 | F31 | Audit/dashboard timestamps follow UI locale via `Intl` | RD-059 |
| S-EV4.8 | F31 | Minimal shadcn re-exports from `frontend-ui` | RD-060 |
| S-EV4.9 | F31 | Language toggle in sidebar footer beside theme control | RD-061 |
| S-EV4.10 | F31 | High priority — ship before next deploy | RD-062 |
| S-EV4.11 | F31 | UJ-022 for admin language toggle | RD-063 |
| S-EV4.12 | F31 | Vitest mirror ChatRAG language-toggle tests | RD-064 |
| S-EV4.13 | F31 | No API contract changes — client-only i18n | RD-065 |
| S-EV4.14 | F31 | Deploy: build packages → redeploy both frontends; no API/Modal | RD-066 |
| S-EV4.15 | F31 | Shared `localStorage` key `vecinita.locale` across both frontends | RD-053, ADR-019 |

### Reviewed (medium / low)

| Stmt ID | Confidence | Verdict | Action |
|---------|------------|---------|--------|
| S-EV4.M1 | Medium | approved | ~120+ admin static strings scope retained |
| S-EV4.M2 | Medium | approved | Full ChatRAG Tailwind migration confirmed in scope |
| S-EV4.M3 | Medium | approved | Typed message keys + runtime dev fallback |
| S-EV4.C3 | Medium | approved | H4/H5 regression at deploy — added AC-F7, test-plan note |
| S-EV4.L1 | Low | approved | Non-en/es browser default → ES (match ChatRAG) |
| S-EV4.L2 | Low | **denied** | ThemeToggle **extracted** to `frontend-ui` — RD-067; ADR-019/020/spec updated |

### Contradictions resolved

| ID | Issue | User verdict | Resolution |
|----|-------|-------------|------------|
| S-EV4.C1 | Feature matrix missing F30, F31 | **Fix matrix** | Added F30/F31 rows to feature-list matrix |
| S-EV4.C2 | Journey index / E2E table missing UJ-020, UJ-021 | **Fix index** | Added UJ-020/UJ-021 to user-journeys index + test-plan E2E table |

### Consistency check (EV-004)

| Check | Result | Action |
|-------|--------|--------|
| Feature ↔ Spec | **Pass** | F31 maps to `frontend-i18n`, `frontend-ui`, both frontends |
| Feature ↔ Journey | **Pass** (after fix) | UJ-022 for F31; UJ-020/021 index restored |
| Journey ↔ Test | **Pass** (after fix) | TC-065–TC-069 + TC-062–064 for UJ-020/021 |
| Feature ↔ Test | **Pass** | TC-065–TC-071 cover F31 |
| Feature ↔ Acceptance | **Pass** | AC-F1–AC-F7 for F31 |
| Spec ↔ Config | **Pass** | Browser locale in config-spec §Browser locale |
| Test ↔ Connectivity | **Pass** (after fix) | AC-F7 + test-plan H4/H5 regression note |
| Cross-doc naming | **Pass** | `vecinita.locale`, package names consistent |
| Scope boundaries | **Pass** | No API/backend changes; R30 translation boundary |
| Template conformance | **Pass** | npm workspaces + DO static frontends |

### EV-004 summary

| Metric | Count |
|--------|-------|
| New statements audited | 21 |
| Auto-approved (high) | 15 |
| User-approved (medium/low) | 5 |
| Denied / modified | 1 (ThemeToggle → shared package) |
| Contradictions found | 2 |
| Contradictions resolved | 2 |
| Source documents updated | 10 |

**Next step (EV-004 routing):** [05-verify-tech](.cursor/skills/05-verify-tech/SKILL.md) complete — see `docs/sessions/S000-internal-docs-archive/audits.md#technical-plan-audit-report` §EV-004 delta (2026-06-13) for task-count reconciliation (TV-041–TV-052).

## Technical plan audit report

> **Stage**: 05-verify-tech  
> **Started**: 2026-05-19  
> **Completed**: 2026-05-19  
> **Status**: completed

## Document inventory

| # | Document | Path | Statements | Result |
|---|----------|------|------------|--------|
| 1 | Execution Plan | docs/sessions/S000-internal-docs-archive/execution-plan.md | 22 | Updated (8 tasks + deps + cost) |
| 2 | Deployment Integration | docs/deployment-integration.md | 6 | Updated (cost gate note) |
| 3 | Dependency Inventory | docs/dependency-inventory.md | 5 | Pass |
| 4 | Data Management Plan | docs/data-management-plan.md | 4 | Pass |
| 5 | ADRs (ADR-001–013) | docs/adr/ | 8 | ADR-001, ADR-002 amended |
| 6 | API Contract | docs/api-contract.md | 3 | Cross-ref pass |

**Product cross-check:** feature-list F1–F18, spec components, config-spec, acceptance-criteria, test-plan.

---

## Results summary

| Metric | Count |
|--------|-------|
| Documents audited | 6 |
| Total statements | 48 |
| Auto-approved (high) | 27 (56%) |
| Resolved via audit fixes | 12 |
| Deferred (documented) | 3 |
| Skipped (user) | 6 (batch interview skipped; defaults applied) |

---

## Auto-approved (high confidence) — 27

See `docs/decisions.md#technical-decisions-05-verify-tech` and audit Pass 1 table (TS-EP-01 … TS-ADR-04): Python 3.11, Pyright, pip-audit, no BFF v1, Qwen2.5-1.5B on T4, hybrid Modal+DO, multi-app DO, OpenAPI-first, zero PII schema, 384-dim FastEmbed, LlamaIndex 0.11.x, branch strategy, forbidden tables, etc. — all from **04-tech-plan** interview (TP-001–TP-009) and product audit ADRs.

---

## Consistency check

| Area | Checks | Issues found | Resolved |
|------|--------|--------------|----------|
| Product ↔ Technical | 6 | 9 | 8 |
| Internal Technical | 7 | 12 | 7 |
| **Total** | 115 atomic | 21 | 15 |

**Remaining (deferred):** AC-C4 load test (TV-D01); TDD ordering on scaffold tasks (TV-D02); explicit ingest config unit tests (TV-D03).

---

## Issues resolved (source updates)

| Stmt | Fix |
|------|-----|
| TS-C01, TS-C08 | T3.7 observability |
| TS-C02, TS-C10 | T2.8, T14.5 eval |
| TS-C03–C05 | T10.6, T7.5, T10.7 E2E |
| TS-C06–C07 | Data deps table corrected |
| TS-C11 | Cost section → ~$42–48, cap $50 |
| TS-C12 | test-plan → pyright |
| TS-C13 | T13.4 Modal DATABASE_URL CI check |
| TS-C14, TS-C21 | ADR-001 + workflow-state internal-write-api |
| TS-C15 | ADR-002 Modal `/jobs` row |
| TS-C16 | T1.1 lists internal-write-api |
| TS-C19 | T2.9 ingest fixture |
| TS-C20 | Task count **73** |

---

## Phase B gate (partial)

- [x] Execution plan audited
- [x] Consistency check complete (15/21 fixed; 3 deferred; 3 low-risk accepted)
- [ ] Technical tooling — **next: 06-tech-tooling**

---

## Artifacts

- `docs/sessions/S000-internal-docs-archive/audits.md#technical-plan-audit-report` (this file)
- `docs/decisions.md#technical-decisions-05-verify-tech`
- Updated: `docs/sessions/S000-internal-docs-archive/execution-plan.md`, `docs/test-plan.md`, `docs/adr/ADR-001-*`, `docs/adr/ADR-002-*`, `docs/deployment-integration.md`, `workflow-state.yaml`

---

## EV-001 delta audit (2026-05-24)

> **Stage**: 05-verify-tech (EV-001)  
> **Evolve cycle**: EV-001 (F19–F22)  
> **Prerequisite**: 04-tech-plan completed; 02-verify-plan product delta passed

### Document inventory

| # | Document | Statements reviewed | Result |
|---|----------|---------------------|--------|
| 1 | Execution plan (Phase 5) | 18 | Updated (11 tasks/deps/gates) |
| 2 | ADR-015 | 8 | Pass (auto-approved) |
| 3 | Dependency inventory | 2 | Updated (`packages/tagging`) |
| 4 | test-plan.md | 6 | Updated (connectivity §, TC-048/049) |
| 5 | spec.md | 1 | Updated (tagging component) |
| 6 | staging-secrets-matrix | 1 | Updated (browse VITE note) |
| 7 | feature-list F20 | 1 | Narrowed batch retag scope |

### Results summary

| Metric | Count |
|--------|-------|
| Documents audited | 7 |
| Total statements | 37 |
| Auto-approved (high) | 8 (TP-010–TP-017, ADR-015) |
| User-approved (medium/low) | 15 |
| Denied | 0 |
| Modified via verdict | 11 source-doc edits |
| Skipped | 0 |

### Consistency check (EV-001)

| Area | Checks | Issues found | Resolved |
|------|--------|--------------|----------|
| Product ↔ Technical | 12 | 6 | 6 |
| Internal Technical | 8 | 9 | 9 |
| Connectivity | 5 | 3 | 3 |
| **Total** | 25 | 15 | 15 |

### Auto-approved (high) — TP-010 through TP-017

Ingest tag-after-chunk-before-embed; async retag via `jobs.job_type=retag`; union SQL tag filter; same vLLM for inference; `/corpus` browse route; `evolve/EV-001-corpus-tags` branch; LLM cost within ≤ $50/mo cap.

### User-resolved issues

| Stmt | Resolution |
|------|------------|
| TS-EV001-01 | T18.6 → AC-T4 |
| TS-EV001-02/03 | T16.4 ingest-only; T18.3 admin PATCH; T18.1/2 depend T15.2 |
| TS-EV001-04 | T18.7 + TC-049 PATCH CORS |
| TS-EV001-05 | T19.5 H5; Phase 5 gate H4+H5 |
| TS-EV001-06 | test-plan connectivity tiers |
| TS-EV001-07 | TC-048 + UJ-010 cites |
| TS-EV001-09 | Per-document retag only |
| TS-EV001-10 | `packages/tagging` in spec + inventory |
| TS-EV001-08+ | AC-T6, config wiring, RD-030, T19.1, inventory date, UJ-002 typo |

### Phase B gate (EV-001 partial)

- [x] EV-001 execution plan audited
- [x] Consistency check complete (15/15 resolved)
- [x] Connectivity tasks include H4 + H5 + admin PATCH (not deploy-only)
- [ ] **06-tech-tooling** skipped for EV-001 per routing — **next: 07-build** (M15)

---

## EV-002 delta audit (2026-05-26)

> **Stage**: 05-verify-tech (EV-002)  
> **Evolve cycle**: EV-002 (F23–F29)  
> **Prerequisite**: 04-tech-plan completed; 02-verify-plan product delta passed

### Document inventory

| # | Document | Statements reviewed | Result |
|---|----------|---------------------|--------|
| 1 | Execution plan (Phases 6–8) | 13 | Updated (task count, Phase 6 gate) |
| 2 | ADR-017 | 12 | Pass (auto-approved — all from interview) |
| 3 | Dependency inventory | 2 | Pass (Node packages) |
| 4 | Config spec | 3 | Updated (removed VITE_* health vars, added aggregator vars) |
| 5 | Staging secrets matrix | 2 | Updated (VECINITA_HEALTH_DATA_MGMT_URL) |
| 6 | API contract | 4 | Updated (bulk response schemas, health/all endpoint) |
| 7 | Acceptance criteria | 1 | Updated (AC-E5 wording) |
| 8 | Spec.md | 1 | Updated (health/all in API surface) |

### Results summary

| Metric | Count |
|--------|-------|
| Documents audited | 8 |
| Total statements | 23 |
| Auto-approved (high) | 15 (TP-018–TP-029, phases, deps) |
| User-approved (medium/low) | 8 |
| Denied | 0 |
| Modified via verdict | 7 source-doc edits |
| Skipped | 0 |

### Consistency check (EV-002)

| Area | Checks | Issues found | Resolved |
|------|--------|--------------|----------|
| Product ↔ Technical | 9 | 3 | 3 |
| Internal Technical | 8 | 5 | 5 |
| **Total** | 17 | 8 | 8 |

### Auto-approved (high) — TP-018 through TP-029

Tailwind v3; health aggregator on internal-write-api (avoids Modal CORS); real-time SQL stats; React Router v7; fire-and-forget serving stats; explicit audit helpers; partial-success bulk; version snapshots on audit; shadcn/ui npx init; background audit retention (365d); Vitest + Testing Library; sequential deploy order.

### User-resolved issues

| Stmt | Resolution |
|------|------------|
| TS-EV002-C01 | Remove `VITE_*` health URLs from config-spec; frontend uses aggregator via `VITE_VECINITA_CORPUS_API_URL` |
| TS-EV002-C02 | Fix AC-E5: "atomically" → "independently with partial-success" (TP-024 alignment) |
| TS-EV002-C03 | Fix api-contract: bulk endpoint responses use `{successes, failures}` per TP-024 |
| TS-EV002-C04 | Add `GET /internal/v1/health/all` to api-contract (was missing) |
| TS-EV002-C05 | Add `VECINITA_HEALTH_DATA_MGMT_URL` to staging-secrets-matrix; 4 total health URLs + derived |
| TS-EV002-C06 | Fix task count: 73 EV-002 tasks, 184 total (was erroneously 52/163) |
| TS-EV002-C07 | Add M24 (F25/F26) coverage to Phase 6 gate criteria |
| TS-EV002-C08 | Accept frontend code-before-test pattern (consistent with M7/M11, TV-D02) |

### Phase B gate (EV-002 partial)

- [x] EV-002 execution plan audited
- [x] Consistency check complete (8/8 resolved)
- [x] Config spec aligned with TP-019 aggregator decision
- [x] Bulk response schemas aligned with TP-024 partial success
- [x] Health aggregator endpoint documented in api-contract + spec
- [ ] **06-tech-tooling** skipped for EV-002 per routing — **next: 07-build** (M20)

---

## EV-004 delta audit (2026-06-13)

> **Stage**: 05-verify-tech (EV-004)  
> **Evolve cycle**: EV-004 (F31)  
> **Prerequisite**: 04-tech-plan completed; 02-verify-plan product delta passed

### Document inventory

| # | Document | Statements reviewed | Result |
|---|----------|---------------------|--------|
| 1 | Execution plan (Phase 9) | 14 | Updated (task count, deps, T36.9/T36.10, consolidated sync) |
| 2 | ADR-021 | 10 | Pass (auto-approved — TP-030–TP-039) |
| 3 | ADR-019 / ADR-020 | 2 | Updated (Tailwind layout wording) |
| 4 | deployment-integration.md | 2 | Updated (source imports wording) |
| 5 | test-plan.md | 4 | Updated (TC-070/071, UJ-022 index) |
| 6 | acceptance-criteria.md | 2 | Updated (AC-F4/F5 TC refs) |
| 7 | staging-secrets-matrix.md | 1 | Updated (EV-004 footnote) |
| 8 | decisions.md (technical section) | 12 | Updated (TV-041–TV-052) |
| 9 | audits.md (product section) | 1 | Cross-ref to this audit |

### Results summary

| Metric | Count |
|--------|-------|
| Documents audited | 9 |
| Total statements | 34 |
| Auto-approved (high) | 10 (TP-030–TP-039) |
| User-approved (medium/low) | 12 |
| Denied | 0 |
| Modified via verdict | 11 source-doc edits |
| Skipped | 0 |

### Consistency check (EV-004)

| Area | Checks | Issues found | Resolved |
|------|--------|--------------|----------|
| Product ↔ Technical | 10 | 4 | 4 |
| Internal Technical | 8 | 8 | 8 |
| Connectivity | 3 | 0 | 0 |
| **Total** | 21 | 12 | 12 |

### Auto-approved (high) — TP-030 through TP-039

Continue PR #60 branch; source imports via npm workspaces; strict typed `t()`; full ChatRAG Tailwind migration; ES locale fallback; root npm CI workspaces; full ADR-020 component surface; all admin static strings; simultaneous frontend deploy; extend H4/H5 smoke.

### User-resolved issues

| Stmt | Resolution |
|------|------------|
| TS-EV004-C01 | 39 Phase 9 tasks (37 + T36.9/T36.10); 222 total (TV-041) |
| TS-EV004-C02 | Completed count **183/222** (TV-042) |
| TS-EV004-C03 | Consolidated Task Tracking T27.x–T31.x → completed (TV-045) |
| TS-EV004-C04 | TC-070 + TC-071 + T36.9/T36.10 for AC-F4/F5 (TV-043) |
| TS-EV004-C05 | Accept T33.3 post-code test pattern (TV-046) |
| TS-EV004-C06 | ADR-019/020 — Tailwind layout, not App.css (TV-044) |
| TS-EV004-C07 | deployment-integration — workspace source imports (TV-047) |
| TS-EV004-C08 | T32.1 Vitest only (TV-048) |
| TS-EV004-C09 | T37.1 deps on T35.6 + T36.8 (TV-049) |
| TS-EV004-C10 | UJ-022 lists TC-065–TC-069 (TV-050) |
| TS-EV004-C11 | staging-secrets-matrix EV-004 footnote (TV-051) |
| TS-EV004-C12 | product-audit cross-ref (TV-052) |

### Phase B gate (EV-004 partial)

- [x] EV-004 execution plan audited
- [x] Consistency check complete (12/12 resolved)
- [x] Connectivity tasks include H4 + H5 for both frontends (M38)
- [x] AC-F4/AC-F5 have dedicated test coverage (TC-070/071)
- [ ] **06-tech-tooling** skipped for EV-004 per routing — **next: 07-build** (M32)
