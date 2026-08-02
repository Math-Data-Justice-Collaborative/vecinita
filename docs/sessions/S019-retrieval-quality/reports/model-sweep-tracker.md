# EV-016 model sweep — experiment tracker

> **Session:** S019 · **Cycle:** EV-016 · **Plan:** `model-sweep-plan.md`  
> **Status:** **closed** — S019-D21 lock `qwen2.5:1.5b-instruct`; M1+ skipped  
> **Last updated:** 2026-07-31  
> **Fixed cell:** staging · R0 · P1 · judge=`qwen2.5:1.5b-instruct`  
> **Playground GPU:** reverting to **T4** (S019-D26); prior A100-80 was sweep-only

## Control (always re-run or cite)

| Model | Tag | retrieval | faith | relevancy | p95_ms | Artifact | Notes |
|-------|-----|-----------|-------|-----------|--------|----------|-------|
| Qwen2.5 1.5B Instruct (prod pin) | `qwen2.5:1.5b-instruct` | 1.00 | 0.91 | **0.23** | 4766 | `20260731T220620Z_model-sweep.json` | Same-run control under R0+P1 |

## Queue status

| Order | ID | Model | Tag | Tier | Status | retrieval | faith | relevancy | p95_ms | Modal cost note | Artifact |
|------:|----|-------|-----|------|--------|-----------|-------|-----------|--------|-----------------|----------|
| 1 | T1 | AI9Stars G9v3-3B | `g9v3:3b` | Tiny | `complete` | 1.00 | 0.91 | **0.23** | 4851 | Tied with control | `20260731T220620Z_model-sweep.json` |
| 2 | T2 | Qwen3 4B 2507 | `qwen3:4b-instruct-2507` | Tiny | `complete` | 1.00 | 0.91 | **0.23** | 5511 | Tied with control | `20260731T221520Z_model-sweep.json` |
| 3 | T3 | OpenBMB MiniCPM5-1B | `minicpm5:1b` | Tiny | `complete` | 1.00 | 0.91 | **0.23** | 5489 | Tied with control | `20260731T221748Z_model-sweep.json` |
| 4 | S1 | Qwen3.6 27B (fp16 T4) | `qwen3.6:27b` | Small | `complete_caveat_invalid` | 1.00 | 0.91 | **0.23** | 5960 | Invalid — T4 | `20260731T222642Z_model-sweep.json` |
| 4b | S1 | Qwen3.6 27B AWQ | `qwen3.6:27b-awq` | Small | `complete` | 1.00 | 0.91 | **0.23** | 4440 | A10 AWQ; **tie** | `20260731T224759Z_model-sweep.json` |
| 4c | S1 | Qwen3.6 27B fp16 | `qwen3.6:27b` | Small | `complete` | 1.00 | 0.91 | **0.23** | 5915 | A100-80 non-AWQ warm OK; **tie** | `20260731T230525Z_model-sweep.json` |
| 5 | S2 | Qwen3.5 27B AWQ | `qwen3.5:27b-awq` | Small | `complete` | 1.00 | 0.91 | **0.23** | 4818 | A10 AWQ; **tie** | `20260731T225612Z_model-sweep.json` |
| 6 | S3 | Qwen3.6 35B A3B FP8 | `qwen3.6:35b-a3b-fp8` | Small | `complete` | 1.00 | 0.91 | **0.23** | 5496 | A100-80 official FP8; warm OK; **tie** | `20260731T230854Z_model-sweep.json` |
| 7 | M1 | Qwen3.5 122B A10B | `qwen3.5:122b-a10b` | Medium | `skipped` | | | | | S019-D21 stop | |
| 8 | M2 | Mistral Medium 3.5 | TBD | Medium | `skipped` | | | | | S019-D21 stop | |
| 9 | M3 | NVIDIA Nemotron 3 Super | TBD | Medium | `skipped` | | | | | S019-D21 stop | |
| 10 | L1 | Kimi K3 (max) | TBD | Large | `skipped` | | | | | S019-D21 stop | |
| 11 | L2 | GLM-5.2 (max) | TBD | Large | `skipped` | | | | | S019-D21 stop | |
| 12 | L3 | DeepSeek V4 Flash 0731 (max) | TBD | Large | `skipped` | | | | | S019-D21 stop | |
| 13 | L4 | Kimi K3 (low) | TBD | Large | `skipped` | | | | | S019-D21 stop | |

