# 02-verify-plan audit — EV-015 / #167 / F41

**Session:** S017-corpus-reembed-migration  
**Date:** 2026-07-30  
**Mode:** delta consistency (Standard+build)  
**Status:** **complete** — Gate A→B PASS

## Documents checked

| Doc | Delta present |
|-----|---------------|
| feature-list F41 | yes (+ promote UI, backfill) |
| spec (Jobs + Internal write) | yes |
| user-journeys UJ-053, UJ-054 | yes |
| test-plan TC-161–169 | yes (TC-169 promote UI) |
| acceptance-criteria AC-RB1–10 | yes |
| api-contract EV-015 + JobOptions | yes |
| config-spec rebuild/shadow knobs | yes |
| ADR-040 | yes |
| decisions RD-188–196 + 02 verdicts | yes |
| evolve-decisions EV-015 | yes |
| runbook outline (session) | yes |
| deployment-integration.md | deferred to 04 (M5) |
| data-flow.md | deferred to 04 (M5) |

## Results

| Category | Count |
|----------|-------|
| Auto-approved (high) | 14 |
| User-approved / modified (medium) | 5 (M1–M4, M6) |
| Deferred (low) | 1 (M5 → 04) |
| Denied | 0 |
| Skipped | 0 |

## High confidence (auto-approve)

| ID | Statement | Evidence |
|----|-----------|----------|
| H1 | **F41** = document store + rebuild (not split F42) | RD-188; S017-D17 |
| H2 | `job_type=rebuild` + `mode ∈ {reembed, rechunk, rescrape}` | RD-189; S017-D10 |
| H3 | Ops prefer **store-backed** reembed/rechunk; no live scrape unless rescrape | RD-190 |
| H4 | Dry-run = **shadow dual-write** + promote | RD-191 |
| H5 | Scope = whole corpus default + optional `document_ids` | RD-192 |
| H6 | Version stamps; dim dual-write deferred to #159 | RD-193 |
| H7 | Retag remains a **separate** job | RD-194 |
| H8 | Progress = Jobs SSE + `/jobs/:id` only | RD-195 |
| H9 | Postgres `body_text` + `document_revisions`; ADR-007 writes | RD-196 |
| H10 | Admin Jobs UI enqueue + Modal + `force` | S017-D5 |
| H11 | Staging + F36; prod live rebuild out of scope | S017-D6 |
| H12 | UJ-053 ↔ TC-161–163, TC-166, TC-167 | post-M1 |
| H13 | UJ-054 ↔ TC-164–165, TC-168–169 | post-M3 |
| H14 | ADR-040 accepted; OpenAPI shape deferred to 04 | api-contract |

## Medium / low — final verdicts

| ID | Verdict | Action |
|----|---------|--------|
| M1 | Approve fix | TC-166 under UJ-053 |
| M2 | Lock | F36 against shadow **before** promote |
| M3 | Modify | Admin UI promote + full build this session; TC-169 |
| M4 | Approve | One-time backfill in F41 |
| M5 | Defer | deployment-integration / data-flow → **04-tech-plan** |
| M6 | Approve | Promote auth = **`admin`** (enqueue parity) |

## Consistency checklist (16-evolve)

- [x] F41 in feature-list + spec components
- [x] UJ-053/054 + Playwright TC-167 / TC-169
- [x] Journey ↔ test IDs consistent
- [x] Feature ↔ AC-RB1–10 ↔ TC coverage
- [x] Config names match
- [x] api-contract ↔ deployment-integration deferred to 04 (M5)
- [x] ADR-040 referenced
- [x] Prod live rebuild excluded
- [x] Connectivity: Admin UI has Playwright (not Vitest-only)

## Gate A→B

**Passed** 2026-07-30 (M1–M6 resolved).

**Next:** Phase A checkpoint AskQuestion → **04-tech-plan** (03 skipped). User wants full build this session.
