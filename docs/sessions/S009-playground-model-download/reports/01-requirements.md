# 01-requirements report — S009 / EV-010 / F38

**Session:** S009-playground-model-download  
**Evolve cycle:** EV-010  
**Feature:** F38 — Playground model download (super-admin)  
**Date:** 2026-07-05  
**Mode:** delta (evolve-lite)

## Interview summary

User request: super-admins download additional Ollama models for the eval playground; testing is a first-class requirement.

Prior **00-context** (R76–R82) established session scope, auth split, polling UX, and full-stack test intent. This stage resolved remaining product gaps and wrote standing-doc deltas.

## Decisions recorded

| ID | Topic | Decision |
|----|-------|----------|
| RD-146 | Document manifest | feature-list, user-journeys, test-plan, api-contract, acceptance-criteria |
| RD-147 | Pull auth | Super-admin only; admin `403`; list unchanged for admin |
| RD-148 | Model tags | Free-text Ollama tag (non-empty, max 128) |
| RD-149 | Concurrent pulls | Allow parallel duplicate pulls |
| RD-150 | Progress UX | Poll every 10s, 30 min timeout |
| RD-151 | Admin UI | Download section hidden for non-super-admin |
| RD-152 | Testing | Integration + Vitest + API E2E + Playwright |
| RD-153 | Feature ID | F38 (separate from F37) |

## Artifacts updated

| Document | Changes |
|----------|---------|
| `docs/feature-list.md` | Added F38; F37 auth note references F38 for pull |
| `docs/user-journeys.md` | Added UJ-048 with cross-component interaction notes |
| `docs/test-plan.md` | Revised TC-134; added TC-135–TC-138 |
| `docs/api-contract.md` | Added §EV-010 Ollama list/pull routes + polling contract |
| `docs/acceptance-criteria.md` | Added AC-E27–AC-E29 |
| `docs/decisions.md` | Added §EV-010 requirements decisions RD-146–RD-153 |

## Test requirements (by layer)

| Layer | Cases | Module |
|-------|-------|--------|
| Integration | TC-134 | `tests/integration/test_ollama_models_list.py` — auth matrix |
| Vitest | TC-135, TC-136 | `test_evaluation_playground.test.tsx` |
| API E2E | TC-138 | `tests/e2e/test_uj048_playground_model_download.py` |
| Playwright T0-ui | TC-137 | `tests/ui/admin/uj048-playground-model-download.spec.ts` |
| Unit (client) | — | `admin.ts` `pullOllamaModel()` + `admin.test.ts` (04-tech-plan) |

## Gaps / deferred

- Ollama catalog browser — out of scope v1
- Auto-pull on eval run when model missing — out of scope v1
- `VECINITA_MODAL_OLLAMA_URL` production wiring — deploy checklist note (not F38 blocker)
- Branch base `feat/S009-playground-model-download` from `main` — confirm at 07-build

## Contradictions resolved

| Source | Issue | Resolution |
|--------|-------|------------|
| TC-134 (F37) | Expected admin pull `202` | Revised — super-admin only (RD-147) |
| Current code | `WriteActorDep` on pull route | Spec requires `SuperAdminActorDep` (M71) |
| ADR-035 RD-141 | Background pull on missing model | F38 = explicit super-admin UI pull; no auto-pull v1 |

## Next step

**04-tech-plan** — milestones M71–M73, TDD task breakdown, auth change + UI wire-up + test matrix.
