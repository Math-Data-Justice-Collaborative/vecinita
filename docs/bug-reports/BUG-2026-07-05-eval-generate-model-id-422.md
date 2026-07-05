# BUG-2026-07-05 — Eval run 422: model_id rejected by vecinita-llm

**Status:** fixing (local patch ready; deploy pending user approval)  
**Severity:** high  
**Feature:** F36 / EV-009 eval playground (ADR-035)  
**Reported:** 2026-07-05  
**Environment:** Production admin frontend + internal-write-api + Modal vecinita-llm

## Error description

Evaluation run fails with:

```
Evaluation run failed: generate failed with status 422: {"detail":"1 validation error for GenerateRequest\nmodel_id\n  Extra inputs are not permitted [type=extra_forbidden, input_value='qwen2.5:1.5b-instruct', input_type=str]\n  For further information visit https://errors.pydantic.dev/2.13/v/extra_forbidden"}
```

## Error logs

```
generate failed with status 422: {"detail":"1 validation error for GenerateRequest\nmodel_id\n  Extra inputs are not permitted ... input_value='qwen2.5:1.5b-instruct' ..."}
```

## Symptoms & reproduction

- **Where:** Production Evaluation page (playground / run history).
- **When:** After recent S008 deploy; production-only repro per user.
- **Frequency:** User reported intermittent overall; eval 422 occurs when LLM generate is invoked.

## Investigation

1. `EvalConfig.model_id` defaults to `qwen2.5:1.5b-instruct` (Ollama tag).
2. `eval_runtime_for_config()` uses Ollama only when **both** `VECINITA_MODAL_OLLAMA_URL` and `VECINITA_MODAL_PROXY_KEY` are set on internal-write-api.
3. `infra/do/internal-write-api.yaml` declares `VECINITA_MODAL_LLM_URL` but **not** `VECINITA_MODAL_OLLAMA_URL`.
4. Fallback: `LlmClient()` targets vecinita-llm; `_generate_body()` always adds `model_id` when configured.
5. `infra/modal/llm_app.py` `GenerateRequest` uses `extra="forbid"` and has **no** `model_id` field → 422.

## Root cause

**Code bug + config drift:** Eval playground model routing (ADR-035) expects Ollama HTTP API, but production internal-write-api only wires vLLM. `LlmClient` forwards `model_id` to vLLM, which rejects it.

## Remediation path

Local-first fix → PR → deploy after user approval.

## Verification plan

- **Success:** Eval playground run completes without 422; failed runs show real errors/metrics.
- **Checks:** Full main CI parity (local) + PR branch CI after push.
- **Post-deploy:** User watches production.

## Repro test

- `tests/bugs/test_bug_2026_07_05_eval_vllm_rejects_model_id.py`

## TDD iteration log

| # | Date | Action | Result |
|---|------|--------|--------|
| 1 | 2026-07-05 | Added repro asserting vLLM `/generate` body omits `model_id` | RED |
| 2 | 2026-07-05 | `LlmClient._supports_model_id_in_body()` — omit for non-Ollama URLs | GREEN |

## Fix

- `packages/llm-client/vecinita_llm_client/client.py` — only include `model_id` when base URL contains `ollama`
- `infra/do/internal-write-api.yaml` + `scripts/deploy/do_apps.py` — declare/sync `VECINITA_MODAL_OLLAMA_URL` for future Ollama routing

## Spec conformance

| Check | Result |
|-------|--------|
| ADR-035 Ollama playground | Implementation drift — Ollama URL not on internal-write-api |
| llm_app GenerateRequest | Pass — correctly forbids unknown fields |
| LlmClient contract | Drift — must not send Ollama-only fields to vLLM |
