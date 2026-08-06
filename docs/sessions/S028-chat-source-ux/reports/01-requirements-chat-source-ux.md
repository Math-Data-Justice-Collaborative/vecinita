# 01-requirements — Chat source UX (EV-026 / F72–F74)

**Session:** S028-chat-source-ux  
**Date:** 2026-08-06  
**Mode:** delta  
**Seed:** [checkpoints/01-requirements-seed.md](../checkpoints/01-requirements-seed.md)

## Phase 0C outcomes

| Batch | Choice |
|-------|--------|
| Locked S1–S11 | **1a** approve all |
| OQ1–OQ4 API/fallback/audit | **2a** PATCH + COALESCE + clear + `document.edited` |
| OQ5–OQ6 validator / CE off | **3a** http(s) only; `min_retrieval_score` alone when CE off |
| OQ7–OQ8 ingest / Playwright + write | **4a** optional ingest title (04); Vitest + API e2e; Playwright optional |

## RD allocated

RD-309–RD-321 in `docs/decisions.md` §EV-026.

## Docs updated (delta)

| Doc | Change |
|-----|--------|
| `feature-list.md` | F72–F74 Planned |
| `user-journeys.md` | UJ-077–079 |
| `test-plan.md` | TC-242–251 + journey map |
| `acceptance-criteria.md` | AC-SU1–SU11 |
| `api-contract.md` | sources semantics; PATCH document; bulk `display_title` |
| `config-spec.md` | `top_k` max; min_score F73 note |
| `spec.md` | packing coalesce; schema; endpoints |
| `runbooks/corpus-operator-guide.md` | Display titles section |
| `decisions.md` | RD-309–321 |
| `decisions/evolve-decisions.md` | EV-026 scope (prior) |

## Next

**02-verify-plan** (delta consistency on changed sections).

[Corpus: feature-list.md §F72–F74] [Spec: docs/api-contract.md §POST /ask sources]
