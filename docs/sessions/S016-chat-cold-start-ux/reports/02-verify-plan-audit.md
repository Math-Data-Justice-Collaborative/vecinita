# 02-verify-plan audit — EV-014 / #87 / F40

**Session:** S016-chat-cold-start-ux  
**Date:** 2026-07-29  
**Mode:** delta consistency (Lean+build)

## Documents checked

| Doc | Delta present |
|-----|---------------|
| feature-list F40 | yes |
| spec ChatRAG Frontend | yes |
| user-journeys UJ-052 | yes |
| test-plan TC-156–160 | yes |
| acceptance-criteria AC-CS1–CS8 | yes |
| config-spec VITE_WRWC + prefs | yes |
| ADR-039 | yes |
| decisions RD-183–187 | yes |
| evolve-decisions EV-014 | yes |

## High confidence (auto-approve)

| ID | Statement | Evidence |
|----|-----------|----------|
| H1 | New Fn **F40** (not extend F11) | Scope gate; RD-183 |
| H2 | Triggers: cold-start retry **or** >8s no first token | S016-D6/D7; RD-186 |
| H3 | Rotate ~4–5s; ~10 static EN/ES i18n facts; no API/CMS | Q4/Q5/Q21; RD-186 |
| H4 | Soft donate CTA → wrwc.org/donate (optional VITE_) | Q11; config-spec |
| H5 | FE `/warm` only — no Modal/backend | Q10→2; RD-184 |
| H6 | Consent Accept/No thanks; memory only after Accept | Q23; ADR-039 |
| H7 | localStorage seen ids + HTTP cookie opt-out; no PII; not API auth | Q12/Q13; RD-185 |
| H8 | Vitest TC-156–159 + Playwright TC-160; no new API e2e | Q22; RD-187 |
| H9 | No CORS / API contract change | Q16; UJ-052 |
| H10 | Lean+build skips 03–06, 09, 11–12 | Session D2 |

## Medium — user verdicts (2026-07-29)

| ID | Issue | Verdict |
|----|-------|---------|
| M1 | Cookie **Max-Age** | **A — Lock 1 year** (`31536000` s) |
| M2 | `deployment-integration.md` for optional `VITE_WRWC_DONATE_URL` | **A — Skip** — default constant sufficient; no CORS |
| M3 | Exact EN/ES fact strings | **A — Defer to 07-build** from Phase 0 scrape pool (~10) |

## Consistency checklist (16-evolve)

- [x] F40 in feature-list + spec component  
- [x] UJ-052 ↔ TC-156–160 ↔ AC-CS1–CS8  
- [x] Privacy: ADR-039 distinct from admin RD-181  
- [x] Connectivity: no CORS/API change; H4–H5 N/A for this delta  
- [x] Playwright required for cross-component wait/consent (not Vitest-only)  
- [x] Lean skips 04 — implementation notes fold into 07-build  

## Advisory (non-blocking)

- Historical EV-011 text “no F40” refers to F39 follow-on — superseded by EV-014 F40 allocation (feature-list note already clarifies).

## Gate A→B

**Passed** 2026-07-29 (M1–M3 all A).

Next stage: **07-build** (Lean — no 04-tech-plan).
