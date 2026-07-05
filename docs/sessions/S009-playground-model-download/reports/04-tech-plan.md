# 04-tech-plan — S009 playground model download (EV-010 / F38)

**Session:** S009-playground-model-download  
**Evolve cycle:** EV-010 (F38)  
**Date:** 2026-07-05  
**Status:** Complete — pending user review

## Intent

Delta technical plan for **super-admin-only Ollama model download** on the Evaluation Playground:
tighten pull API auth, add download UI with list polling, and deliver full-stack tests (integration,
Vitest, API E2E, Playwright T0-ui).

## Prerequisites (verified)

| Prerequisite | Status | Evidence |
|--------------|--------|----------|
| 01-requirements complete | met | `reports/01-requirements.md`; RD-146–RD-153 |
| F38 in feature-list | met | `docs/feature-list.md` §F38 |
| UJ-048 / TC-134–138 / AC-E27–29 | met | standing docs updated 2026-07-05 |
| Modal pull infra (F37) | met | `infra/modal/ollama_app.py`, ADR-035 §6 |
| evolve-lite routing | met | `routing-plan.md` — skips 02/03/05/06 |

## Interview resolutions (04-tech-plan)

Requirements stage resolved product gaps (RD-146–153). This stage locks implementation choices:

| Topic | Decision | ID |
|-------|----------|-----|
| Build order | M71 → M72 → M73 | TP-S009-01 |
| Branch base | `feat/S009-playground-model-download` from `main` | TP-S009-02 |
| Pull auth | `SuperAdminActorDep`; list unchanged | TP-S009-03 |
| **Model storage** | **Modal Volume `vecinita-models` only** (`/models`, manifest.json) | **TP-S009-17** |
| Modal app code | No functional changes v1; storage pipeline from F37 | TP-S009-04 |
| FE client | `pullOllamaModel()` in `admin.ts` | TP-S009-05 |
| Poll UX | 10s interval, 30 min timeout | TP-S009-06 |
| UI placement | Config column card below model picker; hidden for non-super-admin | TP-S009-07 |
| i18n | `frontend-i18n` download keys EN/ES | TP-S009-08 |
| Playwright | New `mockAuthenticatedSuperAdmin` helper | TP-S009-09 |
| Dependencies | No new runtime deps | TP-S009-10 |
| Deploy | write-api → admin FE; no migration | TP-S009-11 |
| CORS | Existing POST preflight sufficient | TP-S009-12 |
| OpenAPI | EV-010 pull auth documented | TP-S009-13 |
| Integration tests | Split admin list / super-admin pull / admin 403 | TP-S009-14 |
| TDD | Red tests before implementation per milestone | TP-S009-15 |
| PR | Single evolve-lite PR-52 to `main` | TP-S009-16 |

## Technical decisions (TP-S009-01–17)

See [ADR-036](../../../adr/ADR-036-ev010-playground-model-download.md) for full rationale.

## Execution plan delta

**Phase 16** appended — 3 milestones, **20 tasks** (T71.1–T73.6):

| Milestone | Focus | Feature | Tasks |
|-----------|-------|---------|-------|
| M71 | API auth: super-admin-only pull + Modal storage docs | F38 | T71.1–T71.6 |
| M72 | Playground download UI + poll | F38 | T72.1–T72.7 |
| M73 | Full-stack tests + Modal manifest unit test | F38 | T73.1–T73.6 |

**Current State pointer:** Phase 16 / M71 / T71.1 (first red test).

## Test matrix (handoff to 07-build)

| TC | Layer | Module | Milestone |
|----|-------|--------|-----------|
| TC-134 | Integration + unit | `test_ollama_models_list.py`, `test_app_eval_routes.py` | M71 |
| TC-135 | Vitest | `test_evaluation_playground.test.tsx` | M72 |
| TC-136 | Vitest | `test_evaluation_playground.test.tsx` | M72 |
| TC-137 | Playwright T0-ui | `uj048-playground-model-download.spec.ts` | M73 |
| TC-138 | API E2E | `test_uj048_playground_model_download.py` | M73 |
| TC-139 | Unit (Modal) | `test_ollama_volume_manifest.py` | M73 |

**Acceptance:** AC-E27 (super-admin download + poll), AC-E28 (admin hidden + 403), AC-E29 (full matrix green in CI), **AC-E30** (models persist on Modal `vecinita-models` volume per manifest contract).

## Artifacts produced

| Artifact | Path |
|----------|------|
| ADR | `docs/adr/ADR-036-ev010-playground-model-download.md` |
| Execution plan | `docs/sessions/S000-internal-docs-archive/execution-plan.md` — Phase 16, Current State, PR-52 |
| Roadmap | `docs/sessions/S009-playground-model-download/roadmap.md` |
| Decisions log | `docs/decisions.md` — TP-S009-01–16 |

## Phase 16 gate criteria (T73.5 — at 08-verify-build)

| Gate item | Target |
|-----------|--------|
| M71–M73 tasks | All complete |
| TC-134–TC-138 | Green at T2 |
| UJ-048 | Covered (E2E + Playwright) |
| AC-E27–AC-E29 | Met at T2 |
| Migrations | None required |
| **Modal storage** | Pull targets `vecinita-models` volume; TC-139 manifest contract green |
| Python deps | No new runtime deps (ADR-036 §11) |
| CORS | Existing EV-009 ollama pull preflight still green |
| Lint / typecheck / tests | Full backend + DM-frontend suites green |

**T3 optional:** Manual staging pull smoke when `VECINITA_MODAL_OLLAMA_URL` configured (13-deploy-smoke).

## Handoff

**Next stage:** **07-build** — start T71.1 (integration auth matrix red test).

**Note:** S008 remains parked at 09-qa; F38 does not depend on S008 merge if `main` includes F37
playground baseline (confirm branch base at T71.1).
