# EV-016 harness spike — cache / LangGraph workflows (S019-D23–D28)

> **Session:** S019 · **Cycle:** EV-016 · **Status:** H0-H9 complete  
> **Last updated:** 2026-08-01  
> **Synthesizer lock:** `qwen2.5:1.5b-instruct` (S019-D21)  
> **Fixed RAG cell:** staging golden · R0 · **P1 packing** · top_k=5 · min_score=0.2  
> **Hosting:** playground **T4** (S019-D26 deployed)  
> **ADR-006 path:** spike/eval-only first; **defer amend** until data justifies ship (S019-D27)  
> **Runner:** `scripts/spike_harness_workflows.py`  
> **Artifact:** `eval-experiments/20260801T000138Z_harness-workflows.json`

## Goal

Measure **cost / latency / quality** of caching and **LangGraph workflow schemas**
(intent routing, sub-agents, answer classification) **beside** F36 — without changing
ChatRAG until ADR-006 is amended.

**In:** eval/playground harness scripts + session reports  
**Out until ADR amend:** LangGraph in `apps/chat-rag-backend` or `packages/rag` prod path  
**Parallel ship track:** F42 = P1 packing (S019-D22); ISS-008 still blocks promote smoke

## ADR constraints

| ADR | Constraint for this spike |
|-----|---------------------------|
| **ADR-006** | ChatRAG stays **LlamaIndex**. LangGraph only under `docs/sessions/S019-…/scripts/` (eval). |
| **ADR-004** | No identity-keyed checkpoints; no server chat history. Ephemeral / content-hash keys only. |
| **ADR-037** | Prod pin `qwen2.5:1.5b-instruct`; harness uses playground URL. |

---

## Idea catalog (search, then select)

Brainstormed levers; **✓** = in H0–H9 matrix; **◇** = stretch; **✗** = out / deferred.

### Caching / cost

| Idea | Status | Notes |
|------|--------|-------|
| Embed + retrieval result cache | ✓ H1 | Content-hash / normalize query |
| Exact answer (FAQ) cache | ✓ H1 | Skip LLM on normalized match |
| Semantic answer cache | ✓ H1 | Cosine threshold; false-hit risk |
| Prompt prefix / KV-friendly packing | ✓ H2 | Stable system+context ordering |
| Stacked cheap cascade | ✓ H1/H9 | exact → semantic → retrieve → generate |
| Speculative decode / draft model | ✗ | Needs second model; out of lock |
| Cross-request Modal volume cache | ✗ | Ops complexity; later |

### Intent classification

| Idea | Status | Notes |
|------|--------|-------|
| Coarse intent → route | ✓ H3/H8/H9 | Labels below |
| Language intent (en/es answer) | ◇ | Overlaps ADR-013; optional node later |
| Unsafe / off-corpus refuse early | ✓ H3 | Branch before retrieve |
| Greeting / chitchat short-circuit | ✓ H3 | No retrieve |
| Query rewrite before retrieve | ◇ H7-adjacent | Fold into multi-query |
| Slot-fill / clarify missing entity | ✓ H8 | Answer-class `clarify` |

**Intent label set (v1 harness):**  
`faq_lookup` · `corpus_qa` · `chitchat` · `out_of_scope` · `unsafe` · `clarify_needed`

### Answer classification

| Idea | Status | Notes |
|------|--------|-------|
| Post-synth grader (grounded?) | ✓ H4/H8 | Accept / retry / refuse |
| Citation sufficiency check | ✓ H6 | Critic sub-agent |
| Refuse when empty retrieve | ✓ H4 | No hallucinated fill |
| Confidence / abstain threshold | ✓ H4 | Score → branch |
| Bilingual answer-quality grade | ✗ | Judge cost; later |
| User-facing tone class | ✗ | Product polish; out |

**Answer label set (v1 harness):**  
`grounded` · `weak_grounding` · `refuse` · `clarify` · `retry_retrieve`

### Sub-agents / multi-node

| Idea | Status | Notes |
|------|--------|-------|
| Retriever agent + synthesizer agent | ✓ H5 | Sequential handoff |
| + Critic / citation agent | ✓ H6 | Optional one retry |
| Supervisor router over agents | ✓ H6 | Thin supervisor node |
| Parallel multi-query retrieve | ✓ H7 | Fan-out / fan-in |
| Map-reduce over top chunks | ◇ | Extra LLM calls; stretch |
| Tool-calling ReAct loop | ✗ | Overfit for v1 FAQ RAG |
| Human-in-the-loop interrupt | ✗ | Conflicts ADR-004 ops model |
| Persistent checkpointer (thread_id) | ✗ | ADR-004 hard no |

