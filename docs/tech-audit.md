# Technical plan audit report

> **Stage**: 05-verify-tech  
> **Started**: 2026-05-19  
> **Completed**: 2026-05-19  
> **Status**: completed

## Document inventory

| # | Document | Path | Statements | Result |
|---|----------|------|------------|--------|
| 1 | Execution Plan | docs/execution-plan.md | 22 | Updated (8 tasks + deps + cost) |
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

See `docs/tech-decisions.md` and audit Pass 1 table (TS-EP-01 … TS-ADR-04): Python 3.11, Pyright, pip-audit, no BFF v1, Qwen2.5-1.5B on T4, hybrid Modal+DO, multi-app DO, OpenAPI-first, zero PII schema, 384-dim FastEmbed, LlamaIndex 0.11.x, branch strategy, forbidden tables, etc. — all from **04-tech-plan** interview (TP-001–TP-009) and product audit ADRs.

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

- `docs/tech-audit.md` (this file)
- `docs/tech-decisions.md`
- Updated: `docs/execution-plan.md`, `docs/test-plan.md`, `docs/adr/ADR-001-*`, `docs/adr/ADR-002-*`, `docs/deployment-integration.md`, `workflow-state.yaml`

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
