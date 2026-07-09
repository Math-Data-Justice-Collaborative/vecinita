# Context brief — S010 unify vecinita-llm (EV-011)

**Session:** S010-unify-llm-service  
**Date:** 2026-07-08  
**ADR:** [ADR-037](../../adr/ADR-037-unified-vecinita-llm-modal-app.md)

## Executive summary

Consolidated Vecinita's split Modal LLM surface (`vecinita-llm` + `vecinita-ollama`) into a
single **`vecinita-llm`** app. vLLM remains the sole inference engine (ADR-009). Model download
uses **HuggingFace Hub** into the **`llm-models`** volume because vLLM cannot read Ollama's blob
store. Playground Ollama-style tags are preserved via `llm_model_registry.py`.

## Resolution log

| # | Category | Resolution |
|---|----------|------------|
| R1 | Contradiction | User requested "vLLM serves ollama-pulled models" — **rejected** (incompatible formats). **Adopted:** HF Hub download + vLLM serve (ADR-037 §R1). |
| R2 | Decision | Single volume **`llm-models`** (user choice); re-stage weights; no migration from `vecinita-models`. |
| R3 | Decision | One active vLLM model per GPU instance; `/warm` + engine reload on tag switch. |
| R4 | Decision | New session **S010** / **EV-011** (not extending S009). |
| R5 | Decision | Keep `/models/ollama` API paths for frontend compat; remove `VECINITA_MODAL_OLLAMA_URL` from DO specs. |

## Template / deploy

| Field | Value |
|-------|-------|
| Canonical app | `vecinita-llm` |
| Deprecated app | `vecinita-ollama` (de-deploy after smoke) |
| Volume | `llm-models` |
| GPU | T4 |
| Download fns | `stage_llm_weights`, `stage_default_model`, `pull_model_job` |

## Consumer wiring

| Consumer | Before | After |
|----------|--------|-------|
| ChatRAG | Ollama URL preferred | `VECINITA_MODAL_LLM_URL` only |
| Eval | Ollama branch when OLLAMA_URL set | Always `VECINITA_MODAL_LLM_URL` + `model_id` |
| Playground pull/list | `OllamaModelsClient` → ollama app | Same client → llm app routes |
| `scripts/deploy/modal.sh` | Deploy both apps | Deploy llm only |

## Operator follow-up (post-merge)

1. `modal deploy infra/modal/llm_app.py`
2. `modal run infra/modal/llm_app.py::stage_default_model`
3. Sync DO: drop `VECINITA_MODAL_OLLAMA_URL`, confirm `VECINITA_MODAL_LLM_URL`
4. `modal app stop vecinita-ollama` (or delete app in dashboard)
5. Golden eval smoke with `qwen3:8b` tag

## Persisted pattern

Cursor rule: `.cursor/rules/unified-vecinita-llm.mdc`
