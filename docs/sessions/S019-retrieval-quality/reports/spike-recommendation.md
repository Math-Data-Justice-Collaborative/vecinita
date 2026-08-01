# EV-016 spike recommendation — F42 scope

> **Session:** S019 · **Cycle:** EV-016 · **Status:** `phase0_approved` — Phase A `01-requirements`  
> **Date:** 2026-08-01  
> **Evidence:** [spike-hybrid-plan.md](./spike-hybrid-plan.md) · `20260801T002819Z_hybrid-sweep.json`

## Winner

**F42 = P1 context packing + thin H7 multi-query fan-out** on `packages/rag` + ChatRAG /
eval prompt assembly (#165 + harness H7).

| Lever | Verdict | Evidence |
|-------|---------|----------|
| #165 packing P1 | **Ship (core)** | Hy0: 0.23 / faith 0.91 |
| H7 fan-out | **Ship (boost)** | Hy1: **0.31** / faith 0.91; en_rel 0.36 |
| R1 cheap rerank | **Out** | Hy3: same 0.31, faith **0.82** |
| P3 dedupe+budget | **Defer as default** | Hy2/Hy4 relevancy ↓ to 0.19; optional hygiene later |
| #158 top_k=8 | **Out / secondary** | HyK8 = Hy0 (0.23) |
| L0 language filter | **Keep prod as-is** | HyLang0: relevancy=Hy0, retrieval 0.91, cross_lang 0 |
| #162 soft filter | **Defer** | A3 + HyLang0 — no relevancy lift |
| R3 CE / model upsizing | **Out** | Prior spikes |
| H1/H9 answer cache | **F43 later** | Cost win; not quality |

## F42 ship scope

1. Shared packer: `Source: {title}\nURL: {url}\n{text}` per chunk (P1)  
2. Thin multi-query fan-out (2–3 rewrites, merge by chunk_id / score) — **no LangGraph**  
3. Spanish-aware rewrite variants for `es` queries  
4. Wire ChatRAG `_build_prompt` + eval sandbox through shared helpers  
5. Optional (non-default): document dedupe + char budget behind config  

**Out of F42:** R1, CE/#83, #162, synthesizer change, LangGraph/ADR-006, answer cache (F43).

## Language metrics (S019-D30)

| Metric | Hy1 (winner) | Notes |
|--------|--------------|-------|
| `answer_lang_match_rate` | **1.00** | EN and ES answers match locale |
| `mean_cross_lang_share` | 0.15 overall | es rows higher under H7 (0.6) — watch |
| en relevancy | **0.36** | Lift vs Hy0 0.27 |
| es relevancy | **0.00** (n=2) | Faith 1.0 + lang_match 1.0; judge/golden gap — follow-on |

## Prereqs

| Item | Status |
|------|--------|
| ISS-008 Admin staging golden fixture | **Code fixed** (not deployed) — `staging` → `qa_pairs_staging.json` |
| ES corpus + golden (S019-D34 A+B) | **Done** — 9 ES docs; ≥6 ES hit rows |
| #159 E1 F36 (S019-D36/D37) | **Done** — E1 rejected for F42 (EN relevancy regression) |
| `phase0_approved` | **Yes** (S019-D37 lock) |
| Playground T4 (S019-D26) | Done |

## Next

1. Phase A `01-requirements` for **F42 = H7+P1** (E0 embed)  
2. Deploy ISS-008 with write-api before Admin promote smoke  
3. F43 cache / further #159 — later cycle  
