# EV-016 model sweep — plan (S019 extension)

> **Session:** S019-retrieval-quality · **Cycle:** EV-016  
> **Decisions:** S019-D15–D18  
> **Date:** 2026-07-31  
> **Status:** gates locked — running Tiny→Large in order (fail/skip)

## Why

Retrieval ablations (A0–A4+R3, A3) held the LLM fixed at **`qwen2.5:1.5b-instruct`**.
Answer relevancy stayed low (≤0.31). Extend Phase 0 to test whether a **stronger open
model** lifts F36 metrics under a **fixed retrieval/packing cell**, before locking F42.

## Fixed experimental factors (proposed — confirm Gate A)

| Factor | Proposed value | Rationale |
|--------|----------------|-----------|
| Corpus / golden | Staging + `qa_pairs_staging.json` | Same as A0–A4 |
| Retrieve | L_none, top_k=5, min_score=0.2 | Matches prior spike path |
| Packing | **P1** (title/URL) | Safest measured lift |
| Rerank | **R0** (no cheap/CE rerank) | Isolate LLM effect |
| Control model | `qwen2.5:1.5b-instruct` | Prod pin / prior baseline |
| Metrics | retrieval, faith, answer_relevancy, latency_p95 | F36 |
| Harness | `scripts/eval_sweep_golden_models.py` + session tracker | Existing golden-sweep |
| Results dir | `docs/sessions/S019-retrieval-quality/reports/eval-experiments/` | Session-scoped |

## Ordered queue (deduplicated from user list)

Leaderboard text listed some models twice; queue below is **unique, in stated order**.

### Tier T — Tiny (≤4B)

| # | Display name | Proposed playground tag | HF repo (candidate) | Hosting note |
|---|--------------|-------------------------|---------------------|--------------|
| T1 | AI9Stars G9v3-3B | `g9v3:3b` | `ai9stars/G9v3-3B` | Needs registry override; may fit playground **T4** |
| T2 | Qwen3 4B 2507 | `qwen3:4b-instruct-2507` | `Qwen/Qwen3-4B-Instruct-2507` | Needs override (plain `qwen3:4b` ≠ 2507) |
| T3 | OpenBMB MiniCPM5-1B | `minicpm5:1b` | `openbmb/MiniCPM5-1B` | Needs new family; T4 candidate |

*(User list repeated MiniCPM5-1B twice — tracked once as T3.)*

### Tier S — Small (4B–40B)

| # | Display name | Proposed tag | HF repo (candidate) | Hosting note |
|---|--------------|--------------|---------------------|--------------|
| S1 | Qwen3.6 27B AWQ | `qwen3.6:27b-awq` | `QuantTrio/Qwen3.6-27B-AWQ` | S019-D19: playground **A10** + AWQ; prior fp16 `qwen3.6:27b` on T4 **invalid** |
| S2 | Qwen3.5 27B AWQ | `qwen3.5:27b-awq` | `QuantTrio/Qwen3.5-27B-AWQ` | S019-D19 A10; **complete — tie @ 0.23** |
| S3 | Qwen3.6 35B A3B FP8 | `qwen3.6:35b-a3b-fp8` | `Qwen/Qwen3.6-35B-A3B-FP8` | S019-D20 A100-80; **complete — tie @ 0.23** (BF16 ~70GB skipped) |

*(User list repeated Qwen3.6 27B — once as S1.)*

### Tier M — Medium (40B–150B)

| # | Display name | Proposed tag / ID | Hosting note |
|---|--------------|-------------------|--------------|
| M1 | Qwen3.5 122B A10B | `qwen3.5:122b-a10b` | Multi-GPU / not on current playground T4 |
| M2 | Mistral Medium 3.5 | TBD (often **API**, not HF self-host) | ADR-009 conflict unless waived |
| M3 | NVIDIA Nemotron 3 Super | TBD HF id | Large; GPU / license check |

*(User list repeated Qwen3.5 122B A10B — once as M1.)*

### Tier L — Large (>150B)

| # | Display name | Variant | Hosting note |
|---|--------------|---------|--------------|
| L1 | Kimi K3 | max | Frontier-scale; self-host unlikely on current Modal |
| L2 | Z.AI GLM-5.2 | max | Same |
| L3 | DeepSeek V4 Flash 0731 | max | Same |
| L4 | Kimi K3 | low | Same family, lower reasoning effort if API |

## Infrastructure constraints (current)

| Surface | GPU | Role |
|---------|-----|------|
| `vecinita-llm` (prod) | pinned | **Do not** use for sweep reloads |
| `vecinita-llm-playground` | **A100-80GB** (S019-D20) | Eval `model_id` reload — non-AWQ + MoE; prod stays T4 |
| Catalog | `resolve_hf_repo` | Many proposed tags need registry deltas before pull |

**S019-D8 / ADR-009:** prefer self-hosted. Medium/Large may require an explicit waiver or deferral.

## Gates (locked 2026-07-31)

| Gate | Answer | Decision |
|------|--------|----------|
| **A** | R0+P1 + staging + 1.5B control | S019-D16 |
| **B** | Self-host all in order; fail/skip + cost | S019-D17 |
| **C** | Queue T1→L4 approved | S019-D18 |

**Method note:** Synthesis uses the candidate model on playground; **judges stay on**
`qwen2.5:1.5b-instruct` so cross-model relevancy/faith are comparable. Eval runner packing
is still P0 — model sweep uses session script with **P1** until F42 ships packing.

## Execution checklist

- [x] Record S019-D15–D18
- [x] Registry tags for Tiny (T1–T3)
- [x] Run T1 (`g9v3:3b`) — tied with 1.5B control @ relevancy 0.23
- [x] Run T2 (`qwen3:4b-instruct-2507`) — tied @ 0.23
- [x] Run T3 (`minicpm5:1b`) — tied @ 0.23; **Tiny tier complete (all ties)**
- [x] Playground A10 / A100-80 + S1–S3 (all ties @ 0.23)
- [x] Aggregate — **no model lift**; S019-D21 lock 1.5B; M1+ skipped
- [x] Model change **out** of F42 scope (F42 = packing only)

## Artifacts

| Path | Role |
|------|------|
| This file | Plan + queue |
| `model-sweep-tracker.md` | Live status / metrics per model |
| `reports/eval-experiments/*.json` | Raw sweep payloads |
| `scripts/eval_sweep_golden_models.py` | Runner |
| `scripts/eval_setup_playground_model.py` | Pull/warm |
