# 04-tech-plan — F39 client consolidation (EV-011 follow-on)

**Session:** S010-unify-llm-service  
**Date:** 2026-07-10  
**Stage:** 04-tech-plan (delta reopen)  
**ADR:** [ADR-037](../../../adr/ADR-037-unified-vecinita-llm-modal-app.md) (amended)  
**Feature:** F39 follow-on (no F40)  
**Prior 04:** [04-tech-plan.md](./04-tech-plan.md) (2026-07-08 — Phase 17 / TP-S010-01–16)

## Intent

Map RD-163–RD-172 into **Phase 18** milestones M77–M81 (slices A–E). Do **not** build a
provider plugin system. Fold clients, fix streaming/auth, rename the Ollama layer, share
prompt/catalog logic, isolate prod vs playground as **two Modal apps**.

## Interview resolutions (TP-S010-17–31)

| ID | Topic | Decision |
|----|-------|----------|
| TP-S010-17 | Plan shape | **Phase 18** with M77–M81 (one milestone per slice); keep Phase 17 as history |
| TP-S010-18 | Client API | Expand `LlmClient`; delete `OllamaModelsClient` after migration |
| TP-S010-19 | Rename | Full BE+FE Ollama→playground rename in Slice A; keep `/models/ollama*` aliases |
| TP-S010-20 | Resolver | Shared env/auth/timeout resolver in `packages/shared-schemas` |
| TP-S010-21 | PR | Single evolve PR after A–E (PR-53) |
| TP-S010-22 | Streaming | vLLM `engine.generate` / async iterator → existing SSE |
| TP-S010-23 | Auth | ASGI middleware on all non-health routes; fail closed if proxy key unset in prod |
| TP-S010-24 | Chat template | Helper in `packages/llm-client` (keep schemas free of transformers) |
| TP-S010-25 | Isolation | **Two Modal apps:** `vecinita-llm` + `vecinita-llm-playground` (overrides RD-169 class-only) |
| TP-S010-26 | Catalog | Filter to `resolve_hf_repo`; pull **400** if unmapped |
| TP-S010-27 | Playground URL | `VECINITA_MODAL_LLM_PLAYGROUND_URL`; ChatRAG uses prod URL only |
| TP-S010-28 | Volume | Both apps mount shared **`llm-models`** |
| TP-S010-29 | Env cleanup | Slice E removes Ollama fallbacks; missing LLM URL hard-fails |
| TP-S010-30 | Tests | Per-milestone TDD; FE Vitest+Playwright in M77; stream = API E2E+unit (no stream Playwright) |
| TP-S010-31 | Task grain | ~4–8 TDD tasks per milestone |

**User review:** Approve all (2026-07-10).

## Execution plan delta

**Phase 18** appended — 5 milestones, **31 tasks** (T77.1–T81.5):

| Milestone | Slice | Focus | Tasks |
|-----------|-------|--------|-------|
| M77 | A | One client + rename | T77.1–T77.7 |
| M78 | B | Real streaming + proxy auth | T78.1–T78.6 |
| M79 | C | Chat-template + catalog gate | T79.1–T79.6 |
| M80 | D | Two Modal apps + prod pin | T80.1–T80.7 |
| M81 | E | Env/doc cleanup | T81.1–T81.5 |

**Current State pointer:** Phase 18 / M77 / T77.1.

## Deploy order (Slice D+)

1. Deploy/update **`vecinita-llm`** (prod pin `qwen2.5:1.5b-instruct`)
2. Deploy **`vecinita-llm-playground`** (shared `llm-models`)
3. Set `VECINITA_MODAL_LLM_PLAYGROUND_URL` on internal-write-api / DM
4. ChatRAG keeps `VECINITA_MODAL_LLM_URL` only
5. Smoke: playground pull + prod chat unaffected by playground `model_id`
6. Slice E: remove legacy Ollama env fallbacks

## Test matrix (handoff to 07-build)

| TC | Layer | Milestone |
|----|-------|-----------|
| TC-144 | Unit — unified client | M77 |
| TC-142 / UJ-049 | Unit + integration — proxy auth | M78 |
| TC-143 | Unit + API E2E — real streaming | M78 |
| TC-141 | Unit + UJ-048 e2e — catalog gate | M79 |
| TC-145 | Unit / smoke — chat-template + engine isolate | M79–M80 |
| TC-135–137 | Vitest + Playwright — FE rename | M77 |

## Artifacts produced / updated

| Artifact | Path |
|----------|------|
| Execution plan | `docs/sessions/S000-internal-docs-archive/execution-plan.md` — Phase 18 |
| This report | `docs/sessions/S010-unify-llm-service/reports/04-tech-plan-client-consolidation.md` |
| Roadmap | `docs/sessions/S010-unify-llm-service/roadmap.md` |
| Decisions | `docs/decisions.md` — TP-S010-17–31 |
| ADR | `docs/adr/ADR-037-*.md` — §17–18 two-app isolation |
| Config / deploy / deps | config-spec, deployment-integration, staging-secrets-matrix, dependency-inventory |
| Cursor rule | `.cursor/rules/unified-vecinita-llm.mdc` |

## Handoff

**Next stage:** **07-build** — start **T77.1** (Slice A / M77).

Skipped by routing: 05-verify-tech, 06-tech-tooling.
