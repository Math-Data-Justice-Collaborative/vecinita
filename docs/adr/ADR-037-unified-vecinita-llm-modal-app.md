# ADR-037: Unified `vecinita-llm` Modal app (deprecate `vecinita-ollama`)

**Status:** Accepted  
**Stage:** 00-context + 01-requirements (S010 / EV-011)  
**Date:** 2026-07-08  
**Supersedes in part:** ADR-009 §Ollama fallback; ADR-036 §Modal Ollama app storage

## Context

Vecinita operated **two** Modal LLM apps with split responsibilities:

| App | Engine | Role |
|-----|--------|------|
| `vecinita-llm` | vLLM | Fixed `Qwen2.5-1.5B-Instruct` for ChatRAG, ingest/retag, eval fallback |
| `vecinita-ollama` | Ollama | Arbitrary tag pull (`pull_model_job`, `stage_default_model`), playground download UI (F38), eval when `VECINITA_MODAL_OLLAMA_URL` set |

Production configured both URLs (`prod.env`). Eval routing (`eval_runtime_for_config`) preferred Ollama when the Ollama URL was set, so golden eval with `qwen3` tags hit `vecinita-ollama`, not vLLM. Operating two GPU apps increased deploy surface, secret drift risk, and cold-start debugging cost (BUG-2026-07-07, BUG-2026-07-08).

**User decision (S010):** One canonical Modal app — **`vecinita-llm`** — with vLLM as the sole inference engine. Model download/staging functions move into that app. Deprecate and de-deploy `vecinita-ollama`. Reuse the `llm-models` volume (single volume; re-stage weights). Wire all consumers to `VECINITA_MODAL_LLM_URL` only.

### Prior state (pre-ADR-037)

| App | Engine | Model | Who uses it |
|-----|--------|-------|-------------|
| `vecinita-llm` | vLLM | Fixed `Qwen2.5-1.5B-Instruct` | ChatRAG, ingest/retag, eval **fallback** |
| `vecinita-ollama` | Ollama | Any tag you pull (e.g. `qwen3:…`) | Playground download UI, eval when `VECINITA_MODAL_OLLAMA_URL` set |

**Eval routing (removed):** When `VECINITA_MODAL_OLLAMA_URL` was set, `eval_runtime_for_config()` sent sandbox `model_id` tags (e.g. `qwen3:8b`) to **`vecinita-ollama`**. Without it, eval used **`vecinita-llm`** but ignored `model_id` (fixed vLLM model). Production configured both URLs, so golden eval with qwen3 tags hit Ollama — not vLLM.

**Persisted pattern:** Cursor rule `.cursor/rules/unified-vecinita-llm.mdc`; standing docs reference ADR-037 for all new LLM work.

### Technical constraint (R1)

vLLM **cannot** read Ollama's internal blob store. `ollama pull` writes a proprietary layout; vLLM loads HuggingFace **safetensors** (or experimental single-file GGUF with separate HF tokenizer/config). Therefore:

- **`pull_model_job` / `stage_default_model` download HuggingFace Hub repos** (`huggingface_hub.snapshot_download`) into `llm-models`, not `ollama pull`.
- Playground **model_id tags** (e.g. `qwen2.5:1.5b-instruct`) are preserved in API/manifest; a **tag→HF repo registry** resolves the on-disk path vLLM loads.
- Quantization suffixes on Ollama-style tags (e.g. `-q4_K_M`) map to the **base instruct HF repo**; vLLM serves fp16 on T4.

### Serving constraint (R2)

vLLM loads **one active model per GPU class instance**. Switching the sandbox/eval `model_id` triggers an engine reload (~60–120s). `/warm` accepts `model_id` to fold reload into the warm-up window. ChatRAG production default remains `Qwen2.5-1.5B-Instruct` unless `VECINITA_LLM_MODEL_ID` overrides.

## Decision

1. **Single Modal app:** `vecinita-llm` (`infra/modal/llm_app.py`) is the only LLM deployable.
2. **Inference:** vLLM only (ADR-009 primary engine unchanged).
3. **Volume:** `llm-models` only; manifest at `/models/manifest.json`.
4. **Download functions (Modal):**
   - `stage_llm_weights` — existing default Qwen staging (unchanged entry point).
   - `stage_default_model` — alias staging default playground tag (`qwen2.5:1.5b-instruct`).
   - `pull_model_job(job_id, model_id)` — background HF download + manifest update + `volume.commit()`.
5. **ASGI routes on `vecinita-llm`** (proxy-auth via `X-Vecinita-Proxy-Key`):
   - Existing: `/health`, `/warm`, `/generate`, `/generate/stream`.
   - Migrated from ollama app: `GET /models/ollama`, `POST /models/ollama/pull` (path kept for API compat).
   - `/generate` accepts optional `model_id` (Ollama-style tag); vLLM loads the resolved HF path.
6. **Deprecate `vecinita-ollama`:** remove from `scripts/deploy/modal.sh`; do not deploy. Delete app on Modal after S010 deploy smoke.
7. **Env vars:** consumers use `VECINITA_MODAL_LLM_URL` + `VECINITA_MODAL_PROXY_KEY`. `VECINITA_MODAL_OLLAMA_URL` **removed** from deploy specs (deprecated; clients may log a warning if still set).
8. **Eval routing:** `eval_runtime_for_config` always uses `LlmClient` against `VECINITA_MODAL_LLM_URL`; no Ollama URL branch.

## Alternatives considered

| Alternative | Why rejected |
|-------------|--------------|
| Keep both apps | User rejected; ops/secrets/routing complexity |
| Ollama engine inside unified app | User chose vLLM-only serving |
| `ollama pull` + vLLM serve same blobs | **Incompatible formats** — blocked |
| GGUF download + vLLM experimental GGUF loader | Experimental; multi-file GGUF unsupported; fragile on T4 |
| Two volumes under one app | User chose single `llm-models` volume |

## Consequences

- **F38 playground download UI** unchanged at API boundary (`/internal/v1/models/ollama/*`); backend client targets `vecinita-llm`.
- **Re-stage:** operators run `modal run infra/modal/llm_app.py::stage_default_model` after deploy; existing `vecinita-models` Ollama blobs are **not** migrated (HF re-download).
- **Catalog tags** without HF mapping fail pull with explicit error until registry extended.
- **ADR-009** Ollama fallback clause is **closed** — no separate Ollama Modal app.
- **S001** GPU snapshot path on `LlmService` preserved for default model; model-switch reloads bypass snapshot until re-snapshotted.
- Tests: manifest contract moves from `ollama_app` to `llm_app`; eval routing tests drop Ollama URL branch.

## References

- ADR-009, ADR-036, ADR-035
- BUG-2026-07-07-eval-ollama-generate-404, BUG-2026-07-08-eval-ollama-generate-read-timeout
- `docs/deployment-integration.md` §vecinita-llm
- Modal vLLM guide; vLLM GGUF docs (rejected path)
- Resolution **R1** (S010 context brief): HF Hub download, single volume, vLLM-only
