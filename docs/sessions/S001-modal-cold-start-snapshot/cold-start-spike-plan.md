# Cold-start reduction spike — Modal GPU Memory Snapshots

> Session S001 · ops/perf · Owner: agent + user
> Goal: cut `vecinita-llm` cold start so first cold ask < DigitalOcean ~60s gateway, while
> keeping scale-to-zero (ADR-004 budget). Mechanism under test: **GPU Memory Snapshots**.

## 1. Problem statement (grounded)

Cold path today crosses **two** scale-to-zero Modal containers plus an upstream timeout:

```
ChatRAG FE → DO backend (~60s gateway; VECINITA_REQUEST_TIMEOUT_S=120)
           → vecinita-llm ASGI web fn (CPU, scale-to-zero)        ← cold start #1
              └─ service.complete.remote() → LlmService (T4, sz)  ← cold start #2 (dominant)
```

Dominant cost is `LlmService.load_model()` → `vllm.LLM(...)` in `@modal.enter()`
(`infra/modal/llm_app.py:105`). Measured: cold ≈ 68s (504) vs warm ≈ 14.6s.

Note the cold path crosses **two** scale-to-zero containers in series — the ASGI web fn
(CPU) *and* `LlmService` (T4) — so both boots land on the critical path that already blows
the ~60s DO budget. See §5.1 for the web-fn lever.

## 1a. Priority order (decided 2026-06-25)

Modal's docs are explicit that `@modal.enter` *"doesn't get rid of the latency — it just moves
the latency to the warm-up period"* (cold-start guide). Snapshots shrink that period but, being
**alpha + gated on P1**, may not land. So the lever that reliably defeats the 504 *regardless of
the snapshot outcome* leads:

1. **Pre-warm on session open (PRIMARY)** — overlap the boot with user think-time so containers
   are warm before the first submit. Budget-safe; works whether or not the GPU snapshot gate
   passes. Tracked as T11 — **shipped**: FE POST `/api/v1/warm` on chat mount → backend
   parallel POST `/warm` on Modal LLM + embedding (not `/health`, which only warms ASGI).
2. **P1 instrumentation** (T1–T3) — the docs-mandated gate (init/compilation vs weight-load
   dominance). Expected to pass; confirm with real traces.
3. **GPU snapshot P2/P3** (T4–T9) — only if the gate passes (ADR-022).
4. **CPU-snapshot or collapse the ASGI web fn** (T12) — remove the second cold start from the path.
5. **Scheduled/peak-hours warm dial** (T13) — cost-bounded escape hatch for demos.

## 2. What memory snapshots can and cannot do (Modal docs)

Source: https://modal.com/docs/guide/memory-snapshot · https://modal.com/docs/guide/cold-start

| Helps with (snapshot-able) | Does NOT help (or hurts) |
|----------------------------|--------------------------|
| Library init / imports (torch ≈ 20k file ops) | **Weight loading from Volume** — same distributed FS; snapshot adds overhead |
| JIT / graph compilation (Torch, Triton, CUDA graph capture) | Multi-GPU resource setup (generally incompatible) |
| Post-init warmed CUDA state (with `enable_gpu_snapshot`) | Non-CUDA GPU (graphics) work before snapshot |

API shape:
```python
@app.cls(
    gpu="T4",
    enable_memory_snapshot=True,
    experimental_options={"enable_gpu_snapshot": True},  # alpha
)
class LlmService:
    @modal.enter(snap=True)
    def load(self): ...   # captured in snapshot
    @modal.enter(snap=False)
    def post_restore(self): ...  # runs after restore
```
Snapshots are created **only for deployed apps** (`modal deploy`), recaptured on code/config
change. Full coverage needs **~6 captures for CPU-only** functions and **~2–3 per GPU type** for
GPU functions (snapshots are per worker type).

> **No GA snapshot fallback for the LLM.** The GA CPU-snapshot trick (load weights to CPU in
> `@modal.enter(snap=True)`, move to GPU in `snap=False`; ~3x, *not* alpha) does **not** apply to
> vLLM: `vllm.LLM(...)` initializes CUDA at construction and GPUs are unavailable inside a
> CPU-only `snap=True`. So `LlmService` can only benefit from the **alpha GPU snapshot**. If the
> P1 gate fails, the LLM fallback is the budget-safe combo (§5) — there is no CPU-snapshot middle
> ground for it. (The embedding service is CPU-only, so its CPU snapshot is unaffected.)

## 3. vLLM-specific risks (must design around)

Modal explicitly flags vLLM as a "complex inference engine" needing rewrites:

1. **KV cache**: discard the unfilled KV cache *before* snapshot, recreate on restore (else you
   snapshot/restore meaningless GB of pages). Follow Modal's official vLLM + memory-snapshot
   example.
2. **`torch.compile`** can make snapshot *creation* fail → set
   `TORCHINDUCTOR_COMPILE_THREADS=1`.
3. **xformers** calls `torch.cuda.get_device_capability` on import → can init CUDA with 0 GPUs
   during snapshot → set `XFORMERS_ENABLE_TRITON=1` in the image.
