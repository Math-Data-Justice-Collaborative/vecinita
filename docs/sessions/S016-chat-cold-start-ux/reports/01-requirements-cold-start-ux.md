# 01-requirements — EV-014 / F40 cold-start wait UX

**Session:** S016-chat-cold-start-ux  
**Cycle:** EV-014  
**Date:** 2026-07-29  
**Issue:** [#87](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/87)

## Summary

Delta requirements for ChatRAG cold-start / long-wait UX: rotating bilingual fun facts, soft
donate CTA, friendly consent + cookie opt-out before remembering seen facts, FE `/warm` only.

## Locked (seed + Q20–Q23)

| ID | Decision |
|----|----------|
| Q20 | Approve all Phase 0 locked scope |
| Q21 | Curate ~10 facts from WRWC/Providence scrape |
| Q22 | Vitest + Playwright T0-ui |
| Q23 | Accept / No thanks; rotate either way; memory only after Accept |

## RD / ADR

- RD-183–RD-187 in `docs/decisions.md`
- ADR-039 ChatRAG fun-fact consent cookie

## Spec deltas

| Doc | Change |
|-----|--------|
| feature-list | F40 |
| user-journeys | UJ-052 |
| test-plan | TC-156–TC-160 |
| acceptance-criteria | AC-CS1–AC-CS8 |
| spec | ChatRAG Frontend F40 |
| config-spec | `VITE_WRWC_DONATE_URL` + storage keys |
| evolve-decisions | Cycle EV-014 |

## Next

02-verify-plan (Gate A→B).
