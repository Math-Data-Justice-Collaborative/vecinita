# Product plan audit report

> **Stage**: 02-verify-plan  
> **Started**: 2026-05-19  
> **Status**: completed (2026-05-19)  
> **Partial re-run**: 2026-05-19 (drift scan; no new user interview items)

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