4. **Existing NCCL teardown** (`@modal.exit()` `_shutdown_vllm_engine`, BUG-2026-05-20) must
   stay compatible with snapshot/restore lifecycle.
5. GPU snapshots are **alpha**; driver checkpoint/restore is new. Treat as a spike with a kill
   switch, not a guaranteed win.

## 4. Plan (gated)

### Phase P1 — Instrument & measure (do this first; cheap)

Add timing logs to `LlmService.load_model()` and the request path:
- t0 image-ready → t1 enter start → t2 `vllm.LLM` constructed → t3 weights resident →
  t4 first warm-up token → t5 ready.
- Break out **weight load** vs **engine/CUDA init + graph capture** explicitly.
- Capture from Modal container logs across ≥3 cold starts (snapshots recapture per worker
  type, so sample a few).

**Gate:**
- compilation/init > weight load  → **P2 proceed**.
- weight load dominates → **abort snapshot**; fall back to budget-safe combo; mark ADR-022
  Rejected.

> Prior estimate: Qwen2.5-1.5B in fp16 ≈ ~3 GB; Modal Volumes load at ~1–2 GB/s → weight load is
> only ~2–3s of the ~50s cold overhead. So compilation/engine-init almost certainly dominates and
> the gate is **expected to pass** — but P1 must confirm with real numbers before P2.

### Phase P2 — Snapshot implementation (only if gate passes)

1. Move remote-only imports into `image.imports()` so they land in the snapshot.
2. Split `@modal.enter` into `snap=True` (engine/graph build, warm-up forward pass, **KV cache
   discarded**) and `snap=False` (KV cache recreate / any per-restore reinit).
3. Add `enable_memory_snapshot=True` + `experimental_options={"enable_gpu_snapshot": True}`.
4. Set env: `TORCHINDUCTOR_COMPILE_THREADS=1`, `XFORMERS_ENABLE_TRITON=1`.
5. Keep `enforce_eager` as an A/B variable — snapshotting graph-capture may make eager
   unnecessary; measure both.
6. Preserve `@modal.exit()` NCCL teardown; verify no double-free on restore.

### Phase P3 — Deploy & measure

- `modal deploy infra/modal/llm_app.py`; trigger ≥3 cold starts to force snapshot capture.
- Confirm via logs: `Snapshot created. Restoring Function from memory snapshot.` and the
  Containers tab restore icon.
- Record cold-vs-warm ask latency (15-service-health). Compare to 68s baseline and the <60s
  DO ceiling.

## 5. Budget-safe levers (pre-warm is now PRIMARY, not a fallback)

Independent of the snapshot outcome, these are cheap and reduce cold-start pain:
- **Pre-warm on session open (PRIMARY lever — T11):** FE fires async `/health` to LLM +
  embedding when the chat UI mounts, so boot overlaps user think-time and the first submit hits
  a warm (or warming) container. This is the only lever that defeats the DO 504 *regardless* of
  the snapshot gate, so it leads the plan (see §1a). Cross-app: `apps/chat-rag-frontend` +
  `apps/chat-rag-backend`.
- `enforce_eager=True` in `_llm_engine_kwargs` (skip CUDA graph capture). ✅ shipped.
- Raise `scaledown_window` (LLM 300s — capped to bound idle T4 cost; embedding 600s ✅).
- Add `scaledown_window` + pre-warm to `vecinita-embedding` (cold embed stacks before LLM). ✅
  scaledown shipped.

### 5.1 Collapse / snapshot the ASGI web-fn hop (T12)

The cold path crosses two scale-to-zero containers (§1). The ASGI web fn boots in seconds, but
those seconds land on the critical path that's already over the ~60s DO budget. Two options:
- **CPU memory snapshot** on the web fn (same GA pattern as `EmbeddingService`) — cheap, removes
  its import/init from most boots.
- **Collapse the hop** — serve HTTP directly from the GPU class so there is one cold start, not
  two. Larger change; weigh against keeping the web fn for validation/streaming separation.

### 5.2 Explicitly rejected — do not attempt

- **`buffer_containers`** — provisions extra idle containers *while the Function is active*; it
  does **nothing** when scaling *from* zero (Modal cold-start guide). Useless for our idle→cold
  pattern. Documented here so it isn't retried.
- **`min_containers=1`** — T4 warm 24/7 ≈ $430/mo, ~9x the ADR-004 cap. Off the table as an
  always-on fix (see §scheduled warm dial T13 for the cost-bounded version).

## 6. Success criteria

| Metric | Baseline | Target |
|--------|----------|--------|
| Cold first-ask latency | ~68s (504) | < 55s (under DO gateway) — stretch < 30s |
| Warm ask latency | ~14.6s | no regression |
| Monthly Modal GPU cost | $5–20 (sz) | unchanged (still scale-to-zero) |
| Snapshot restore confirmed | n/a | log line + Containers tab icon |

## 7. Execution tasks

