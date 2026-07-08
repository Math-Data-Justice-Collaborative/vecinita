# S010 — Unify vecinita-llm Modal service (EV-011)

**Type:** feature (architectural consolidation)  
**Branch:** `feat/S010-unify-llm-service`  
**Orchestrator:** 16-evolve  

## Intent

Deprecate `vecinita-ollama` and consolidate all LLM inference, model download/staging, and
playground list/pull routes onto **`vecinita-llm`** with vLLM as the sole engine (ADR-037).

## Scope

- Extend `infra/modal/llm_app.py` with `pull_model_job`, `stage_default_model`, manifest, model routes
- HF Hub downloads (not `ollama pull`) into `llm-models` volume
- Wire clients: `LlmClient`, `OllamaModelsClient`, eval, chat-rag, internal-write-api
- Remove `VECINITA_MODAL_OLLAMA_URL` from DO deploy specs
- De-deploy `vecinita-ollama` on Modal (operator step post-smoke)

## Out of scope

- Frontend API path rename (`/models/ollama` kept for compat)
- Re-migrating legacy `vecinita-models` Ollama blobs (re-stage via HF)

## ADR

`docs/adr/ADR-037-unified-vecinita-llm-modal-app.md`