### Graph topology / schema variants

| Schema id | Shape | Used by |
|-----------|-------|---------|
| **S0** | No graph (LlamaIndex baseline) | H0 |
| **S1 CacheRouter** | lookup → hit\|miss→retrieve→synth→store | H1 |
| **S2 PrefixPack** | pack-for-prefix-cache → synth (linear) | H2 |
| **S3 IntentRouter** | classify → branch (faq\|rag\|chitchat\|refuse\|clarify) | H3, H9 |
| **S4 GradeLoop** | retrieve → synth → grade → accept\|retry\|refuse | H4 |
| **S5 DualAgent** | retriever_agent → synthesizer_agent | H5 |
| **S6 TriadAgent** | supervisor → retrieve \| synth \| critic (+1 loop) | H6 |
| **S7 FanOut** | rewrite×N → parallel retrieve → merge → synth | H7 |
| **S8 IntentGrade** | intent → (rag path) → answer_class → emit | H8 |

---

## Config matrix (10 cells: H0–H9)

Shared factors unless noted: staging golden · R0 · P1 · top_k=5 · min_score=0.2 ·
synth=`qwen2.5:1.5b-instruct`.

Metrics: F36 retrieval / faith / relevancy · p50/p95 latency · approx $/row ·
cache hit % · intent accuracy (where labeled) · answer-class distribution · retry count.

| ID | Name | Schema | What it tests |
|----|------|--------|----------------|
| **H0** | Baseline | **S0** | LlamaIndex + P1 + 1.5B control |
| **H1** | Cache cascade | **S1** | Exact → semantic answer → embed/retrieve cache → generate |
| **H2** | Prefix / KV pack | **S2** | Stable prefix packing; TTFT / p95 vs H0 |
| **H3** | Intent router | **S3** | Intent classify → faq cache / rag / chitchat / refuse / clarify |
| **H4** | Answer grade loop | **S4** | Synth → answer class → accept / retry retrieve once / refuse |
| **H5** | Dual sub-agents | **S5** | RetrieverAgent → SynthesizerAgent (typed state handoff) |
| **H6** | Triad + critic | **S6** | Supervisor + retrieve + synth + critic (max 1 critique loop) |
| **H7** | Multi-query fan-out | **S7** | 2–3 query rewrites → parallel retrieve → merge → synth |
| **H8** | Intent + answer class | **S8** | Intent route then post-answer classification (no critic LLM if heuristic grade OK) |
| **H9** | Intent + cache stack | **S3+S1** | Intent router in front of H1 cascade (max skip-LLM + early refuse) |

### LangGraph state schemas (eval stubs)

Distinct `TypedDict` / pydantic states per schema — do **not** reuse one mega-state for all cells.

```text
S1 CacheRouterState
  query, norm_query, cache_hit: none|exact|semantic|retrieve,
  chunks[], answer?, sources[], metrics{}

S3 IntentRouterState
  query, intent, intent_confidence,
  route: faq|rag|chitchat|refuse|clarify,
  chunks[], answer?, sources[]

S4 GradeLoopState
  query, chunks[], draft_answer?,
  answer_class, retries: int, final_answer?, sources[]

S5 DualAgentState
  query, retrieve_notes, chunks[], synth_answer?, sources[]

S6 TriadAgentState
  query, supervisor_plan,
  chunks[], draft?, critique?, answer_class, loops, final?, sources[]

S7 FanOutState
  query, rewrites[], per_rewrite_chunks[][], merged[], answer?, sources[]

S8 IntentGradeState
  query, intent, route, chunks[], draft?, answer_class, final?, sources[]
```

Checkpointer: **MemorySaver** (process-local) or none — never Postgres/Redis keyed by user.

---

## Hypotheses

1. **H1/H9** win on $/row when enough FAQ / repeat traffic; watch false semantic hits (faith).
2. **H3** helps out-of-scope / chitchat (fewer bad retrieves); may not lift golden relevancy if golden is all `corpus_qa`.
3. **H4/H8** can raise **faith** by refusing weak grounding; relevancy may fall if over-refuse.
4. **H5** ≈ H0 quality if agents only wrap the same retrieve+synth — latency likely worse (sanity / wiring cell).
5. **H6** may lift faith via critic; cost ↑ (extra LLM calls); stop if no faith gain ≥ noise.
6. **H7** may lift retrieval/relevancy on hard rows; cost ↑; compare vs packing-only F42.
7. **H2** is latency-only; quality ≈ H0.
8. If **no graph cell beats H0+H1** on quality or cost, **keep ADR-006** (LlamaIndex) and ship caches without LangGraph.

