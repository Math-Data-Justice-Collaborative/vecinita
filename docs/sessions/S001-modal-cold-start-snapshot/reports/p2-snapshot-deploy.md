# S001 P2/P3 — GPU snapshot deploy + cold-start validation

> **Tasks:** T8 (deploy + snapshot confirm) · partial T9 (initial measurements)  
> **Session:** S001-modal-cold-start-snapshot  
> **Date:** 2026-06-26  
> **Deploy:** `modal deploy infra/modal/llm_app.py` (vLLM **0.7.0**, GPU snapshot enabled)  
> **Modal app:** `vecinita-llm` · **URL:** `https://vecinita--vecinita-llm-fastapi-app.modal.run`

## Deploy

```text
modal deploy infra/modal/llm_app.py
✓ App deployed in 154.6s
✓ fastapi_app => https://vecinita--vecinita-llm-fastapi-app.modal.run
```

Image build installed `vllm-0.7.0` with snapshot env vars (`TORCHINDUCTOR_COMPILE_THREADS=1`,
`XFORMERS_ENABLE_TRITON=1`). `LlmService` has `enable_memory_snapshot=True` +
`experimental_options={"enable_gpu_snapshot": True}` and split enter (`sleep(level=1)` /
`wake_up()`).

## Snapshot confirmation (T8)

After deploy + several cold boots (stop containers → `POST /generate` or `/warm`):

| Signal | Result |
|--------|--------|
| Log line `Restoring Function from memory snapshot.` | **Seen** on GPU container `ta-01KW0QA6WH8YBDABT5J7BRK0CR` |
| `Snapshot created.` | Expected on first boots per worker type (Modal recaptures 2–3× per GPU); not captured in this shell session |
| Containers tab restore icon | Operator verify in [Modal dashboard](https://modal.com/apps/vecinita/main/deployed/vecinita-llm) |

## Latency samples (partial T9)

Method: `modal container stop` all `vecinita-llm` containers → wait → timed `curl`.
Stopping containers mid-request can yield HTTP 500 (`Server has lost track of input`) — excluded.

| Scenario | Wall time | Notes |
|----------|-----------|-------|
| First cold `/warm` post-deploy | **46.2s** | Snapshot creation path (no restore yet) |
| Forced cold `/warm` (containers stopped) | **35.2s** | After initial snapshot capture |
| Forced cold `/generate` (snapshot restore) | **21.5s** | Log shows **memory snapshot restore** on GPU container |
| Warm `/generate` (same session) | **~1–2s** | No container stop between requests |
| Warm `/warm` | **<1s** | ASGI + warm GPU class |

**vs P1 baseline:** cold end-to-end was ~42–52s (instrumentation only); pre-snapshot baseline ~68s (504).
Snapshot-restore cold `/generate` at **21.5s** is under the DO ~60s gateway ceiling.

## Issues observed

- Abrupt `modal container stop` during in-flight `/warm` → HTTP 500 (`internal error: Server has lost track of input`). Same as P1 traces — not a regression.
- `modal app logs vecinita-llm` streams indefinitely; use `modal container logs <id>` with timeout for scripted collection.

## Next

- **T7:** A/B `enforce_eager` on/off with snapshot (optional — eager already ships; measure if snapshot makes graphs redundant).
- **T9:** Full cold/warm ask via ChatRAG path → `15-service-health` + update ADR-022 status if win holds.
- **T12:** CPU-snapshot or collapse ASGI web-fn hop (second scale-to-zero container).
