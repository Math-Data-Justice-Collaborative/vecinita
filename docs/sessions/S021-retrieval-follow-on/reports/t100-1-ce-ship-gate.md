# T100.1 — CE ship-gate re-run (after F46 / UJ-061)

> **Session:** S021 · **Cycle:** EV-018 · **Feature:** F45 · **Date:** 2026-08-02  
> **Status:** completed · **ship_gate_pass:** **true**

## Preconditions

| Check | Evidence |
|-------|----------|
| AC-FO1 / UJ-061 | Path B promote `a0e8f32d-…`; empty@0.2 = 0/8 (`t99-5-f46-closeout.md`) |
| Staging pools in this run | All 18 golden rows `pool=20` at `min_score=0.2` |
| LLM URL | prod `VECINITA_MODAL_LLM_URL` (`llm_url_kind=prod`) |
| CE model / GPU | `BAAI/bge-reranker-v2-m3` / Modal T4 ephemeral |

## Command

```bash
set -a && source .env && set +a
export PATH="$PWD/.venv/bin:$PATH"
uv run python docs/sessions/S020-retrieval-batch-b/scripts/spike_f45_ce_ship_gate.py
```

Log: `t100-1-ce-ship-gate-run.log`  
JSON: `spike-f45-ce-ship-gate.json` (also under S020 `reports/`)

## Results (TC-184 / AC-BB9)

| Cell | retrieval | faith | relevancy | p95 ms |
|------|-----------|-------|-----------|--------|
| R0+P1 | 1.0 | 0.9375 | 0.722 | 2895 |
| **CE+P1** | **1.0** | **0.9375** | **0.778** | 2835 |

| Floor | Required | Observed | Pass |
|-------|----------|----------|------|
| Relevancy | ≥ 0.28 | **0.778** | yes |
| Faithfulness | ≥ 0.91 | **0.938** | yes |

**`ship_gate_pass=true`** · CE wall ~54.5s · est T4 USD ~0.0089

## Disposition pointer

See `ce-ship-gate.md` (S021) / updated S020 template — **ship candidate cleared floors**; prod `VECINITA_RAG_RERANK_CE` still **off** until 12/13 Path A approval (AC-FO4).
