# 01-requirements — S022 / EV-019 (Ingest resilience)

**Date:** 2026-08-02  
**Mode:** delta  
**Features:** F47 (#163), F48 (#166), F49 (#160)

## Phase 0C answers

| Q | Answer | Decision |
|---|--------|----------|
| Q0 | 1 | Approve locked L1–L11 |
| Q1 | 1 | F47: refresh metadata; skip chunks+embed |
| Q2 | 1 | F48: fail URL after retry exhaust |
| Q3 | 2 | F49: **`chunk_overlap` default 32** |
| Q4 | 2 | F49: **HF tokenizer** this cycle (ADR-044) |
| Q5 | 1 | Extend ingest UJ + TC (UJ-062; TC-187–192) |

## Document manifest checklist

| Document | Status |
|----------|--------|
| `docs/feature-list.md` | Updated F47–F49 details + F1 knobs |
| `docs/spec.md` | Ingest algorithm + data-flow steps |
| `docs/config-spec.md` | Overlap, tokenizer, embed retry knobs |
| `docs/api-contract.md` | Ingest JobOptions `force` / overlap |
| `docs/user-journeys.md` | UJ-002 extend + **UJ-062** |
| `docs/test-plan.md` | TC-187–192 |
| `docs/acceptance-criteria.md` | AC-IR1–IR7 |
| `docs/dependency-inventory.md` | transformers on ingest path |
| `docs/adr/ADR-044-*.md` | Accepted |
| `docs/decisions.md` | RD-219–RD-228 |
| `docs/decisions/evolve-decisions.md` | S022-D14–D19 |

## Out of scope (held)

#159 multilingual embeds · #165 packing · CE flag flip · ADR-023 tag fail-open change

## Next

`@.cursor/skills/02-verify-plan/SKILL.md` — delta consistency + statement audit