| ID | Task | Phase | Depends on | Status |
|----|------|-------|-----------|--------|
| T1 | Add cold-start timing instrumentation to `LlmService` + log breakdown | P1 | — | completed |
| T2 | Deploy instrumented app to staging; collect ≥3 cold-start traces | P1 | T1 | completed |
| T3 | Decision gate: compilation vs weight-load dominance → proceed/abort | P1 | T2 | completed (PASS → P2) |
| T4 | Move imports to `image.imports()`; add snapshot env vars | P2 | T3 | completed |
| T5 | Split `@modal.enter` snap/non-snap; KV-cache discard+recreate per Modal vLLM example | P2 | T4 | completed |
| T6 | Enable `enable_memory_snapshot` + `enable_gpu_snapshot`; verify `@modal.exit` compat | P2 | T5 | completed |
| T7 | A/B `enforce_eager` on/off with snapshot; pick winner | P2 | T6 | completed |
| T8 | Deploy; force snapshot capture; confirm restore log/icon | P3 | T6 | completed |
| T9 | Measure cold/warm ask; record in 15-service-health; update ADR-022 status | P3 | T8 | completed (preliminary — 15-service-health pending) |
| T10 | (Parallel, budget-safe) ship `enforce_eager` + embedding scaledown | any | — | done (pre-warm split to T11) |
| T11 | **PRIMARY** pre-warm-on-session-open: FE→backend async warm LLM + embedding on chat mount | any | — | completed |
| T12 | CPU-snapshot or collapse the ASGI web-fn hop (remove 2nd cold start from path) | any | — | pending |
| T13 | Scheduled/peak-hours warm dial (cron `min_containers` bump for demos) — cost-bounded | any | — | pending |

### Tier-0/1 shipped (2026-06-25, this session)

Budget-safe levers landed without the snapshot gate (no GPU snapshot, no cost change):

- ✅ `enforce_eager=True` in `_llm_engine_kwargs` (`llm_app.py`) — skips CUDA graph capture
  on `LlmService` and `stage_llm_weights`.
- ✅ `EmbeddingService` `scaledown_window=600` (`embedding_app.py`) — was unset (60s default);
  cheap for a CPU service.
- ✅ `EmbeddingService` **CPU memory snapshot** (`enable_memory_snapshot=True`,
  `FastEmbed` import moved to `image.imports()`, model load **+ warm-up embed** in
  `@modal.enter(snap=True)`). CPU snapshot is GA (not the alpha GPU path); FastEmbed/ONNX is
  CPU-only so no `enable_gpu_snapshot` needed. Modal's ~3x snapshot speedup figure is measured
  for a **sentence-transformers** CPU→GPU `snap`/non-`snap` split on an a10 GPU — same `bge-small`
  *model* but a different framework and mechanism than our pure-CPU FastEmbed/ONNX snapshot, so
  treat 3x as an upper-bound analogy, not a promise. The warm-up embed in `snap=True` folds the
  ONNX session / first-inference init into the snapshot (Modal docs: warm up inside `snap=True`).

Deliberately **not** changed:
- `LlmService` `scaledown_window` left at **300s** — raising it keeps an idle **T4 GPU** alive
  longer (direct ADR-004 cost), so it stays as-is pending a cost decision.
- ASGI web fn CPU snapshot — out of approved scope, marginal (web fn boots in seconds).

**Remaining Tier-0 item:** ~~pre-warm-on-chat-open~~ — **shipped in T11** (cross-app:
`apps/chat-rag-frontend` + `apps/chat-rag-backend` + Modal `/warm` routes).

### T7 — `enforce_eager` A/B (completed 2026-06-25)

Toggle via Modal secret/env `VECINITA_LLM_ENFORCE_EAGER` (`true` default, `false`/`0`/`off`
disables). Compare on two deploys after T8 snapshot capture:

1. **Arm A (default):** `enforce_eager=true` — skips CUDA graph capture at engine init (Tier-0).
2. **Arm B:** `enforce_eager=false` — allows graph capture; may interact with GPU snapshot
   restore differently.
3. **Measure:** `cold_start_breakdown` `construct_s` + wall-clock cold `/generate` (≥3 each).
4. **Interim winner:** **`true` (default)** — P1 traces show engine/CUDA init dominates; eager
   skips graph capture during snapshot *creation*. Arm B remains deployable for P3 confirmation;
   revisit only if T9 shows faster cold restore with graphs snapshotted.

> Validation note: these changes only take measurable effect on a **deployed** app. Snapshots
> capture across the first several boots and per worker type — **~6 captures for CPU-only**
> functions (the embedding service), **~2–3 per GPU type** for GPU functions — so don't conclude
> the embedding snapshot is broken if early boots still re-init. Confirm via the Containers tab
> restore icon and the `Snapshot created. Restoring Function from memory snapshot.` log line,
> then re-measure cold/warm ask in 15-service-health.

## 8. References

- Modal Memory Snapshots: https://modal.com/docs/guide/memory-snapshot
- Modal cold start guide: https://modal.com/docs/guide/cold-start
- Modal vLLM + memory-snapshot example (KV-cache pattern) — locate via Modal examples repo
- ADR-009 (vLLM on T4), ADR-004 (cost), BUG-2026-05-22 (cold-start UX), docs/sessions/S000-internal-docs-archive/reference.md#cost-monitoring-baseline-adr-004
