# Context — EV-311 cold-start latency (#311)

**Session:** `EV-311-infra-sub-second-chatrag-latency-on-cheap-server`  
**Date:** 2026-09-03  
**Mode:** scoped evolve

## Problem

ChatRAG first ask after idle still risks multi-second waits when Modal GPU scales to zero. Wait UX (F40/F64) hides pain; #311 asks for a **latency system** under ADR-004 (not always-on T4).

## Prior art (do not redo)

| Artifact | Outcome |
|----------|---------|
| S001 + ADR-022 | GPU snapshots Accepted; restore sometimes &lt;1s |
| #313 / EV-313 | Prod-only snapshots + sleep/wake; **enabled** staging+prod |
| #316 | LoRA post-restore + SHA-256 |
| #314 | `cold_kind` harness |
| #318 | Async GPU `/warm` |
| #320 / F85 | FAQ fast-path Layer D |
| Open | #315 seed, #317 thin ingress, #319 scaledown (`priority:medium`) |

## Code anchors

- `infra/modal/llm_app.py` — `VECINITA_LLM_GPU_SNAPSHOT`, `VECINITA_LLM_SCALEDOWN_WINDOW`, snapshot enter hooks  
- `docs/adr/ADR-022-gpu-memory-snapshot-cold-start.md` — amendments EV-313…EV-320  
- `docs/config-spec.md` — kill-switches  
- Scripts: `scripts/ops/cold_start_bench.py` (EV-314), seed script intent (#315)

## Must-not-break

Prod pin / playground snapshot-off; LoRA integrity fail-closed; DO gateway no silent 504; ADR-004 budget; stage-before-main.

## Next Spec step

`spec-development/requirements` — lock remaining #311 acceptance given filter `open`+`priority:high` (umbrella close vs expand to medium children).

## Cites

[Corpus: product] [Spec: docs/adr/ADR-022-gpu-memory-snapshot-cold-start.md] [Corpus: config] [Corpus: feature-list.md §F85]

## Spec band complete (2026-09-04)

Requirements locked (EV-311-D1–D8). Docs delta: ADR-022 EV-311, AC-311, TC-311, staging-runbook §EV-311, modal README, evolve-decisions.
Documenting verify: all angles PASS.
**Next:** Spec→Build gate AskQuestion → staging harness evidence → fill frontier → close #311.
