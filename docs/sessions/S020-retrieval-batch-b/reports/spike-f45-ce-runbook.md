# F45 CE spike runbook — Modal T4 ship gate (TC-184 / UJ-060)

> **Session:** S020 · **Cycle:** EV-017 · **Feature:** F45 · **Decisions:** RD-204, S020-D5/D11/D12/D15  
> **Date:** 2026-08-02  
> **Scripts:** `docs/sessions/S020-retrieval-batch-b/scripts/spike_f45_ce_modal.py`,  
> `docs/sessions/S020-retrieval-batch-b/scripts/spike_f45_ce_ship_gate.py`  
> **Metrics artifact:** `docs/sessions/S020-retrieval-batch-b/reports/spike-f45-ce-ship-gate.json`

## Purpose

Renew the cross-encoder track after S019 R3 (`bge-reranker-base` failed relevancy lift).
Spike **`BAAI/bge-reranker-v2-m3`** on an **ephemeral Modal T4** app
(`vecinita-spike-f45-rerank`). **Do not** enable prod `VECINITA_RAG_RERANK_CE` unless the
ship gate passes (S020-D5). ChatRAG / this harness must use **`VECINITA_MODAL_LLM_URL`**
(prod LLM) — never `VECINITA_MODAL_LLM_PLAYGROUND_URL` / `vecinita-llm-playground` (S020-D15).

## Ship floors (TC-184 / AC-BB9)

| Metric | Floor |
|--------|-------|
| Answer relevancy (`CE+P1` cell) | ≥ **0.28** |
| Faithfulness (`CE+P1` cell) | ≥ **0.91** |

Harness writes `ship_gate_pass: true|false` from those floors. Prior R3 evidence is **not**
enough to ship.

## Preconditions

1. Staging `DATABASE_URL` (`*.ondigitalocean.com`) — golden retrieve against live corpus.
2. `VECINITA_MODAL_LLM_URL` + `VECINITA_MODAL_PROXY_KEY` (prod ChatRAG LLM).
3. `VECINITA_MODAL_EMBED_URL` (or embed client defaults) for pool retrieve.
4. Modal CLI authenticated (`modal` token) for ephemeral T4 run.
5. Fixture: `data/fixtures/eval/qa_pairs_staging.json`.

## Run (repo root)

```bash
set -a && source .env && set +a   # or prod.env locally — never commit
export PATH="$PWD/.venv/bin:$PATH"

# Optional knobs (defaults match F45 / F42 keep_k)
# export SPIKE_TOP_K=5
# export SPIKE_RETRIEVE_N=20
# export SPIKE_MIN_SCORE=0.2

uv run python docs/sessions/S020-retrieval-batch-b/scripts/spike_f45_ce_ship_gate.py
```

Ephemeral Modal app is started via `app.run()` inside the harness (no durable deploy).
Model weights cache on volume `spike-f45-rerank-models`.

## Metrics capture path

| Field | Location |
|-------|----------|
| JSON report | `docs/sessions/S020-retrieval-batch-b/reports/spike-f45-ce-ship-gate.json` |
| Key cells | `cells[]` — labels `R0+P1` (dense control) and `CE+P1` (gated candidate) |
| Gate boolean | top-level `ship_gate_pass` |
| CE model / GPU | `ce_model`, `ce_gpu`, `ce_app` |
| Cost note | `ce_scoring_wall_ms`, `ce_modal_cost_estimate_usd` |
| LLM URL kind | `llm_url_kind` must be `"prod"` |

After a live run:

1. Commit or attach the JSON under the session `reports/` folder (operator choice; large
   per-row payloads may stay local).
2. Summarize in the T98.3 ship-gate report template (Path A) — pass/fail + EN/ES if present.
3. If `ship_gate_pass` is **false**, leave `#83` open; keep `VECINITA_RAG_RERANK_CE` default
   **off**.
4. If **true**, record gate evidence before any prod flag enablement (12/13 staging Path A).

## Comparison cells

| Label | Rerank | Pack | Role |
|-------|--------|------|------|
| R0+P1 | dense top_k | P1 | Same-run control (F42 packing) |
| CE+P1 | `bge-reranker-v2-m3` | P1 | Ship candidate — floors apply here |

## Out of scope for this runbook

- Durable Modal CE deploy / playground CE hosting
- Default-on ChatRAG CE without gate evidence
- Replacing F42 Hy1 packing or multi-query knobs
- T98.3 filled results narrative (template filled after metrics exist)

## Checklist

- [ ] Staging DB + prod LLM URL verified (not playground)
- [ ] Spike harness completed; JSON written to metrics path above
- [ ] `ship_gate_pass` recorded; T98.3 report drafted from JSON
- [ ] Prod flag remains off unless gate passed and deploy approved