Status values: `queued` · `pulling` · `running` · `complete` · `failed` · `skipped` · `blocked_gpu` · `blocked_hosting` · `blocked_registry`

## Run log

| When (UTC) | Action | Detail |
|------------|--------|--------|
| 2026-07-31 | Setup | Plan + tracker; gates A1/B4/C1 → S019-D16–D18 |
| 2026-07-31 | Registry | Tiny tags `g9v3:3b`, `qwen3:4b-instruct-2507`, `minicpm5:1b` |
| 2026-07-31 | Infra | Playground redeploy; volume list reload fix; manifest race workaround |
| 2026-07-31T22:06Z | T1 complete | G9v3-3B = control on relevancy/faith (0.23 / 0.91) |
| 2026-07-31T22:15Z | T2 complete | Qwen3-4B-Instruct-2507 = control (0.23 / 0.91) |
| 2026-07-31T22:17Z | T3 complete | MiniCPM5-1B = control (0.23 / 0.91); **Tiny tier done** |
| 2026-07-31T22:26Z | S1 complete* | Qwen3.6-27B reported same 0.23; *caveat: T4 VRAM vs ~56GB weights |
| 2026-07-31 | S019-D19 | Playground GPU → **A10**; S1 re-verify via `qwen3.6:27b-awq` → QuantTrio AWQ; prior S1 invalidated |
| 2026-07-31T22:47Z | S1 AWQ complete | QuantTrio Qwen3.6-27B-AWQ on A10; warm+sweep OK; relevancy **0.23** (tie) |
| 2026-07-31T22:56Z | S2 AWQ complete | QuantTrio Qwen3.5-27B-AWQ on A10; relevancy **0.23** (tie again) |
| 2026-07-31 | S019-D20 | Playground → **A100-80GB** for non-AWQ / larger MoE |
| 2026-07-31T23:05Z | S1 fp16 complete | `qwen3.6:27b` on A100-80; relevancy **0.23** (tie) |
| 2026-07-31T23:08Z | S3 FP8 complete | `Qwen3.6-35B-A3B-FP8` on A100-80; relevancy **0.23** (tie) |
| 2026-07-31 | S019-D21 | **Sweep closed** — keep 1.5B; skip M1+ (quality-neutral) |
| 2026-07-31 | S019-D26 | Playground GPU → **T4** (cost) |

## Recommendation (closed)

**No synthesizer change.** Every measured model tied control at relevancy **0.23** / faith **0.91**.
Keep prod pin `qwen2.5:1.5b-instruct`. Next quality levers: **F42 P1 packing** + harness
cache configs (`spike-harness-cache.md`), not larger LLMs.

## Aggregate

| Rank | Model | relevancy | faith | vs 1.5B control |
|------|-------|-----------|-------|-----------------|
| 1 (tie) | `qwen2.5:1.5b-instruct` | 0.23 | 0.91 | — |
| 1 (tie) | `g9v3:3b` | 0.23 | 0.91 | 0 |
| 1 (tie) | `qwen3:4b-instruct-2507` | 0.23 | 0.91 | 0 |
| 1 (tie) | `minicpm5:1b` | 0.23 | 0.91 | 0 |
| — | `qwen3.6:27b` (T4 fp16) | 0.23 | 0.91 | invalid (T4) |
| 1 (tie) | `qwen3.6:27b-awq` (A10) | 0.23 | 0.91 | 0 |
| 1 (tie) | `qwen3.5:27b-awq` (A10) | 0.23 | 0.91 | 0 |
| 1 (tie) | `qwen3.6:27b` fp16 (A100-80) | 0.23 | 0.91 | 0 |
| 1 (tie) | `qwen3.6:35b-a3b-fp8` (A100-80) | 0.23 | 0.91 | 0 |
