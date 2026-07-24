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

### Client consolidation follow-on (2026-07-10 — Phase 18)

- One `LlmClient` surface (merge generate + list/pull); delete `OllamaModelsClient`
- Real vLLM streaming; ASGI proxy auth on all non-health LLM routes
- Full BE+FE rename Ollama → playground (path aliases kept)
- Shared HF chat-template; catalog gated by HF registry
- **Two Modal apps:** `vecinita-llm` (prod pin) + `vecinita-llm-playground` (shared `llm-models`)
- Drop legacy Ollama env fallbacks + package doc/deps cleanup
- Build: M77–M81 (slices A–E); next **07-build** T77.1

## Out of scope

- Provider ABC / multi-provider plugin framework
- Re-migrating legacy `vecinita-models` Ollama blobs (re-stage via HF)

## ADR

`docs/adr/ADR-037-unified-vecinita-llm-modal-app.md`

## Routing

See [routing-plan.md](./routing-plan.md) (04-tech-plan completed 2026-07-10).

## Roadmap

[roadmap.md](./roadmap.md) — Phase 18 M77–M81 issue map

## Tech-plan report

[reports/04-tech-plan-client-consolidation.md](./reports/04-tech-plan-client-consolidation.md)

## Context brief

`docs/sessions/S010-unify-llm-service/context-brief.md`

## 01-requirements handoff

`docs/sessions/S010-unify-llm-service/checkpoints/01-requirements-seed.md` — used for 01 delta
(completed). See `.cursor/skills/00-context/SKILL.md` §Phase 4.5 and
`.cursor/skills/01-requirements/SKILL.md` §Phase 0C.
