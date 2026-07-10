# Context brief — S010 unify vecinita-llm (EV-011)

**Session:** S010-unify-llm-service  
**Date:** 2026-07-08 (updated 2026-07-10 — client consolidation partial re-run)  
**ADR:** [ADR-037](../../adr/ADR-037-unified-vecinita-llm-modal-app.md)

## Executive summary

Consolidated Vecinita's split Modal LLM surface (`vecinita-llm` + `vecinita-ollama`) into a
single **`vecinita-llm`** app. vLLM remains the sole inference engine (ADR-009). Model download
uses **HuggingFace Hub** into the **`llm-models`** volume because vLLM cannot read Ollama's blob
store. Playground Ollama-style tags are preserved via `llm_model_registry.py`.

**2026-07-10 follow-on:** After ADR-037, do **not** build a multi-provider framework. Fold
clients, fix streaming/auth, rename the Ollama compat layer, share prompt/catalog logic, and
isolate prod vs playground engines so `vecinita-llm` is the only mental model.

## Resolution log

| # | Category | Resolution |
|---|----------|------------|
| R1 | Contradiction | User requested "vLLM serves ollama-pulled models" — **rejected** (incompatible formats). **Adopted:** HF Hub download + vLLM serve (ADR-037 §R1). |
| R2 | Decision | Single volume **`llm-models`** (user choice); re-stage weights; no migration from `vecinita-models`. |
| R3 | Decision | One active vLLM model per GPU instance; `/warm` + engine reload on tag switch. |
| R4 | Decision | New session **S010** / **EV-011** (not extending S009). |
| R5 | Decision | Keep `/models/ollama` API paths for frontend compat; remove `VECINITA_MODAL_OLLAMA_URL` from DO specs. |
| R6 | Decision | Host consolidation in **S010/EV-011** (partial 00 re-run; not S011). |
| R7 | Decision | **One client surface** — merge `LlmClient` + `OllamaModelsClient`; vLLM inference + HF downloads. |
| R8 | Decision | **Real vLLM token streaming** into `/generate/stream` SSE (stop word-chunk fake streaming). |
| R9 | Decision | **Proxy key required** on all LLM routes (`/generate`, `/warm`, `/models/*`). |
| R10 | Decision | **Rename** Ollama modules/types → playground/LLM; keep `/models/ollama` path aliases. |
| R11 | Decision | **Shared chat-template** via HF `apply_chat_template`. |
| R12 | Decision | **Catalog gated** by `resolve_hf_repo`; clear errors on unmapped tags. |
| R13 | Decision | **Isolate engines** — separate Modal class for playground; prod pinned to fixed default. |
| R14 | Decision | **Env/doc cleanup** — drop legacy Ollama env fallbacks; fix docstrings; declare `shared-schemas` on `llm-client`. |
| R15 | Decision | **Skip provider ABC** — no multi-provider plugin framework. |
| R16 | Decision | Routing amendment: delta **01 → 04 → 07** (slices A–E) → **08–13**; skip 02/03/05/06. First build slice **A = (1)+(4)**. |

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
| Playground pull/list | `OllamaModelsClient` → ollama app | Merged into unified `LlmClient` → llm app (rename in Slice A) |
| `scripts/deploy/modal.sh` | Deploy both apps | Deploy llm only |

## Build slices (follow-on)

| Slice | Decisions | Focus |
|-------|-----------|--------|
| A (first) | 1 + 4 | One client + rename |
| B | 2 + 3 | Streaming + auth |
| C | 5 + 6 | Chat-template + catalog gate |
| D | 7 | Prod vs playground engines |
| E | 8 | Env/doc cleanup |

See [routing-plan.md](./routing-plan.md).

## Multi-app topology / browser risk

Browser-facing: chat-rag FE + data-management FE (DO). APIs: chat-rag backend, internal-write-api (DO); GPU LLM on Modal (`vecinita-llm`). Cross-origin: FE → DO APIs; DO backends → Modal with `VECINITA_MODAL_PROXY_KEY` (now required on all LLM routes per R9). No BFF planned; hybrid CORS remains the integration risk.

## Operator follow-up (post-merge)

1. `modal deploy infra/modal/llm_app.py`
2. `modal run infra/modal/llm_app.py::stage_default_model`
3. Sync DO: drop `VECINITA_MODAL_OLLAMA_URL`, confirm `VECINITA_MODAL_LLM_URL`
4. `modal app stop vecinita-ollama` (or delete app in dashboard)
5. Golden eval smoke with `qwen3:8b` tag

## Persisted pattern

Cursor rule: `.cursor/rules/unified-vecinita-llm.mdc`
