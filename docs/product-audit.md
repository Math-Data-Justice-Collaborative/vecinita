# Product plan audit report

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
| 11 | Roadmap | docs/roadmap.md | 2 | 2 | Pass 1 done |
| 12 | Glossary | docs/glossary.md | 1 | 2 | Pass 1 done |
| 13 | Risk Register | docs/risk-register.md | 2 | 3 | Pass 1 done |

Skipped (reference input): `requirements-decisions.md`, `context-brief.md`.

---

## Pass 1 — Auto-approved (high confidence)

**Count: 28** — derived directly from `requirements-decisions.md` and interview ADRs.

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

See [product-decisions.md](product-decisions.md). Contradictions C1–C4 resolved 2026-05-19.

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

**Source documents updated:** 11 files — initial 8 + partial re-run (`feature-list.md`, `deployment-integration.md`, `adr/ADR-001-five-app-architecture.md`, `requirements-decisions.md`).

**Next step:** [03-plan-tooling](.cursor/skills/03-plan-tooling/SKILL.md) — rewrite stale RFantibody `.cursor/rules/` (ISS-001).

---

## EV-001 delta audit (2026-05-24)

**Scope:** F19–F22 product docs updated in 01-requirements (ADR-014). Full consistency pass across 13 spec documents; focus on new journeys UJ-009–UJ-012 and tag/browse connectivity.

### Auto-approved (high confidence) — 14 statements

Derived from `requirements-decisions.md` RD-024–RD-033 and ADR-014:

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

## EV-004 delta (2026-06-13) — F31 per-component coverage gate

**Partial re-run:** EV-004 F31 — 11 statements, 3 contradictions resolved, 1 source doc updated.

### Document inventory (delta)

| # | Document | Statements | Status |
|---|----------|------------|--------|
| 1 | Feature List | 3 | Pass |
| 2 | Test Plan | 3 | Pass |
| 3 | Acceptance Criteria | 3 | Pass |
| 4 | ADR-019 | 2 | Pass (reference) |

Skipped (already audited in prior passes): spec, user-journeys, config-spec, deployment-integration.

### Pass 1 — Auto-approved (high confidence)

**Count: 8** — derived directly from RD-053–RD-060 (EV-004 interview).

| Stmt ID | Statement (summary) | Source |
|---------|---------------------|--------|
| S-EV4.1 | ≥95% line + ≥95% branch per component | RD-053 |
| S-EV4.2 | Twelve gates: `packages/<name>` + `apps/<name>` | RD-054 |
| S-EV4.3 | Unit tests only (`tests/unit` + Vitest) | RD-055 |
| S-EV4.4 | Blocking CI on any component below threshold | RD-056 |
| S-EV4.5 | Exclusions: `__init__.py`, alembic, test paths | RD-057 |
| S-EV4.6 | Modal worker code in `apps/data-management-backend` gate | RD-058 |
| S-EV4.7 | Single milestone — all twelve before merge; no grandfathering | RD-059 |
| S-EV4.8 | Frontends same 95% line + branch as backends | RD-060 |

### Pass 2 — User review (medium/low)

| Stmt ID | Confidence | Verdict | Action |
|---------|------------|---------|--------|
| S-EV4.9 | Medium | approved | Baseline 61.0% lines / ~42.9% branches (2026-06-13) |
| S-EV4.10 | Medium | approved | Gate via `make test-unit-coverage` + summary script (exit non-zero pending) |
| S-EV4.11 | Medium | approved | Out of scope: integration/e2e, scripts/, infra/, OpenAPI clients |
| S-EV4.12 | Low | approved | Waive UJ requirement for F31 — AC-Q1–Q3 suffice (cross-cutting CI) |
| S-EV4.13 | Low | approved | Waive dedicated TC-xxx — metrics table + CI step + AC-Q sufficient |
| S-EV4.14 | Low | modified | Updated `execution-plan.md` Phase 3 gate: 80% → 95% per-component (ADR-019) |

### Consistency check (EV-004)

| Check | Result | Action |
|-------|--------|--------|
| Feature ↔ Spec | **Pass** | F31 in feature-list; ADR-019 canonical |
| Feature ↔ Journey | **Pass (waived)** | No UJ for F31 — user approved waiver (cross-cutting quality) |
| Journey ↔ Test | **N/A** | No journey for F31 |
| Feature ↔ Test | **Pass (waived)** | AC-Q + metrics + CI step 5; no TC-xxx required |
| Feature ↔ Acceptance | **Pass** | AC-Q1–Q3 cover F31 |
| Spec ↔ Config | **Pass** | Exclusions reference pyproject/vitest configs |
| Cross-doc naming | **Pass** | Twelve components consistent across feature-list, test-plan, ADR-019 |
| Scope boundaries | **Pass** | Supersedes ≥80% unit target; retrieval ≥80% eval benchmark unchanged |
| execution-plan drift | **Fixed** | Phase 3 gate updated to 95% per-component |

### EV-004 summary

| Metric | Count |
|--------|-------|
| New statements audited | 11 |
| Auto-approved (high) | 8 |
| User-approved (medium/low) | 5 |
| Modified | 1 |
| Contradictions found | 3 |
| Contradictions resolved | 3 |
| Source documents updated | 1 (`execution-plan.md`) |

**Next step (EV-004 routing):** 04-tech-plan — gate script, CI wiring, Vitest thresholds, test backlog per component.
