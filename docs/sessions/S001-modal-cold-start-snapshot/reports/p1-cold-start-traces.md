# S001 P1 — Cold-start instrumentation traces

> **Task:** T2 (deploy + collect ≥3 traces) · **Session:** S001-modal-cold-start-snapshot  
> **Date:** 2026-06-26 · **Deploy:** `modal deploy infra/modal/llm_app.py` @ `f27b477`+  
> **Modal app:** `vecinita-llm` · **URL:** `https://vecinita--vecinita-llm-fastapi-app.modal.run`

## Deploy

```text
modal deploy infra/modal/llm_app.py
✓ App deployed — fastapi_app => https://vecinita--vecinita-llm-fastapi-app.modal.run
```

Instrumented `LlmService.load_model()` logs `cold_start_breakdown` with `import_s`, `construct_s`,
`warmup_s`, and `total_enter_s` (S001 T1).

## Collection method

1. `POST /generate` after stopping all `vecinita-llm` containers via `modal container stop` (forces
   scale-from-zero GPU boot).
2. `modal app logs vecinita-llm` — grep `cold_start_breakdown` and vLLM weight lines.
3. Wall-clock for end-to-end ask (ASGI web fn + GPU class) recorded separately.

## Traces (≥3)

| # | import_s | construct_s | warmup_s | total_enter_s | Wall POST /generate | Weight load (log timestamps) |
|---|----------|-------------|----------|---------------|---------------------|------------------------------|
| 1 | 9.18 | 24.50 | 0.12 | 33.80 | 41.6s (first post-deploy) | ~4s (00:21:15→00:21:19 UTC) |
| 2 | 11.82 | 30.32 | 0.21 | 42.35 | 51.9s | ~5s (00:26:46→00:21:51 UTC) |
| 3 | 8.22 | 23.65 | 0.16 | 32.03 | 42.0s | ~5s (00:28:58→00:29:03 UTC) |

**Raw log lines:**

```text
cold_start_breakdown import_s=9.18 construct_s=24.50 warmup_s=0.12 total_enter_s=33.80 ...
cold_start_breakdown import_s=11.82 construct_s=30.32 warmup_s=0.21 total_enter_s=42.35 ...
cold_start_breakdown import_s=8.22 construct_s=23.65 warmup_s=0.16 total_enter_s=32.03 ...
```

vLLM weight line (all three boots): `Loading model weights took 2.8875 GB` — wall time ~4–5s per
boot from adjacent log timestamps (vLLM does not emit seconds on this line).

## T3 gate analysis (ADR-022)

| Component | Avg (s) | Snapshot-able? |
|-----------|---------|----------------|
| `import_s` (torch/vLLM import) | ~9.7 | Yes (CPU/GPU snapshot) |
| Engine/CUDA init (`construct_s` − weight load) | ~21–25 | Yes (GPU snapshot, alpha) |
| Weight load from Volume | ~4–5 | **No** (Modal docs) |
| `warmup_s` (first token) | ~0.16 | Partially |

**Dominance check:** import + engine init ≈ **31–35s** vs weight load ≈ **4–5s** → **compilation/init
dominates weight load by ~7×**.

**Gate result:** **PASS — proceed to P2** (GPU memory snapshot implementation, T4–T7).

**Notes:**

- End-to-end cold ask (web fn + GPU) is ~42–52s — still above DO ~60s gateway in these samples but
  improved vs ~68s baseline; pre-warm (T11) remains the primary UX lever.
- `/warm` route confirmed 200 after redeploy (~38s cold); early 404 was pre-propagation.
- One forced-cold attempt returned HTTP 500 (`Server has lost track of input`) when stopping
  containers mid-flight — expected; excluded from trace count.

## Next

- T4–T7: GPU snapshot implementation per `cold-start-spike-plan.md` §Phase P2/P3.
- ADR-022 remains **Proposed** until P3 measured win (T9).
