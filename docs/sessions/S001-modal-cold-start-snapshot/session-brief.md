# S001 — Modal LLM cold-start reduction via GPU memory snapshots

> Type: **ops** (performance / infra)
> Status: **in_progress**
> Opened: 2026-06-25
> Branch: `feat/S001-modal-cold-start-snapshot`
> Standing docs touched: `docs/adr/ADR-022-gpu-memory-snapshot-cold-start.md`,
> `docs/reference.md#cost-monitoring-baseline-adr-004` (no change expected), `infra/modal/llm_app.py`

## Intent

Reduce the `vecinita-llm` (and secondarily `vecinita-embedding`) **cold-start latency** so the
first chat question after Modal scale-to-zero stops crossing DigitalOcean's ~60s gateway
timeout. Measured baseline: **cold ask ≈ 68s (504), warm ask ≈ 14.6s** — cold start adds ~50s
(BUG-2026-05-22, service-health 2026-05-21).

The user-selected direction is a **Modal GPU Memory Snapshot spike** — the highest-ceiling
lever (Modal claims 3–10x init speedup) that, unlike `min_containers`, **preserves the
scale-to-zero cost model** required by ADR-004 ($50/mo hard cap, $25/mo target).

## Why snapshots and not "keep it warm"

A T4 kept warm 24/7 ≈ **$430/mo** — ~9x the hard cap. `min_containers=1` is therefore off the
table as an always-on fix. Memory snapshots attack cold-start *latency* while keeping the
container scaled to zero when idle, so they fit the budget envelope.

## Hard gate (from Modal docs)

GPU Memory Snapshots **do not** speed up weight loading from a Volume and can *add* overhead.
They only help with library init (imports, ~20k file ops for torch) and JIT/graph
compilation. **We must instrument the cold path and confirm that compilation/init — not
weight load — dominates before committing to the snapshot rewrite.** If weight load dominates,
the spike fails its gate and we fall back to the budget-safe combo (enforce_eager + pre-warm
on session open + scaledown tuning).

## Scope

- In: `infra/modal/llm_app.py` (vLLM `LlmService`); instrumentation; optional
  `infra/modal/embedding_app.py` snapshot (simpler CPU→GPU split pattern).
- Out: DO topology changes; model swap; multi-GPU; always-on warming (separate decision).

## Linked artifacts

- Plan: `cold-start-spike-plan.md` (this folder)
- Routing: `routing-plan.md` (this folder)
- Decision: `docs/adr/ADR-022-gpu-memory-snapshot-cold-start.md` (Proposed)
- Prior bug: `docs/bug-reports/BUG-2026-05-22-chat-cold-start-network-error.md`
- Constraints: ADR-004 (cost), ADR-009 (vLLM on T4), `docs/reference.md#cost-monitoring-baseline-adr-004`
