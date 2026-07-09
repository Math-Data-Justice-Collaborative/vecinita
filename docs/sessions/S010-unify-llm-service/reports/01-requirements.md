# 01-requirements — S010 unify vecinita-llm (EV-011)

**Session:** S010-unify-llm-service  
**Date:** 2026-07-08  
**Stage:** 01-requirements (delta)  
**ADR:** [ADR-037](../../adr/ADR-037-unified-vecinita-llm-modal-app.md)  
**Feature:** F39 (unified LLM Modal service); F38 UI unchanged

## Summary

Requirements delta to consolidate Vecinita's split Modal LLM surface into a single **`vecinita-llm`**
app. vLLM is the sole inference engine. Model download/staging uses **HuggingFace Hub** into the
**`llm-models`** volume. **`vecinita-ollama`** is deprecated and will be de-deployed after smoke.

User-provided prior-state analysis (two-app eval routing, qwen3 golden eval on Ollama) is recorded
in ADR-037 §Prior state and decisions RD-154–RD-162.

## Interview outcomes

| # | Topic | Resolution |
|---|-------|------------|
| 1 | Canonical service | `vecinita-llm` only (RD-154) |
| 2 | Download | HF Hub `pull_model_job` / `stage_default_model` — not `ollama pull` (RD-155) |
| 3 | Volume | `llm-models` only; re-stage; no blob migration (RD-160) |
| 4 | Eval routing | Always `VECINITA_MODAL_LLM_URL` + `model_id` (RD-157) |
| 5 | API paths | Keep `/models/ollama` for frontend compat (RD-159) |
| 6 | Env | Drop `VECINITA_MODAL_OLLAMA_URL` from deploy specs (RD-161) |
| 7 | Feature ID | F39 new; F38 backend superseded (RD-162) |

## Document manifest (delta)

| Document | Action | Sections updated |
|----------|--------|------------------|
| `docs/feature-list.md` | Updated | F38 backend note; **F39** added |
| `docs/user-journeys.md` | Updated | UJ-048 backend + eval routing note |
| `docs/test-plan.md` | Updated | TC-134, TC-138, TC-139; **TC-140** added |
| `docs/api-contract.md` | Updated | §EV-010 storage + upstream `vecinita-llm` |
| `docs/config-spec.md` | Updated | LLM URL/proxy; deprecated `VECINITA_MODAL_OLLAMA_URL` |
| `docs/deployment-integration.md` | Updated | Services table; EV-010/ADR-037 redeploy order |
| `docs/acceptance-criteria.md` | Updated | AC-E30 volume; **AC-E31–AC-E33** added |
| `docs/decisions.md` | Updated | RD-154–RD-162 |
| `docs/adr/ADR-037-*.md` | Updated | Prior state + 01-requirements stage |
| `.cursor/rules/unified-vecinita-llm.mdc` | Existing | Persisted pattern (no change) |

## Test requirements (by layer)

| Change | Test artifact | TC / path |
|--------|---------------|-----------|
| Contract: storage on `llm-models` | Unit | TC-139 — `tests/unit/modal/test_llm_volume_manifest.py` |
| Contract: eval routing | Unit | TC-140 — `tests/unit/eval/test_modal_llm_model_routing.py` |
| Journey: super-admin pull | Integration | TC-134 — `tests/integration/test_ollama_models_list.py` |
| Journey: super-admin pull | API E2E | TC-138 — `tests/e2e/test_uj048_playground_model_download.py` |
| Journey: download UI | Vitest | TC-135, TC-136 — `test_evaluation_playground.test.tsx` |
| Journey: download UI | Playwright T0-ui | TC-137 — `uj048-playground-model-download.spec.ts` |
| Staging: qwen3 golden eval | T3 live | AC-E32 — post de-deploy smoke |

## Gaps

None — all mandatory delta sections filled from S010 context brief + user interview.

## Next step

**04-tech-plan** — milestones M74–M76, execution tasks, deploy order, secret merge plan.
