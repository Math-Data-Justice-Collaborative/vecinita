# F45 CE ship gate report (TC-184 / AC-BB9) — EV-018 re-gate

> **Session:** S021 · **Cycle:** EV-018 · **Feature:** F45  
> **Predecessor template:** `docs/sessions/S020-retrieval-batch-b/reports/ce-ship-gate.md`  
> **Metrics JSON:** [spike-f45-ce-ship-gate.json](./spike-f45-ce-ship-gate.json)  
> **Ops note:** [t100-1-ce-ship-gate.md](./t100-1-ce-ship-gate.md)  
> **Status:** **PASS** — floors met after F46 Path B restore (2026-08-02)

## Ship candidate

| Knob | Value |
|------|-------|
| CE model | `BAAI/bge-reranker-v2-m3` |
| GPU / app | Modal **T4** ephemeral `vecinita-spike-f45-rerank` |
| Retrieve N / keep_k | 20 / 5 |
| Packing | **P1** (F42) |
| LLM URL | **prod** `VECINITA_MODAL_LLM_URL` |
| Prod flag | `VECINITA_RAG_RERANK_CE` remains **false** until 12/13 Path A approval |

## Floors (must both pass)

| Metric | Floor | Observed (`CE+P1`) | Pass? |
|--------|-------|--------------------|-------|
| Answer relevancy | ≥ **0.28** | **0.778** | ☑ |
| Faithfulness | ≥ **0.91** | **0.938** | ☑ |

Top-level harness field: `ship_gate_pass` → **true**

## Same-run control

| Cell | relevancy | faith | notes |
|------|-----------|-------|-------|
| R0+P1 | 0.722 | 0.938 | Dense + P1 control |
| CE+P1 | 0.778 | 0.938 | Ship candidate — floors apply here |

## Cost (informational)

| Item | Value |
|------|-------|
| CE scoring wall-clock | **54506** ms |
| Rough T4 estimate USD | **0.0089** |

## Decision

- [x] **Ship (metrics)** — floors met; enable prod CE only after 12/13 Path A approval  
- [ ] **Spike-only** — floors unmet; leave `#83` open; keep flag default off  

**Recorded decision:** AC-BB9 / TC-184 **PASS** on staging post–F46 (S021-D24). Keep `#83` open until staging Path A flag flip is approved; default flag stays **off** in code (AC-FO4 / TC-183).

## Operator checklist

- [x] Ran CE ship-gate harness against staging golden (non-empty pools)  
- [x] Wrote `spike-f45-ce-ship-gate.json`  
- [x] Filled observed metrics + pass/fail  
- [x] Confirmed ChatRAG spike used prod LLM URL (`llm_url_kind=prod`)  
- [ ] If ship: open follow-up to flip `VECINITA_RAG_RERANK_CE` on staging first (12/13)  

## References

- UJ-060 · TC-184 · AC-BB9 · AC-FO3/FO4 · feature-list F45  
- F46 evidence: `t99-5-f46-closeout.md`
