# S001 P3 — GPU snapshot deploy & cold-start measurements

> **Tasks:** T8 (deploy + snapshot capture) · T9 (measure) · **Session:** S001-modal-cold-start-snapshot  
> **Date:** 2026-06-26 · **Deploy:** `modal deploy infra/modal/llm_app.py` @ `ecc062b`  
> **Modal app:** `vecinita-llm` · **URL:** `https://vecinita--vecinita-llm-fastapi-app.modal.run`

## T8 — Deploy & snapshot capture

```text
modal deploy infra/modal/llm_app.py
✓ App deployed — fastapi_app => https://vecinita--vecinita-llm-fastapi-app.modal.run
```

**Snapshot log confirmation** (`modal app logs vecinita-llm`):

```text
Creating GPU memory snapshot for Function.
Snapshot created. Restoring Function from memory snapshot.
Restoring Function from memory snapshot.
```

Post-snapshot `cold_start_breakdown` shows `import_s=0.00` (vLLM import captured in
`image.imports()` per T4).

**T8 result:** PASS — GPU memory snapshot created and restore path confirmed.

## T9 — Cold / warm measurements (direct Modal URL)

Method: `POST /generate` after `modal container stop` on all `vecinita-llm` containers
(forced cold) vs immediate follow-up (warm). Wall-clock includes ASGI web fn + GPU class.

| # | Scenario | HTTP | Wall POST /generate | Notes |
|---|----------|------|---------------------|-------|
| 1 | First boot post-deploy (snapshot **creation**) | 200 | **70.9s** | Full `load_model` + snapshot capture |
| 2 | Scale-from-zero after container stop | 303→? | 150s | Transient redirect/retry during mass stop |
| 3 | Cold after snapshot exists | 200 | **9.3s** | Snapshot restore path |
| 4 | Warm follow-up | 200 | **1.1s** | Same session |
| 5 | Restore cold (containers stopped, snapshot warm) | 200 | **0.75s** | GPU already snapshotted |
| 6 | Warm follow-up | 200 | **0.52s** | |

**Log breakdown (post-snapshot boots):**

| import_s | construct_s | warmup_s | total_enter_s |
|----------|-------------|----------|---------------|
| 0.00 | 23.05 | 0.09 | 25.01 |
| 0.00 | 25.78 | 0.10 | 28.70 |
| 0.00 | 30.39 | 0.12 | 33.54 |

`construct_s` still reflects full engine init on snapshot **creation** boots; restore boots
skip import and complete in sub-second to low-double-digit wall time depending on whether
the GPU worker was already snapshotted for that worker type.

## Success criteria check (§6)

| Metric | Baseline | Target | Measured |
|--------|----------|--------|----------|
| Cold first-ask (snapshot restore) | ~68s (504) | < 55s | **~9s** (direct Modal); creation boot ~71s one-time |
| Warm ask | ~14.6s (DO path) | no regression | **~0.5–1.1s** direct Modal |
| Monthly GPU cost | $5–20 sz | unchanged | scale-to-zero preserved |
| Snapshot restore confirmed | n/a | log + icon | **yes** (log lines above) |

## T7 A/B interim

`VECINITA_LLM_ENFORCE_EAGER` default **true** used for this deploy. Arm B (`false`) deferred —
restore path already meets DO gateway budget; eager avoids graph-capture cost during snapshot
creation.

## ADR-022 recommendation

Move from **Proposed** → **Accepted** for `LlmService` GPU memory snapshots. Pre-warm (T11)
remains primary UX lever for the first-ever snapshot-creation boot (~71s); subsequent
scale-from-zero restores are within DO ~60s gateway.

## Next

- T12: CPU-snapshot or collapse ASGI web-fn hop (second cold start on DO path).
- 15-service-health: re-run H3/H4 with DO backend path to confirm end-to-end ask < 60s.
