---
name: eval-golden-sweep
description: >
  Orchestrates Vecinita golden-set eval experiments — playground model list/setup,
  example generation, multi-model/multi-prompt sweeps, JSON experiment saves, folder
  load/aggregate, and agent presentation. Use when the user asks to create golden
  examples, list or stage LLM models, run eval sweeps, compare models/prompts/parameters,
  aggregate experiment JSONs, or present eval results for agent analysis.
---

# Eval golden sweep pipeline

End-to-end process:

```text
[optional setup] list/ensure models -> example generation -> evaluate/sweep -> save JSON -> load -> aggregate -> agent
```

## Scripts

| Step | When to run | Command |
|------|-------------|---------|
| 0a. List models | User asks what models are available / before choosing `--models` | `uv run python scripts/eval_list_playground_models.py` |
| 0b. Setup model | User (or agent) names a model to stage/warm before a sweep | `uv run python scripts/eval_setup_playground_model.py --model <tag>` |
| 1. Examples | New golden rows | `uv run python scripts/eval_create_golden_examples.py` |
| 2. Sweep | Run / compare configs | `uv run python scripts/eval_sweep_golden_models.py` |
| 3. Aggregate | After one or more experiment JSONs exist | `uv run python scripts/eval_aggregate_experiments.py` |

Helpers live in `packages/eval/vecinita_eval/` (`playground_setup.py`, `golden_draft.py`,
`sweep.py`, `experiments.py`). Spec: `docs/eval-golden-set.md`.

## Agent routing (choose scripts from the user prompt)

Decide which steps to run from the request; skip steps the user did not ask for.

| User intent (examples) | Run |
|------------------------|-----|
| "What models are available?" / "list playground models" | **0a** only (`--json` for machine-readable) |
| "Pull / stage / warm `qwen3:8b`" / "set up model X for eval" | **0b** with `--model` / `--models` |
| "Create a golden example …" | **1** |
| "Sweep models A,B …" / "compare prompts" | **0b** (if models may be missing) → **2** → **3** → agent summary |
| "Aggregate the last experiments" / "rank results" | **3** → agent summary (canvas preferred) |
| Full experiment from scratch | **0a** (discover) → **0b** (ensure) → **1** (if needed) → **2** → **3** → agent |

Do **not** invent model tags. Prefer listing first when the user did not specify models.
Unset `VECINITA_MODAL_OLLAMA_URL` before any live call (ADR-037).

## Hard constraints

- Env: `VECINITA_MODAL_LLM_URL`, `VECINITA_MODAL_EMBED_URL`, `DATABASE_URL` (+ proxy key when required).
- List/pull/setup prefer `VECINITA_MODAL_LLM_PLAYGROUND_URL` (falls back to `VECINITA_MODAL_LLM_URL`).
- **Unset** `VECINITA_MODAL_OLLAMA_URL` (ADR-037). Path aliases `/models/ollama*` are FE compat only — staging is HF Hub + vLLM, not `ollama pull`.
- Corpus is **read-only** — never `reset_corpus_tables` / seed while `prod.env` is sourced (corpus-db-safety).
- Golden schema fields: `id`, `locale`, `domain`, `question`, `retrieval_expectation`, `required_facts`, optional `expected_doc_url(s)`.

## Step 0a — List playground models

```bash
set -a && source prod.env && set +a
unset VECINITA_MODAL_OLLAMA_URL

uv run python scripts/eval_list_playground_models.py
# or: ... --json | --available-only
```

## Step 0b — Ensure / warm a model

```bash
set -a && source prod.env && set +a
unset VECINITA_MODAL_OLLAMA_URL

uv run python scripts/eval_setup_playground_model.py \
  --model qwen3:8b
# or: --models qwen2.5:1.5b-instruct,qwen3:8b
# flags: --no-pull | --no-wait | --no-warm | --json
```

## Step 1 — Example generation

### Interview first (required for new/changed golden rows)

Before writing golden fixtures (`qa_pairs.json` for CI / `qa_pairs_staging.json` for
live corpus), interview the operator with **AskQuestion** (batch when
possible). Cover **inputs** (what to capture) and **outputs** (how scoring resolves URLs).

**Inputs — ask:**

