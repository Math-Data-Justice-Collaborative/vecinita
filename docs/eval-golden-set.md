# Golden evaluation set — curation runbook

> **Feature:** F36 (EV-008 / S007 / GitHub #99)  
> **CI fixture:** `data/fixtures/eval/qa_pairs.json` (`fixture://` URLs)  
> **Staging fixture:** `data/fixtures/eval/qa_pairs_staging.json` (live `https://` URLs)  
> **Last updated:** 2026-07-24

## Purpose

The golden set is the **regression benchmark** for Vecinita RAG quality. It drives:
- CI harness (`tests/eval/`) — retrieval + answer-quality metrics against a **seeded fixture corpus**
- Admin **Evaluation** tab — on-demand runs and history (F36)
- Staging / Modal playground sweeps — live corpus URLs via `qa_pairs_staging.json`
- Coordination with #83 (reranking) and #84 (groundedness)

## Two fixtures (do not mix)

| File | URLs | Used by |
|------|------|---------|
| `qa_pairs.json` | `fixture://corpus/...` | `tests/eval/`, default `load_golden_rows()` |
| `qa_pairs_staging.json` | live `https://` docs in DO Postgres | `eval_sweep_golden_models.py` default; staging `prod.env` runs |

CI seeds local Postgres from `data/fixtures/corpus/`. Staging sweeps read Managed Postgres
where documents use real site URLs. Keep both files in sync on **edge** cases
(`edge-abstain-mayor-phone`, `edge-empty-quantum`); domain hit rows differ by corpus.

## Fixture schema

Each row is one locale variant of an eval case (`id` groups bilingual pairs).

| Field | Required | Description |
|-------|----------|-------------|
| `id` | Yes | Stable case id (e.g. `community-food-pantry`) |
| `locale` | Yes | `en` or `es` |
| `domain` | Yes | `community`, `housing`, `legal`, or `edge` |
| `question` | Yes | User phrasing (no production PII) |
| `expected_doc_url` | For `hit` | Single doc URL that must appear in top-k |
| `expected_doc_urls` | For `any_of` | Any listed URL in top-k passes retrieval |
| `retrieval_expectation` | Yes | `hit` \| `any_of` \| `abstain` \| `empty` |
| `required_facts` | Yes | Bullets the answer must satisfy for faithfulness / answer relevancy |

**Retrieval aggregate (≥80%):** Computed over rows with `retrieval_expectation` of `hit` or `any_of` only
(CI fixture: 11 scored rows). Edge `abstain` / `empty` rows use separate assertions (TC-113).

## Staging live-URL coverage (2026-07-24)

`qa_pairs_staging.json` — **real `https://` corpus URLs only** (no `fixture://`). Used by
playground / staging sweeps (`scripts/eval_sweep_golden_models.py`).

| Domain | Cases | Locales | Notes |
|--------|-------|---------|-------|
| Community | 5 | en + es (2 paired) | Free clinic, Nuevas Voces, resilience hub, VECINA intro |
| Housing | 1 | en only | Flood insurance wait (`health.ri.gov/flooding`) |
| Legal aid | 2 | en only | RILS mission + safe affordable housing priority |
| Edge | 3 | en | Abstain (mayor phone), ambiguous `housing`, empty quantum |

**Total:** 11 cases, 13 locale rows.

## How to add or change an example

1. **Pick domain** — must map to a real corpus document (or intentional edge case).
2. **Draft question** — realistic community phrasing; get product sign-off for en and es pairs.
3. **Set expected source(s)** — for staging sweeps, live `https://` URLs already in the target DB;
   for local fixture tests, `fixture://` URLs under `data/fixtures/corpus/`.
4. **List `required_facts`** — short bullets grounded in the source doc; no invented PII.
5. **Update fixture** — append/edit `qa_pairs.json`; keep `id` stable when editing wording.
6. **Run harness locally** — `uv run pytest tests/eval -m integration` (Postgres required).
7. **Record baseline** — after a staging eval run, note scores in the admin tab or session report.

## Model / parameter sweep (sample CLI)

End-to-end experiment loop (see skill `eval-golden-sweep`):

```text
[optional] list/ensure models -> example generation -> evaluate/sweep -> save JSON -> load -> aggregate -> agent
```

| Step | Script |
|------|--------|
| List models | `scripts/eval_list_playground_models.py` (`GET /models/ollama` alias) |
| Ensure / warm model | `scripts/eval_setup_playground_model.py --model <tag>` |
| Create examples | `scripts/eval_create_golden_examples.py` |
| Sweep + save | `scripts/eval_sweep_golden_models.py` → `data/eval-experiments/*.json` |
| Aggregate | `scripts/eval_aggregate_experiments.py` |

```bash
# Discover staged tags (prefer VECINITA_MODAL_LLM_PLAYGROUND_URL)
set -a && source prod.env && set +a
unset VECINITA_MODAL_OLLAMA_URL
uv run python scripts/eval_list_playground_models.py --json

# Stage + warm a model before sweeping
uv run python scripts/eval_setup_playground_model.py --model qwen3:8b

# Inspect the grid without LLM/DB calls
uv run python scripts/eval_sweep_golden_models.py \
  --models qwen2.5:1.5b-instruct,qwen3:8b \
  --temperatures 0.0,0.2 \
  --system-prompt-dir data/fixtures/eval/prompts \
  --top-k 3,5 \
  --dry-run

# Live multi-run sweep (staging env; read-only corpus)
uv run python scripts/eval_sweep_golden_models.py \
  --models qwen2.5:1.5b-instruct,qwen3:8b \
  --temperatures 0.0,0.2 \
  --runs 3 \
  --system-prompt-dir data/fixtures/eval/prompts \
  --rules-file data/fixtures/eval/sample_rules.json \
  --extra-fixture data/fixtures/eval/similar_examples.json \
  --results-dir data/eval-experiments \
  --limit 4

# Aggregate saved experiments for agent review
uv run python scripts/eval_aggregate_experiments.py \
  --results-dir data/eval-experiments \
  --group-by model_id,prompt_name,temperature \
  --metrics retrieval_relevance,faithfulness,wall_time_s,spawn_wall_time_s
```

Sweep knobs map to `EvalConfig` plus **prompt variants** (`--system-prompt-dir` /
`--system-prompt-files`). Each live run writes an experiment JSON with per-cell
`config` (params + `model_type` + `prompt_name` + `system_prompt` + `rules`),
`spawn_wall_time_s`, per-run `runs[]`, and `averages`. Paraphrase extras live in
`data/fixtures/eval/similar_examples.json` (same schema as `qa_pairs.json`).

## Privacy (ADR-004)

- No real resident names, addresses, phone numbers, or case details.
- Use synthetic or public-corpus-only scenarios.
- Eval run persistence stores **question text from the fixture only** — not live operator or visitor prompts.

## Bilingual policy

- Community rows: **paired en/es** with locale-appropriate corpus URLs.
- Housing/legal: **en-only in v1** until Spanish corpus documents land (#94). Do not add es rows that expect en doc URLs without an explicit interview decision.

## Judge guidelines (LlamaIndex evaluators)

- Judge LLM uses the **same Modal self-hosted HTTP LLM** as ChatRAG.
- Evaluator prompts evaluate in the **query language** (en question → en rubric; es → es).
- Faithfulness: answer must be supported by retrieved context and include `required_facts` where applicable.
- Answer relevancy: answer must address the question without unrelated filler.
- When #84 groundedness lands, the eval tab should surface the **same groundedness signal** — do not maintain a duplicate verifier.

## Related specs

- Thresholds: `docs/acceptance-criteria.md` (AC-E12–AC-E16)
- API: `docs/api-contract.md` §EV-008 eval routes
- Config: `docs/config-spec.md` §RAG evaluation (F36)
- Implementation: `docs/adr/ADR-033-ev008-rag-evaluation-implementation.md`
