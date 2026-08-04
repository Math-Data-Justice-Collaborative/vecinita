# 01-requirements seed — S026 / EV-024

**From:** 00-context Phase 4.5  
**For:** 01-requirements Phase 0C  
**Session:** S026-frontend-ux-polish  
**Cycle:** EV-024  
**Epic:** [#193](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/193)

## Locked decisions (confirm-only)

| ID | Lock |
|----|------|
| S026-D1 | `feature` session → 16-evolve |
| S026-D2 | One evolve branch; **one PR per issue** (6 PRs) |
| S026-D3 | #87: tips + VECINA marketing on wait surface; **no mini surveys** |
| S026-D4 | Include #186 + #170 |
| S026-D5 | #93: backend heuristic energy (TDP × util × duration → Wh/CO₂e) + **UI estimate advisory**; cite Modal power-as-proxy conceptually |
| S026-D6 | #186: backend submit/store/forward (privacy review in 01) |
| S026-D7 | #170: read-time enrich only; no PII on `audit_log` |
| S026-D8 | Tooltip primitive in `packages/frontend-ui` |
| S026-D9 | Standard routing |
| S026-D10 | Session open approved |

## Open for 01 interview

1. ~~Fn allocation~~ — **locked S026-D11** (F64–F69)
2. #93: GPU class pin + utilization assumption + grid intensity source
3. #186: storage target (ChatRAG DB vs forward-only email/webhook) + retention
4. Mini-survey cancellation already locked — do not re-open unless user asks
5. Exact MVP control lists for #104 / #106
6. Whether #87 content extends F40 fact catalog vs new module

## Issue → Fn (approved)

| Issue | Fn | Title |
|-------|----|-------|
| #87 | F64 | Cold-start wait: query tips + VECINA marketing |
| #93 | F65 | Ask energy estimate + use guide + advisory |
| #104 | F66 | Action icon micro-interactions |
| #106 | F67 | Bilingual tooltips / contextual hints |
| #186 | F68 | ChatRAG feedback page + backend |
| #170 | F69 | Admin audit actor username (read-time) |

## Standing docs to delta

`feature-list.md`, `user-journeys.md`, `test-plan.md`, `acceptance-criteria.md`,
`api-contract.md` (#93/#186/#170), privacy/ADR as needed (#186), `packages/frontend-i18n`.