1. **Case identity** — `id`, `locale` (`en`/`es`), `domain`
   (`community`/`housing`/`legal`/`edge`)
2. **Question** — realistic phrasing (no PII)
3. **Retrieval expectation** — `hit` | `any_of` | `abstain` | `empty`
4. **Required facts** — bullets grounded in the source doc
5. **URL profile(s)** — which corpus this row must pass against:
   - Fixture only (`fixture://…`)
   - Staging/live only (`https://…`)
   - **Both** (dual URL — recommended for staging sweeps)

When dual URL is chosen, collect **both**:
- Fixture URL(s) under `data/fixtures/corpus/`
- Live/staging document URL(s) that already exist in the target DB (do not invent;
  confirm via retrieval smoke or operator paste)

**Outputs — ask which scoring shape to write:**

| Option | Schema shape | Passes when |
|--------|--------------|-------------|
| **A — `any_of` dual list** (recommended) | `retrieval_expectation: any_of` + `expected_doc_urls: [fixture, https, …]` | Any listed URL appears in top-k |
| **B — profile fields** | Keep `hit` + add `expected_doc_url_staging` (schema/ADR change) | Runner picks URL by `corpus_profile` |
| **C — fixture hit only** | `hit` + single `expected_doc_url: fixture://…` | Fixture corpus DB only |
| **D — staging hit only** | `hit` + single `expected_doc_url: https://…` | Live/staging sweeps only |

Default recommendation: **A** — no schema change; works for fixture seed DBs and live
`DATABASE_URL` sweeps. Last option always: "Let me explain / provide more context".

Also ask **output locale pair**: create en-only, or paired en+es now?

Then run:

```bash
uv run python scripts/eval_create_golden_examples.py \
  --id community-new-case --locale en --domain community \
  --question "..." \
  --expected-doc-url-multi fixture://corpus/en/community-resources.md \
  --expected-doc-url-multi https://example.org/community-resources \
  --retrieval-expectation any_of \
  --required-fact "..." \
  --fixture data/fixtures/eval/qa_pairs_staging.json --append
```

For CI / seeded fixture corpus, use `--fixture data/fixtures/eval/qa_pairs.json` instead.

Single-URL `hit` still supported via `--expected-doc-url`. Or `--draft path/to/draft.json`
(object or array). Use `--replace` to overwrite same `id`+`locale`.

## Step 2 — Evaluate / sweep (saves JSON)

Always drops an experiment JSON under `--results-dir` (default `data/eval-experiments/`) unless `--no-save`.

```bash
set -a && source prod.env && set +a
unset VECINITA_MODAL_OLLAMA_URL

uv run python scripts/eval_sweep_golden_models.py \
  --models qwen2.5:1.5b-instruct,qwen3:8b \
  --temperatures 0.0,0.2 \
  --runs 3 \
  --system-prompt-dir data/fixtures/eval/prompts \
  --rules-file data/fixtures/eval/sample_rules.json \
  --extra-fixture data/fixtures/eval/similar_examples.json \
  --results-dir data/eval-experiments \
  --limit 4
```

Multi-prompt options: `--system-prompt-files a.txt,b.txt`, `--system-prompt-dir`, or single `--system-prompt` / `--system-prompt-file`.

Dry-run grid: add `--dry-run`.

## Step 3 — Load + aggregate

```bash
uv run python scripts/eval_aggregate_experiments.py \
  --results-dir data/eval-experiments \
  --group-by model_id,prompt_name,temperature \
  --metrics retrieval_relevance,faithfulness,wall_time_s,spawn_wall_time_s \
  --out data/eval-experiments/aggregate.json
```

## Step 4 — Agent

1. Read `aggregate.json` (and optionally latest experiment JSON).
2. Rank groups by target metrics (default: retrieval, faithfulness, wall time).
3. Present findings (prefer a Cursor canvas for multi-group comparisons).
4. Recommend promote candidates (model + prompt + params) — do not auto-promote prod config.

## Checklist

```
- [ ] (If needed) Listed playground models / staged requested tags
- [ ] Golden rows valid / appended
- [ ] Sweep dry-run looks right
- [ ] Live sweep wrote data/eval-experiments/<id>.json
- [ ] Aggregate written with intended --group-by / --metrics
- [ ] Agent summary / canvas from aggregate
```
