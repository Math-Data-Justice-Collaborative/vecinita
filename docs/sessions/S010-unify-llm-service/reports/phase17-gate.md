# Phase 17 gate checklist — S010 / EV-011 / F39

> **Session:** S010-unify-llm-service  
> **ADR:** [ADR-037](../../../adr/ADR-037-unified-vecinita-llm-modal-app.md)  
> **Branch:** `feat/S010-unify-llm-service` → `main` (PR-53)  
> **Date:** 2026-07-08

## Build gate (T2 — 07-build / 08-verify-build)

| Criterion | Status | Evidence |
|-----------|--------|----------|
| M74 unified `llm_app.py` (vLLM + HF staging + model routes) | ✅ | `infra/modal/llm_app.py`; `ollama_app.py` removed |
| `llm_model_registry.py` tag→HF mapping | ✅ | `tests/unit/modal/test_llm_model_registry.py` |
| Manifest contract on `llm-models` (TC-139) | ✅ | `tests/unit/modal/test_llm_volume_manifest.py` |
| `modal.sh` deploys llm only (AC-E33) | ✅ | `scripts/deploy/modal.sh` |
| Modal secret `vecinita-llm` (proxy key) | ✅ | `scripts/deploy/sync_llm_secret.sh`; `verify_secrets.sh` |
| Eval routing — no Ollama URL branch (TC-140) | ✅ | `tests/unit/eval/test_modal_llm_model_routing.py` |
| Clients → `VECINITA_MODAL_LLM_URL` only | ✅ | `LlmClient`, `OllamaModelsClient`, `modal_llm.py` |
| DO specs omit `VECINITA_MODAL_OLLAMA_URL` (AC-E31) | ✅ | `infra/do/*.yaml`, `scripts/deploy/do_apps.py` |
| TC-134 integration green | ✅ | 36 tests passed 2026-07-08 |
| TC-138 API e2e green | ✅ | `test_uj048_playground_model_download.py` |
| ruff / basedpyright / full pytest | ⬜ | 08-verify-build |

## Deploy gate (T3 — 12–13)

| Criterion | Status | Evidence |
|-----------|--------|----------|
| `modal deploy infra/modal/llm_app.py` | ✅ | 2026-07-08; `infra/` mount fix for registry |
| `modal run …::stage_default_model` | ✅ | HF download completed |
| DO secrets — LLM URL only, no OLLAMA_URL | ⬜ | Live DO may still have legacy OLLAMA_URL — sync via `do_apps.py` |
| `modal app stop vecinita-ollama` | ✅ | 2026-07-08 |
| Golden eval `qwen3:8b` on `vecinita-llm` (AC-E32) | ✅ | T76.7 — `reports/t76-7-golden-eval-smoke.md` |

## Prior routing (recorded in ADR-037)

Before ADR-037, production configured both `VECINITA_MODAL_LLM_URL` and
`VECINITA_MODAL_OLLAMA_URL`. Eval with `qwen3` tags routed to **`vecinita-ollama`**.
Post-unification, all traffic uses **`vecinita-llm`** with optional `model_id` on `/generate`.

## Verify pipeline pointer

After this gate passes at T2: stages **08-verify-build** → **09-qa** → **10-e2e** → **11-verify-impl**
per `docs/sessions/S010-unify-llm-service/roadmap.md`.
