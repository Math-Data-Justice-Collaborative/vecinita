# BUG-2026-05-20 — vLLM Modal log warnings (bfloat16 cast + NCCL)

> Status: **resolved**  
> Feature: **F6** (self-hosted LLM on Modal)  
> Component: `infra/modal/llm_app.py` (`vecinita-llm`)

## Error description

During `modal run` / `LlmService` GPU lifecycle, logs show:

1. `WARNING … config.py:2276] Casting torch.bfloat16 to torch.float16.`
2. `[rank0]:[W520 … ProcessGroupNCCL.cpp:1250] Warning: WARNING: process group has NOT been destroyed before we destruct ProcessGroupNCCL.`

No functional failure; noisy logs and potential resource hygiene on container teardown.

## Error logs

```
WARNING 05-20 17:44:23 config.py:2276] Casting torch.bfloat16 to torch.float16.
[rank0]:[W520 17:45:10.695523189 ProcessGroupNCCL.cpp:1250] Warning: WARNING: process group has NOT been destroyed before we destruct ProcessGroupNCCL. On normal program exit, the application should call destroy_process_group to ensure that any pending NCCL operations have finished in this process.
```

## Symptoms & reproduction

| Field | Value |
|-------|--------|
| Where | Modal `vecinita-llm` — `stage_llm_weights`, `LlmService.complete`, ASGI `/generate` |
| Frequency | Every GPU container exit after vLLM load |
| Repro | `modal run infra/modal/llm_app.py::LlmService.complete --prompt warmup --max-tokens 8` |

## Remediation path

User: fix locally + Modal ephemeral as needed, then deploy.

## Investigation

| # | Hypothesis | Result |
|---|------------|--------|
| H1 | T4 requires fp16; model hub config is bf16 → cast warning | **Likely** — explicit `dtype="float16"` still loads bf16 weights first |
| H2 | Modal `@modal.cls` teardown does not call `destroy_process_group` | **Confirmed** — no `@modal.exit()` handler |
| H3 | Upstream vLLM 0.6.x known NCCL shutdown noise | **Likely** — mitigated by explicit cleanup |

## Root cause

1. **bfloat16 cast**: Qwen HF config defaults to bfloat16; vLLM logs when coercing to fp16 on T4.
2. **NCCL**: Distributed process group initialized by vLLM worker; not destroyed before Modal container exit.

## Spec conformance

| Doc | Result |
|-----|--------|
| `docs/feature-list.md` F6 | In scope |
| `docs/deployment-integration.md` | T4 + vLLM — no conflict |
| `docs/dependency-inventory.md` | vLLM 0.6.x pin unchanged |

**Blocking drift:** none.

## Repro test

| Test | Path | Status |
|------|------|--------|
| Shutdown helper calls `destroy_process_group` when initialized | `tests/bugs/test_bug_2026_05_20_vllm_shutdown_warnings.py` | red → green |

## Fix

- Shared `_llm_engine_kwargs()` with `dtype="half"`, `hf_overrides` for fp16.
- `_shutdown_vllm_engine()` + `@modal.exit()` on `LlmService`; `finally` in `stage_llm_weights`.

## Verification plan

| Layer | Check |
|-------|--------|
| L1 | `pytest tests/bugs/test_bug_2026_05_20_vllm_shutdown_warnings.py` |
| L2 | `modal run …::LlmService.complete` — logs reviewed (warnings reduced/absent) |
| L3 | `modal deploy infra/modal/llm_app.py` |

## TDD iteration log

| Run | Action | Result |
|-----|--------|--------|
| 1 | Add repro test for shutdown helper | green (3/3) |
| 2 | `modal run LlmService.complete` post-deploy | no bf16/NCCL lines in log grep |

## Interview record (Phase 5)

| Question | Answer |
|----------|--------|
| Grouped with BUG-2026-05-21 stream_tokens (Modal LLM) | same Phase 5 session |
| Recurrence risk | Very likely on LLM lifecycle changes |
| Detect earlier | AST / bug repro tests |
| Cursor rule | Shared `modal-llm-method-calls.mdc` (+ exit handler in fix) |

## Prevention & countermeasures

| Action | Status |
|--------|--------|
| `@modal.exit()` + `_shutdown_vllm_engine()` | **done** (fix) |
| `test_bug_2026_05_20_vllm_shutdown_warnings.py` | **done** |
| Cursor rule (lifecycle section in `modal-llm-method-calls.mdc`) | **done** |

## Cursor rule

- **Path:** `.cursor/rules/modal-llm-method-calls.mdc` (§ Container teardown)
- **Declined:** no

## Follow-ups

- None — log hygiene only; no user-facing regression.
