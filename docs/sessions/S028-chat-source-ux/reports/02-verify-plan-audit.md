# 02-verify-plan audit — EV-026 / F72–F74

> **Session:** S028 · **Cycle:** EV-026 · **Date:** 2026-08-06  
> **Mode:** evolve delta · **Status:** completed (S028-D20 — C1/M1/M2/M3/L1 approved)  
> **Citations:** [Corpus: feature-list.md §F72–F74] [Spec: docs/api-contract.md §POST /ask sources] [Corpus: decisions.md §RD-309–321]

## Inventory (delta)

| # | Document | Sections | Status |
|---|----------|----------|--------|
| 1 | feature-list.md | Summary F72–F74; detail §F72–F74; `top_k` row | audited + M2 fix |
| 2 | spec.md | ChatRAG packing; FE citation; schema; PATCH; changelog | audited + S023 note |
| 3 | user-journeys.md | UJ-077–079; UJ-063 | audited + C1 fix |
| 4 | test-plan.md | Journey map + TC-242–251 | audited (M3 hold) |
| 5 | acceptance-criteria.md | AC-SU1–SU11; AC-ME10 note | audited + L1 fix |
| 6 | api-contract.md | sources title/length; bulk; PATCH `/{id}` | audited |
| 7 | config-spec.md | `TOP_K` / `MIN_RETRIEVAL_SCORE` F73 notes | audited |
| 8 | runbooks/corpus-operator-guide.md | Display titles | audited |
| 9 | decisions.md RD-309–321 (+ RD-231 supersession) | reference | audited + C1 |

## Consistency

| Check | Result |
|-------|--------|
| Feature ↔ Spec | **Pass** |
| Feature ↔ Journey | **Pass** |
| Journey ↔ Test | **Pass** |
| Feature ↔ Test | **Pass** |
| Spec ↔ Config | **Pass** |
| Test ↔ Acceptance | **Pass** |
| RD ↔ Spec | **Pass** |
| Scope boundaries | **Pass** |
| Connectivity | **Pass** — Vitest F72/F74; API e2e F73/F74; Playwright optional |
| Naming | **Pass** |
| Stale cross-doc | **Pass after C1** — UJ-063 + RD-231 aligned with F73 |

## Verdicts

### Auto-approved (high confidence) — 17

H1–H17 from RD-309–321 / S028 locked batches (see prior mid-stage draft).

### Medium / low — user-approved (S028-D20: 1a/2a/3a/4a)

| ID | Statement | Verdict | Action |
|----|-----------|---------|--------|
| C1 | UJ-063 “equals retrieve top_k” vs F73 0…top_k | **Approved (fix)** | UJ-063 amended; RD-231 superseded by RD-311 |
| M1 | F72 Source cited RD-320 | **Approved (fix)** | → RD-310 / RD-317 |
| M2 | `top_k` summary row missing F73 upper bound | **Approved (fix)** | feature-list row updated |
| M3 | TC-195 strong-hit fixture valid under F73 | **Approved** | no change; F73 = TC-245–247 |
| L1 | AC-ME10 “F72 as separate Fn” naming collision | **Approved (fix)** | footnote — F72 = #222 citation UX |

## Source updates

| File | Change |
|------|--------|
| `docs/user-journeys.md` | UJ-063 steps/acceptance — ≤ top_k after filter; UJ-078 cross-ref |
| `docs/feature-list.md` | `top_k` row F73 upper bound; F72 Source RD cites |
| `docs/acceptance-criteria.md` | AC-ME10 F72 footnote |
| `docs/decisions.md` | Product decisions EV026-*; RD-231 supersession note |
| `docs/spec.md` | S023 changelog — length filter refined by F73 |

## Gate A→B

**Passed** (S028-D20). Phase A complete → next **04-tech-plan** (03 skipped per RD-319).
