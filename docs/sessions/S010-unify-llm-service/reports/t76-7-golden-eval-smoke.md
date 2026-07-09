# T76.7 — Golden eval `qwen3:8b` smoke (AC-E32)

> **Session:** S010-unify-llm-service  
> **Task:** T76.7  
> **Date:** 2026-07-09  
> **Branch:** `feat/S010-unify-llm-service`

## Objective

Verify golden-eval RAG path uses **`vecinita-llm`** only (no `VECINITA_MODAL_OLLAMA_URL`)
with Ollama-style tag **`qwen3:8b`** after `vecinita-ollama` de-deploy (AC-E32).

## Preconditions

| Check | Status |
|-------|--------|
| `VECINITA_MODAL_LLM_URL` set | ✅ |
| `VECINITA_MODAL_OLLAMA_URL` unset | ✅ |
| `vecinita-ollama` stopped | ✅ 2026-07-08 |
| `qwen3:8b` staged on `llm-models` volume | ✅ HF `Qwen/Qwen3-8B-AWQ` |

## Fixes applied during smoke

| Issue | Resolution |
|-------|------------|
| fp16 `Qwen3-8B` CUDA OOM on T4 | Registry maps `qwen3:8b` → `Qwen/Qwen3-8B-AWQ`; vllm `>=0.8.5` |
| `max_model_len=1024` too small for RAG prompt (1561 tokens) | Raised to **2048** via `_max_model_len_for()` |
| Stale warm container kept 1024 limit | `modal app stop vecinita-llm` + redeploy |

## Command

```bash
set -a && source prod.env && set +a
unset VECINITA_MODAL_OLLAMA_URL
uv run python scripts/smoke/t76_7_golden_eval_qwen3_llm.py --limit 1
```

## Result — PASS (2026-07-09)

```
==> POST /generate model_id='qwen3:8b' (loads model if needed)
    generate (69.6s): "ay, but I need to know if you're a human or AI. How"
==> Golden eval smoke: 1 row(s), model_id='qwen3:8b'
    completed in 13.5s
    retrieval_relevance=0.00
    latency_p95_ms=13393
    - community-food-pantry: answer_len=316 latency=13393ms
OK: T76.7 smoke passed
```

## AC-E32

- [x] Golden eval with Ollama-style tag `qwen3:8b` completes against **`vecinita-llm`**
- [x] After `vecinita-ollama` de-deploy

## Notes

- First `/generate` cold-load ~70s (AWQ Qwen3-8B on T4).
- `retrieval_relevance=0.00` on one golden row is acceptable for connectivity smoke; AC-E32
  requires completion on `vecinita-llm`, not retrieval quality threshold.
- Smoke script: `scripts/smoke/t76_7_golden_eval_qwen3_llm.py`
