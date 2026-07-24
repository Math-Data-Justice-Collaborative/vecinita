# 04-tech-plan — S010 unified vecinita-llm (EV-011 / F39)

**Session:** S010-unify-llm-service  
**Evolve cycle:** EV-011 (F39)  
**Date:** 2026-07-08  
**Status:** Complete — superseded in part by **2026-07-10 delta reopen**

> **Delta reopen (2026-07-10):** Phase 18 client consolidation (slices A–E / M77–M81) is
> documented in
> [`04-tech-plan-client-consolidation.md`](./04-tech-plan-client-consolidation.md)
> (TP-S010-17–31). This file remains the Phase 17 (M74–M76) host-unify record.

## Intent

Delta technical plan to consolidate Vecinita's split Modal LLM surface (`vecinita-llm` +
`vecinita-ollama`) into a **single `vecinita-llm` app** with vLLM as the sole inference engine,
HF Hub model staging, and unified consumer wiring. Deprecate and de-deploy `vecinita-ollama`.

User-provided prior-state analysis (two-app eval routing, qwen3 golden eval on Ollama, hotfix scope)
is recorded in [ADR-037](../../../adr/ADR-037-unified-vecinita-llm-modal-app.md) §Prior state and
the eval routing mermaid diagram.

## Prerequisites (verified)

| Prerequisite | Status | Evidence |
|--------------|--------|----------|
| 01-requirements complete | met | `reports/01-requirements.md`; RD-154–RD-162 |
| F39 in feature-list | met | `docs/feature-list.md` §F39 |
| ADR-037 accepted | met | `docs/adr/ADR-037-unified-vecinita-llm-modal-app.md` |
| F38 UI/API baseline | met | S009 M71–M72 on branch; UJ-048, TC-134–TC-138 |
| evolve-lite routing | met | skips 02/03/05/06 |

## Interview resolutions (04-tech-plan)

Requirements stage resolved product gaps (RD-154–162). This stage locks implementation choices:

| Topic | Decision | ID |
|-------|----------|-----|
| Build order | M74 → M75 → M76 | TP-S010-01 |
| Branch base | `feat/S010-unify-llm-service` from `main` | TP-S010-02 |
| Modal app | **`vecinita-llm` only** — delete `ollama_app.py`; no deploy | TP-S010-03 |
| Download | HF Hub `snapshot_download` into **`llm-models`** — not `ollama pull` | TP-S010-04 |
| Modal functions | `stage_llm_weights`, `stage_default_model`, `pull_model_job` on `llm_app.py` | TP-S010-05 |
| Model registry | `llm_model_registry.py` — Ollama-style tag → HF repo | TP-S010-06 |
| Inference | vLLM only; optional `model_id` on `/generate`, `/warm` triggers engine reload | TP-S010-07 |
| Eval routing | `eval_runtime_for_config` always `VECINITA_MODAL_LLM_URL`; no Ollama URL branch | TP-S010-08 |
| Playground client | `OllamaModelsClient` → `vecinita-llm` `/models/ollama*` (path compat) | TP-S010-09 |
| Env | Drop `VECINITA_MODAL_OLLAMA_URL` from DO specs; warn-only in legacy clients | TP-S010-10 |
| Deploy script | `scripts/deploy/modal.sh` deploys llm only | TP-S010-11 |
| Secret migration | ASGI uses `vecinita-ollama` secret during migration; merge into `vecinita-llm` before de-deploy | TP-S010-12 |
| Operator de-deploy | `modal app stop vecinita-ollama` after 13-deploy-smoke | TP-S010-13 |
| Re-stage | `modal run infra/modal/llm_app.py::stage_default_model` post-deploy; no blob migration | TP-S010-14 |
| Dependencies | `huggingface-hub` on llm image (already present); no new runtime deps | TP-S010-15 |
| PR | Single evolve-lite **PR-53** to `main` | TP-S010-16 |

## Early 07-build note

Branch `feat/S010-unify-llm-service` already contains partial M74–M75 implementation (commits
`7c6532a`–`98e9820`). Phase 17 task statuses reflect **actual branch state**; remaining work is
docs/operator steps (M76) and verify/deploy stages.

