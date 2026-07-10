# S010 — Unify vecinita-llm Modal service (EV-011)

**Type:** feature (architectural consolidation)  
**Branch:** `feat/S010-unify-llm-service`  
**Orchestrator:** 16-evolve  

## Intent

Deprecate `vecinita-ollama` and consolidate all LLM inference, model download/staging, and
playground list/pull routes onto **`vecinita-llm`** with vLLM as the sole engine (ADR-037).

## Scope

### ADR-037 (delivered / in flight)

- Extend `infra/modal/llm_app.py` with `pull_model_job`, `stage_default_model`, manifest, model routes
- HF Hub downloads (not `ollama pull`) into `llm-models` volume
- Wire clients: `LlmClient`, `OllamaModelsClient`, eval, chat-rag, internal-write-api
- Remove `VECINITA_MODAL_OLLAMA_URL` from DO deploy specs
- De-deploy `vecinita-ollama` on Modal (operator step post-smoke)

### Client consolidation follow-on (2026-07-10 decisions)

- One client surface (merge generate + list/pull)
- Real vLLM streaming; proxy auth on all LLM routes
- Rename Ollama naming layer → playground (path aliases kept)
- Shared HF chat-template; catalog gated by HF registry
- Separate playground Modal class; prod model pinned
- Drop legacy Ollama env fallbacks + package doc/deps cleanup

## Out of scope

- Provider ABC / multi-provider plugin framework
- Re-migrating legacy `vecinita-models` Ollama blobs (re-stage via HF)
- Frontend path rename is optional later; `/models/ollama` aliases remain for now

## ADR

`docs/adr/ADR-037-unified-vecinita-llm-modal-app.md`

## Routing

See [routing-plan.md](./routing-plan.md) (amended 2026-07-10).

## Roadmap

`docs/sessions/S010-unify-llm-service/roadmap.md`

## Context brief

`docs/sessions/S010-unify-llm-service/context-brief.md`
