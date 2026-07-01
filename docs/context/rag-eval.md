# Scoped context — RAG evaluation tab + golden set (GitHub #99)

**Session:** S007-rag-eval  
**Stage:** 00-context (scoped delta)  
**Date:** 2026-07-01  
**Feature ID:** **F36** (issue #99 incorrectly proposed F34; F34 = Supabase admin auth)  
**Evolve cycle:** EV-008 (proposed)

---

## Executive summary

[GitHub #99](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/99) requests an
**admin-only Model / RAG Evaluation** tab, a maintained bilingual golden eval set, and a backend
runner that scores retrieval + answer-quality metrics with run history. Vecinita today has only a
**3-pair smoke fixture** and a single pytest benchmark (`tests/eval/test_eval_retrieval_relevance.py`)
that checks **≥80% retrieval relevance** via expected document URL match — no answer metrics, no UI,
no persisted run history.

**Tooling decision (R63):** Hybrid — **LlamaIndex native evaluators** + extend `tests/eval` +
**Postgres results table** + **admin tab** (no new eval observability platform for v1).

**Golden content (R67):** Evaluation **prompts** (golden questions), **expected results**
(sources, key facts, reference answers), and **judge prompt guidelines** are **not invented in
00-context** — they are created through a structured **user interview** in **01-requirements**
(and refined before build in 04-tech-plan if needed). See §Interview-driven eval curation.

---

## Current state (repo evidence)

| Area | Today | Gap for #99 |
|------|-------|-------------|
| Golden set | `data/fixtures/eval/qa_pairs.json` — 3 en/es pairs, `question` + `expected_doc_url` only | Expand domains; add reference answers / key facts |
| Harness | `tests/eval/test_eval_retrieval_relevance.py` — URL-in-top-k, 80% threshold | Full RAG pipeline, faithfulness, answer relevancy, latency |
| Admin UI | Nav: dashboard, corpus, jobs, health, audit, users (`AdminLayout.tsx`) | New `/evaluation` route + i18n |
| Admin API | `internal-write-api` — health, jobs proxy, audit, stats patterns | Trigger eval run, list runs, per-question drill-down |
| Groundedness | Not in `packages/rag` yet | Coordinate with #84 — reuse signal, don't duplicate |
| Feature registry | F14 seed/eval fixtures (implemented); no F36 row yet | Add via 16-evolve / 01-requirements |

### Eval fixture shape (today)

```json
{
  "question": "When are food pantry hours updated?",
  "expected_doc_url": "fixture://corpus/en/community-resources.md"
}
```

### Acceptance benchmark (standing)

From `docs/acceptance-criteria.md`: retrieval quality ≥80% "relevant" on eval fixture (`data/fixtures/eval/`).

---

## Multi-app topology (connectivity)

| Consumer | API | Auth | Notes |
|----------|-----|------|-------|
| `data-management-frontend` | `internal-write-api` (DO) | Supabase JWT (`admin`/`viewer`) | Admin-only; no public eval UI |
| Eval runner (new) | `packages/rag` + Modal LLM + Postgres corpus | Service / admin-triggered job | Runs golden set through same path as ChatRAG |
| ChatRAG (production) | `chat-rag-backend` | Anonymous | Eval does **not** log visitor prompts to new tables with PII |

**Browser integration risk:** Low — same-origin admin SPA → internal-write-api pattern already used for jobs/health/audit.

---

## Eval framework provider re-evaluation

Issue #99 lists five options. Expanded comparison against Vecinita constraints
(≤$50/mo cap, self-hosted Modal LLM, no PII off-device, existing LlamaIndex 0.13.x stack):

| Option | Role | New deps / infra | Fits Vecinita v1? | Verdict |
|--------|------|------------------|-------------------|---------|
| **LlamaIndex native evaluators** | Faithfulness, answer/context relevancy, batch runner; uses existing `llama-index` | None (already pinned) | **Yes** — judge LLM can be Modal Qwen2.5-1.5B | **Selected (R63)** |
| **Custom harness** | Retrieval URL match (existing), latency, Postgres persistence, admin UI | None | **Yes** | **Selected (R63)** |
| **Ragas** | Research-backed RAG metrics (faithfulness, context precision/recall) | `ragas` + judge LLM calls | Partial — adds dep; metrics overlap LlamaIndex | Defer; revisit if LlamaIndex judges prove weak |
| **DeepEval** | Pytest-native thresholds, CI gates | `deepeval` (+ optional Confident AI cloud) | Partial — good for CI, overlaps LlamaIndex | Optional later for stricter CI assertions |
| **Langfuse** | Datasets, traces, eval UI (self-host: Postgres+ClickHouse+Redis+S3) | Heavy ops; MIT core | **Poor** for cost/ops cap | Defer — admin tab is the UI |
| **Arize Phoenix** | OTel traces + eval UI (single Docker; ELv2) | `arize-phoenix` stack | Partial — useful if production trace volume grows | Defer to post-v1 observability |
| **promptfoo** | Prompt/model regression matrices | Node CLI | Low priority — not RAG-metric focused | Out of scope v1 |
| **Hybrid Ragas + DeepEval** | Experiments + CI gate | Two Python deps | Overlap with LlamaIndex | Not selected v1 |

### Why LlamaIndex + custom (not Langfuse/Ragas) for v1

1. **Zero new runtime dependency** — `llama-index` already orchestrates RAG ([dependency-inventory.md](../dependency-inventory.md) RD-023).
2. **Judge LLM stays on Modal** — `FaithfulnessEvaluator` / `AnswerRelevancyEvaluator` can use the same self-hosted HTTP LLM as ChatRAG ([LlamaIndex eval docs](https://developers.llamaindex.ai/python/framework/module_guides/evaluating/)).
3. **Cost cap** — Langfuse/Phoenix self-host adds always-on services; LLM-as-judge on every golden row × 4 metrics adds Modal GPU time (budget in 04-tech-plan).
4. **Admin UI is the product goal** — #99 wants eval in `data-management-frontend`, not a second observability dashboard.
5. **CI parity** — extend existing `tests/eval/` rather than introduce `deepeval test run` parallel harness.

### Metrics map (proposed F36)

| Metric | v1 implementation | LLM judge? |
|--------|-------------------|------------|
| Retrieval relevance | Expected doc URL in top-k (existing) + optional context relevancy | Optional (LlamaIndex `ContextRelevancyEvaluator`) |
| Groundedness / faithfulness | LlamaIndex `FaithfulnessEvaluator` **or** #84 verifier if landed first | Yes (Modal LLM) |
| Answer relevance | LlamaIndex `AnswerRelevancyEvaluator` | Yes |
| Latency | Wall-clock per golden question through RAG pipeline | No |

Align groundedness with [#84](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/84) when available — eval tab surfaces the same signal.

---

## Interview-driven eval curation (planned — 01-requirements)

The golden eval set and judge prompts are **domain knowledge**, not code artifacts. They must be
authored with the product owner through interview, not guessed from the 3-pair smoke fixture.

### What the interview produces

| Artifact | Location (planned) | Interview topics |
|----------|-------------------|------------------|
| **Golden questions** | `data/fixtures/eval/qa_pairs.json` (expand) | Bilingual (en/es); domains (housing, legal aid, community resources, …); realistic user phrasing |
| **Expected sources** | Same fixture — `expected_doc_url` or doc IDs | Which corpus doc(s) must appear in retrieval for each question |
| **Reference answers / key facts** | Same fixture — `reference_answer` and/or `required_facts[]` | Groundedness and answer-relevance scoring without production PII |
| **Pass thresholds** | `docs/acceptance-criteria.md`, `docs/test-plan.md` | Per-metric floors (e.g. retrieval ≥80% retained; faithfulness ≥X%) |
| **Judge prompt guidelines** | `docs/config-spec.md` or eval module config | Domain tone, bilingual expectations, “must cite sources” rules for LlamaIndex evaluators |
| **Baseline run snapshot** | Session report + optional committed fixture | First interview-approved run scores as regression baseline |

### Interview phases (01-requirements)

1. **Domain & coverage** — Which corpus topics must the golden set represent? Minimum count per language?
2. **Question drafting** — Walk through candidate questions; user approves/edits en + es pairs.
3. **Expected retrieval** — For each question, which document(s) are the correct sources in the current corpus?
4. **Answer rubric** — Reference answer or bullet key facts; what counts as pass vs fail for groundedness?
5. **Metric thresholds** — Acceptable scores for CI gate vs admin “informational” display.
6. **Privacy check** — No real resident PII; synthetic or public-corpus-only examples (ADR-004).

Outputs land in standing docs (`feature-list` F36, `user-journeys` UJ-NNN, `test-plan` TC-NNN,
`acceptance-criteria`) and the expanded `qa_pairs.json` **after** interview sign-off — not before.

### What stays out of interview (engineering)

- Postgres schema, API routes, admin UI layout → **04-tech-plan**
- LlamaIndex evaluator wiring, Modal judge client → **07-build**
- Harness pytest + admin e2e → **07-build** / **10-e2e** (using interview-approved fixtures)

See session plan: `docs/sessions/S007-rag-eval/reports/eval-curation-plan.md`.

---

## Resolution log (session S007)

| ID | Category | Resolution |
|----|----------|------------|
| R63 | Decision | **Eval tooling:** LlamaIndex native evaluators + custom harness/Postgres/admin UI (no Ragas/DeepEval/Langfuse v1) |
| R64 | Contradiction | Issue #99 proposes **F34** — already **Supabase admin auth**. Use **F36** for RAG evaluation. |
| R65 | Decision | **Session:** Park S006; open S007-rag-eval on `feat/S007-rag-eval` |
| R66 | Decision | **Routing:** evolve-lite — 00→01→04→07→08→09→10→12→13 (skip 02,03,05,06,11) |
| R67 | Decision | **Golden eval content:** prompts, expected results, and judge guidelines created via **01-requirements user interview** — not assumed in 00-context |

---

## Dependencies & blockers

| Item | Status | Notes |
|------|--------|-------|
| Tooling ADR | Pending | Record R63 in `docs/adr/` during 04-tech-plan |
| #84 groundedness | Open | Coordinate metric; don't duplicate verifier |
| #83 reranking | Open | Primary consumer of golden eval regressions |
| #94 corpus curation | Open | Richer corpus → more meaningful golden set |
| Modal LLM | Available | Required for LLM-as-judge metrics |
| F35/F36 feature-list | Pending | 01-requirements delta |

---

## Unresolved gaps (downstream)

**Resolved in 01-requirements via interview (R67):**

1. ~~Golden set size target and curation owners~~ → interview §Domain & coverage
2. ~~Reference answers / key facts per question~~ → interview §Answer rubric
3. ~~Pass thresholds per metric~~ → interview §Metric thresholds
4. ~~Judge prompt domain guidelines~~ → interview §Judge guidelines

**Still engineering (04-tech-plan / 07-build):**

1. Postgres schema for `eval_runs` / `eval_run_items`
2. Whether viewers can **read** eval results or admin-only trigger (01 may decide policy)
3. Staging vs production corpus for eval runs
4. LLM judge cost estimate per run (N questions × metrics × Modal $)

---

## References

- [Issue #99](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/99)
- `tests/eval/test_eval_retrieval_relevance.py`
- `data/fixtures/eval/qa_pairs.json`
- [LlamaIndex evaluating](https://developers.llamaindex.ai/python/framework/module_guides/evaluating/)
- [AgentsCamp eval tools 2026](https://agentscamp.com/guides/evaluation/best-llm-eval-tools-2026)
- [DeepEval vs Ragas 2026](https://qaskills.sh/blog/deepeval-vs-ragas-rag-evaluation-2026)
