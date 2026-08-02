# 01-requirements seed — S022 / EV-019 (Ingest resilience)

Generated from 00-context + 16-evolve Phase 0 (2026-08-02). Locked decisions are **confirm-only**.

## How 01 should use this

1. Load this seed (not a greenfield interview).
2. Confirm locked decisions in one batch.
3. Apply document manifest deltas only.
4. Interview **only** open questions below.
5. Next after 01: `02-verify-plan`.

## Locked decisions

| Seed ID | Session ID | Decision |
|---------|------------|----------|
| L1 | S022-D1 | New session S022; pipeline was idle after S021 |
| L2 | S022-D2 | Scope = #163 + #166 + #160 (Bundle A) |
| L3 | S022-D3 | Routing **Standard**; skip 03/05/06/15 |
| L4 | S022-D4 | 00 scoped — no full regenerate |
| L5 | S022-D5 | **Investigate → ship** in EV-019 |
| L6 | S022-D6 | **Include #160** (F49) this cycle |
| L7 | S022-D8 | Fn: **F47** content_hash skip, **F48** embed sub-batch/retry, **F49** chunk overlap |
| L8 | S022-D9 | Order: **F47 + F48** first, then **F49** |
| L9 | S022-D10 | Deploy **Path A** default after verify |
| L10 | S022-D11 | Shared write/embed path only — no ChatRAG redesign |
| L11 | S022-D12 | Tagging stays ADR-023 fail-open; embeds get explicit retry policy (not silent fail-open) |

## Document manifest (delta)

| Document | Action |
|----------|--------|
| `docs/feature-list.md` | **Done Phase 0** — F47–F49 rows + details |
| `docs/spec.md` | Ingest skip / embed resilience / chunk overlap behavior |
| `docs/config-spec.md` | `force` / overlap / batch size knobs as decided in 01 |
| `docs/api-contract.md` | Job options + any write/embed response fields |
| `docs/test-plan.md` / `acceptance-criteria.md` | AC/TC per Fn + e2e |
| `docs/user-journeys.md` | Admin re-ingest no-op + flaky embed recovery (+ overlap if user-visible) |
| `docs/decisions/evolve-decisions.md` | §Cycle EV-019 |
| `docs/dependency-inventory.md` | Only if tokenizer package added for F49 |

**Excluded:** regenerate greenfield suite; Bundle B (#165/#158); CE/#83; #159 multilingual embeds.

## Pre-filled interview answers (confirm/modify)

| Topic | Locked / proposed |
|-------|-------------------|
| Personas | Admin / ops re-running ingest; system reliability |
| Success F47 | Unchanged hash → no re-embed; measurable skip in job result/logs; `force=true` bypass |
| Success F48 | Transient embed failures recovered via sub-batch+retry; dim mismatch still hard-fail |
| Success F49 | Overlap configurable; sizing documented; cost/re-ingest impact explicit |
| Apps | data-management-backend, internal-write-api, packages/ingest, embedding-client, Modal embed; optional admin FE |
| Breaking | Prefer compatible job options; default skip-on + force; overlap default may stay 0 until opted in |

## Open questions — resolved (01 Phase 0C — 2026-08-02)

| ID | Resolution |
|----|------------|
| Q0 | Approve locked L1–L11 (S022-D14) |
| Q1 | Refresh metadata; skip chunks+embed (RD-221) |
| Q2 | Fail URL after retry exhaust (RD-222) |
| Q3 | **Default overlap 32** (RD-223; overrides seed rec. 0) |
| Q4 | **HF tokenizer** for embed pin (RD-224 / ADR-044; overrides seed rec. word≈token) |
| Q5 | Extend UJ-002 + **UJ-062**; TC-187–192; AC-IR1–7 (RD-225) |

## Explicitly out of interview scope

- ChatRAG packing / CE / soft language
- Multilingual embedding model swap
- Changing ADR-023 tag fail-open to fail-closed

## Next after 01

`02-verify-plan` (delta consistency + statement audit on changed sections).
