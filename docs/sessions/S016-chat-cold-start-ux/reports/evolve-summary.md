# Evolve summary — EV-014 / S016 ChatRAG cold-start UX (#87)

**Cycle:** EV-014  
**Session:** S016-chat-cold-start-ux  
**Issue:** [#87](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/87)  
**PR:** [#157](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/157) — **merged** 2026-07-30  
**Merge SHA:** `82ad84e`  
**Preset:** Lean+build  
**Features:** **F40**

## Outcome

**COMPLETED** — Rotating bilingual fun-fact/info messages during ChatRAG cold-start / slow first token, soft donate CTA, cookie + localStorage consent (ADR-039). Shipped to `main` and live on staging ChatRAG FE.

## Routing executed

| Stage | Result |
|-------|--------|
| 00-context | completed |
| 01-requirements | completed — RD-183–187; ADR-039; UJ-052; TC-156–160; AC-CS1–8 |
| 02-verify-plan | completed — Gate A→B PASS; M1–M3 A |
| 07-build | completed — ColdStartWait, facts/prefs, ChatPanel wiring |
| 08-verify-build | PASS |
| 10-e2e | PASS — UJ-052 Playwright + Vitest |
| 13-deploy-smoke | PASS — merge #157; H0ci; DO CD; F40 FE live; H4/H5 PASS |

Skipped (Lean+build): 03–06, 09, 11–12.

## Evidence

| Artifact | Path |
|----------|------|
| Requirements | `reports/01-requirements-cold-start-ux.md` |
| Verify plan | `reports/02-verify-plan-audit.md` |
| Build | `reports/07-build-cold-start-ux.md` |
| Verify build | `reports/verification-report.md` |
| E2E | `reports/e2e-report.md` |
| Deploy smoke | `reports/deploy-smoke.md` |
| ADR | `docs/adr/ADR-039-chat-cold-start-fun-fact-consent.md` |

## Deploy close-out

| Step | Result |
|------|--------|
| Merge #157 | `82ad84e` on `main` |
| H0ci (`ci.yml` + `deploy-preflight.yml`) | **PASS** @ `82ad84e` |
| Deploy Modal + DigitalOcean | **PASS** |
| Staging ChatRAG FE | F40 markers live (`index-Biqk9SBJ.js`) |
| H0c + H4/H5 | **PASS** post-merge |

## Deferrals / follow-ups

- Optional: 15-service-health live cold-start observation on staging
- Optional: close GitHub #87 after user confirmation
