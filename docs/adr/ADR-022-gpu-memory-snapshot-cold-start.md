# ADR-022: GPU Memory Snapshots for vLLM cold-start reduction

**Status:** Accepted (S001 P3 — GPU snapshot restore measured ~9s cold vs ~71s creation boot)
**Stage:** 00-context (S001-modal-cold-start-snapshot)
**Date:** 2026-06-25

## Context

`vecinita-llm` (vLLM Qwen2.5-1.5B on T4, ADR-009) runs **scale-to-zero** to stay inside the
ADR-004 budget (≤$50/mo hard, ≤$25/mo target). The cost of that is cold starts: the first chat
question after idle measures **~68s and returns 504** (exceeds DigitalOcean's ~60s gateway),
versus **~14.6s warm** (BUG-2026-05-22, service-health 2026-05-21). The dominant cost is
`vllm.LLM(...)` initialization in `LlmService.load_model()`.

The obvious fix — `min_containers=1` (always warm) — is rejected: a T4 warm 24/7 ≈ **$430/mo**,
~9x the hard cap. We need to cut cold-start *latency* while keeping the container scaled to zero
when idle.

Modal **Memory Snapshots** (CPU + alpha GPU) serialize post-initialization container state so
later boots restore instead of re-initializing, claimed 3–10x init speedup — without keeping
containers warm. This preserves the scale-to-zero cost model.

## Decision

**Proposed:** Adopt **GPU Memory Snapshots** for `LlmService` to reduce cold start, **only if**
instrumentation (S001 Phase P1) confirms that library init + compilation (snapshot-able)
dominates the cold path rather than weight loading (not snapshot-able).

- `enable_memory_snapshot=True` + `experimental_options={"enable_gpu_snapshot": True}`.
- Split `@modal.enter` into `snap=True` (engine/graph build, warm-up, KV-cache discarded) and
  `snap=False` (per-restore reinit).
- Mitigations: `TORCHINDUCTOR_COMPILE_THREADS=1`, `XFORMERS_ENABLE_TRITON=1`, KV-cache
  discard/recreate per Modal's official vLLM example (`sleep(level=1)` / `wake_up()`),
  preserve existing `@modal.exit()` NCCL teardown.
- **vLLM pin:** `0.7.x` in Modal image (sleep mode API; was `0.6.x`).
- **A/B lever:** `VECINITA_LLM_ENFORCE_EAGER` env (default `true`; S001 T7) — staging keeps
  eager on until P3 traces confirm graph-capture + snapshot restore is faster.

This is a **spike with a kill switch**, not a committed design — GPU snapshots are alpha and
vLLM is explicitly flagged by Modal as needing rewrites.

## Decision gate

| Instrumentation result | Outcome |
|------------------------|---------|
| compilation/CUDA init > weight load | Proceed; this ADR moves to Accepted on measured win |
| weight load dominates | **Reject** snapshots (Modal: snapshots don't speed weight load and may add overhead); this ADR → Rejected; fall back to budget-safe combo |

> Note: vLLM has **no GA CPU-snapshot fallback** — `vllm.LLM(...)` initializes CUDA at
> construction, which a CPU-only `@modal.enter(snap=True)` cannot do, so `LlmService` depends on
> the **alpha** GPU snapshot. The "weight load dominates" branch therefore falls back to the
> budget-safe combo, not a CPU snapshot. Estimated weight load for Qwen2.5-1.5B fp16 (~3 GB at
> ~1–2 GB/s) is only ~2–3s, so the gate is expected to pass.

## Alternatives considered

| Alternative | Why not (default) |
|-------------|-------------------|
| `min_containers=1` always warm | ~$430/mo — violates ADR-004 |
| `buffer_containers` | Does nothing when scaling *from* zero (Modal cold-start guide); useless for our idle→cold pattern |
| Scheduled / peak-hours warming | Still meaningful cost; keep as a cost-bounded demo dial (S001 T13), not primary |
| `enforce_eager=True` only | Cheap, ships regardless (S001 T10); smaller ceiling than snapshots |
| Smaller / quantized model | Marginal; weight load isn't confirmed bottleneck; quant kernels add compile |
| Ollama fallback (ADR-009) | Larger change; revisit only if vLLM path can't meet budget+latency |

> **Primary lever runs in parallel, not as an alternative:** pre-warm on session open (S001
> T11) overlaps the boot with user think-time and defeats the DO 504 *regardless* of whether
> this snapshot spike passes its P1 gate. Per Modal's cold-start guide, `@modal.enter` only
> *moves* latency into the warm-up period — pre-warm is what hides that period from the user, so
> it leads the S001 priority order and ships independent of this ADR's outcome.

## Consequences

- **If accepted:** cold start drops without raising idle cost; scale-to-zero preserved. Adds
  alpha-feature risk and vLLM-specific init complexity; snapshots recapture on every deploy and
  across worker types (2–3 captures per GPU).
- **If rejected:** budget-safe combo (T10) still improves cold-start UX; revisit when GPU
  snapshot leaves alpha or model/GPU tier changes.
- Cold-start latency remains excluded from the p95 < 15s target (RD-017) but must be documented
  for ops either way.

## References

- S001 plan: `docs/sessions/S001-modal-cold-start-snapshot/cold-start-spike-plan.md`
- Modal Memory Snapshots: https://modal.com/docs/guide/memory-snapshot
- Modal cold start: https://modal.com/docs/guide/cold-start
- ADR-004 (cost/sovereignty), ADR-009 (vLLM on T4)
- BUG-2026-05-22 (cold-start UX), `docs/cost-monitoring.md`