## Execution plan delta

**Phase 17** appended — 3 milestones, **22 tasks** (T74.1–T76.7):

| Milestone | Focus | Feature | Tasks |
|-----------|-------|---------|-------|
| M74 | Unified Modal app (vLLM + HF staging + model routes) | F39 | T74.1–T74.8 |
| M75 | Consumer wiring + eval routing | F39 | T75.1–T75.7 |
| M76 | Deprecation cleanup + deploy gate | F39 | T76.1–T76.7 |

**Current State pointer:** Phase 17 / M76 / T76.4 (docs gate; operator steps at 13-deploy-smoke).

## Test matrix (handoff to 07-build / verify)

| TC | Layer | Module | Milestone | Branch status |
|----|-------|--------|-----------|---------------|
| TC-139 | Unit (Modal) | `test_llm_volume_manifest.py` | M74 | ✅ on branch |
| TC-140 | Unit (eval) | `test_modal_llm_model_routing.py` | M75 | ✅ on branch |
| TC-134 | Integration | `test_ollama_models_list.py` | M75 | verify unchanged |
| TC-138 | API E2E | `test_uj048_playground_model_download.py` | M75 | verify unchanged |
| Bug guards | Unit | `test_bug_2026_07_05/07/08_*` | M76 | ✅ aligned on branch |
| AC-E32 | T3 staging | golden eval `qwen3:8b` on `vecinita-llm` | M76 | pending operator |

**Acceptance:** AC-E31 (LLM URL only in deploy specs), AC-E32 (golden eval post de-deploy),
AC-E33 (`modal.sh` llm-only), AC-E30 updated (`llm-models` volume per ADR-037).

## Deploy order (EV-011)

1. **Modal** — `modal deploy infra/modal/llm_app.py` (unified surface)
2. **Stage weights** — `modal run infra/modal/llm_app.py::stage_default_model`
3. **DO secrets** — confirm `VECINITA_MODAL_LLM_URL` on internal-write-api + chat-rag; **no** `VECINITA_MODAL_OLLAMA_URL`
4. **DO apps** — redeploy internal-write-api, chat-rag-backend (if env changed)
5. **De-deploy** — `modal app stop vecinita-ollama` (operator, post-smoke)
6. **Smoke** — playground pull + golden eval with `qwen3:8b` tag (AC-E32)

## Artifacts produced

| Artifact | Path |
|----------|------|
| ADR (updated) | `docs/adr/ADR-037-unified-vecinita-llm-modal-app.md` — prior routing mermaid |
| ADR (superseded note) | `docs/adr/ADR-036-ev010-playground-model-download.md` |
| Execution plan | `docs/sessions/S000-internal-docs-archive/execution-plan.md` — Phase 17, PR-53 |
| Roadmap | `docs/sessions/S010-unify-llm-service/roadmap.md` |
| Decisions log | `docs/decisions.md` — TP-S010-01–16 |
| Cursor rule | `.cursor/rules/unified-vecinita-llm.mdc` (existing) |

## Phase 17 gate criteria (T76.4 — at 08-verify-build)

| Gate item | Target |
|-----------|--------|
| M74–M76 code tasks | All complete |
| TC-139, TC-140 | Green at T2 |
| TC-134, TC-138 | Green at T2 (UJ-048 backend on llm app) |
| AC-E31–AC-E33 | Met at T2 docs; AC-E32 at T3 post de-deploy |
| **Modal storage** | Pulls target `llm-models` volume; manifest contract green (TC-139) |
| **No ollama app** | `ollama_app.py` absent; `modal.sh` llm-only |
| Python deps | No new runtime deps (TP-S010-15) |
| Lint / typecheck / tests | Full backend + DM-frontend suites green |

**T3 operator (13-deploy-smoke):** De-deploy `vecinita-ollama`; golden eval `qwen3:8b`; playground HF pull smoke.

## Handoff

**Next stage:** **07-build** — complete remaining M76 docs/operator tasks; run full verify pipeline.

**Note:** S009 Phase 16 T73.5 gate remains open on parked branch; S010 supersedes Modal backend
for F38 without frontend changes.