---

## Method

1. Scripts under `docs/sessions/S019-retrieval-quality/scripts/` (e.g. `spike_harness_workflows.py`) — **not** ChatRAG prod.
2. One schema module per **S1–S8** (small graphs); shared retrieve/P1 pack helpers.
3. Intent / answer classifiers: start **heuristic + small LLM JSON** (1.5B); log confusion vs hand labels on a 20-row subsample if cheap.
4. Cache seeds for H1/H9: (a) cold (b) warm golden pass (c) optional FAQ file.
5. Run H0 first; then H1–H9; artifact `spike-harness-cache.json` (+ per-cell summaries in this MD).
6. Rank by (relevancy, faith, p95, $/row); recommend ship / reject / ADR-006 amend or not.

## Success / stop

| Outcome | Action |
|---------|--------|
| Clear cost win (H1/H9) quality ≥ H0 | Propose cache Fn (F43?) **without** LangGraph |
| Clear quality win (H4/H6/H7/H8) | Propose workflow Fn + **then** draft ADR-006 amend |
| Graph cells ≈ H0 with higher $ | Keep LlamaIndex; drop LangGraph ship intent |
| F42 packing | Independent — do not block |

## Implementation note

Workflows are **TypedDict state machines** isomorphic to planned LangGraph schemas
(S0-S8). The `langgraph` PyPI package is **not** added until ADR-006 amend — avoids
prod dep drift while still testing distinct schemas/routes (S019-D27/D28).

## Checklist

- [x] Plan + idea catalog + **10-config** matrix (H0-H9)
- [x] ADR-006 path = spike first, defer amend (S019-D27)
- [x] Runner script `spike_harness_workflows.py` (H0-H9)
- [x] Playground redeploy **T4** (S019-D26) — deployed 2026-07-31
- [x] H0 control + H1-H9 cells + artifacts
- [x] First-pass ranking (below)

## Results (20260801T000138Z)

| Cell | Schema | retrieval | faith | relevancy | p95_ms | llm/row | cache_hit |
|------|--------|-----------|-------|-----------|--------|---------|-----------|
| **H0** | S0 | 1.00 | 0.91 | 0.23 | 2302 | 1.00 | 0.00 |
| **H1** | S1 | 1.00 | 0.91 | 0.23 | ~0 | 0.00 | **1.00** |
| **H2** | S2 | 1.00 | 0.82 | **0.00** | 2697 | 1.00 | 0.00 |
| **H3** | S3 | 0.91 | **1.00** | 0.23 | 2341 | 0.92 | 0.00 |
| **H4** | S4 | 1.00 | 0.91 | 0.23 | 2321 | 1.00 | 0.00 |
| **H5** | S5 | 1.00 | 0.91 | 0.23 | 2332 | 1.00 | 0.00 |
| **H6** | S6 | 1.00 | 0.91 | 0.23 | 2326 | 1.00 | 0.00 |
| **H7** | S7 | 1.00 | 0.91 | **0.31** | 2658 | 1.00 | 0.00 |
| **H8** | S8 | 0.91 | **1.00** | 0.23 | 2380 | 0.92 | 0.00 |
| **H9** | S3+S1 | 0.91 | **1.00** | 0.23 | ~0 | 0.00 | 0.92 |

### Ranking lean

1. **Quality:** **H7 multi-query fan-out** only cell to lift relevancy (0.23 → **0.31**); faith holds.
2. **Cost:** **H1 / H9** after warm-pass → skip LLM (cache_hit ≈ 1); quality = H0. Strong F43 cost candidate **without** LangGraph.
3. **Faith hygiene:** H3/H8 intent(+grade) → faith 1.0 but retrieval 0.91 (edge rows short-circuit).
4. **Reject:** **H2** prefix-stable pack (relevancy collapsed to 0).
5. **Neutral:** H4/H5/H6 ≈ H0 (graph wiring / grade loop no lift on this golden).
6. **ADR-006:** Do **not** amend yet — only H7 wants a workflow; can be a thin fan-out helper without full LangGraph. Revisit if multi-turn / supervisor needed.

## Artifacts

| Path | Role |
|------|------|
| This file | Plan + catalog + matrix + results |
| `eval-experiments/20260801T000138Z_harness-workflows.json` | Raw metrics |
| `scripts/spike_harness_workflows.py` | Runner |
| `spike-recommendation.md` | F42 packing draft |
| `model-sweep-tracker.md` | Sweep closed (S019-D21) |
