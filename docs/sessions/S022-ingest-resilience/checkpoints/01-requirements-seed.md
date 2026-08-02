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

## Open questions for 01 (interview)

| ID | Question | Recommendation |
|----|----------|----------------|
| Q1 | F47 skip: still update document metadata (tags/lang/scraped_at) when hash unchanged? | **Yes** — skip chunks+embed only; refresh metadata unless `force` |
| Q2 | F48 on exhausted retries: fail whole URL job vs partial chunk success? | **Fail URL job** after retries (avoid silent corpus holes); job-level retry already exists |
| Q3 | F49 default `chunk_overlap`: ship default **0** (opt-in) or non-zero? | **Default 0**; document recommended 32–64 for new corpora / rebuild |
| Q4 | F49 tokenizer: keep word-count estimate or add HF tokenizer? | **Keep word≈token** + document; tokenizer align only if eval proves need |
| Q5 | Journeys: new UJ vs extend existing ingest UJ? | **Extend** ingest re-run journey + add TC for skip + embed retry |

## Explicitly out of interview scope

- ChatRAG packing / CE / soft language
- Multilingual embedding model swap
- Changing ADR-023 tag fail-open to fail-closed

## Next after 01

`02-verify-plan` (delta consistency + statement audit on changed sections).
