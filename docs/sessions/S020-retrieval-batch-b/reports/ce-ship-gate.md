# F45 CE ship gate report (TC-184 / AC-BB9) — Path A

> **Session:** S020 · **Cycle:** EV-017 · **Feature:** F45  
> **Decisions:** S020-D5/D11/D12/D13/D15 · RD-204–RD-206  
> **Runbook:** [spike-f45-ce-runbook.md](./spike-f45-ce-runbook.md)  
> **Metrics JSON:** [spike-f45-ce-ship-gate.json](./spike-f45-ce-ship-gate.json) *(fill after live spike)*  
> **Status:** **PENDING** — template only until staging spike metrics exist

## Ship candidate

| Knob | Value |
|------|-------|
| CE model | `BAAI/bge-reranker-v2-m3` |
| GPU / app | Modal **T4** ephemeral `vecinita-spike-f45-rerank` |
| Retrieve N / keep_k | 20 / 5 (defaults) |
| Packing | **P1** (F42) |
| LLM URL | **prod** `VECINITA_MODAL_LLM_URL` (never playground) |
| Prod flag | `VECINITA_RAG_RERANK_CE` remains **false** unless gate passes |

## Floors (must both pass)

| Metric | Floor | Observed (`CE+P1`) | Pass? |
|--------|-------|--------------------|-------|
| Answer relevancy | ≥ **0.28** | _TBD_ | ☐ |
| Faithfulness | ≥ **0.91** | _TBD_ | ☐ |

Top-level harness field: `ship_gate_pass` → _TBD_

## Same-run control

| Cell | relevancy | faith | notes |
|------|-----------|-------|-------|
| R0+P1 | _TBD_ | _TBD_ | Dense + P1 control |
| CE+P1 | _TBD_ | _TBD_ | Ship candidate |

## Cost (informational)

| Item | Value |
|------|-------|
| CE scoring wall-clock | _TBD_ (`ce_scoring_wall_ms`) |
| Rough T4 estimate USD | _TBD_ (`ce_modal_cost_estimate_usd`) |

## Decision

- [ ] **Ship** — floors met; enable prod CE only after 12/13 Path A approval  
- [ ] **Spike-only** — floors unmet; leave `#83` open; keep flag default off  

**Recorded decision:** _pending live metrics_

## Operator checklist

- [ ] Ran [spike-f45-ce-runbook.md](./spike-f45-ce-runbook.md) against staging golden  
- [ ] Wrote `spike-f45-ce-ship-gate.json` under this `reports/` folder  
- [ ] Filled observed metrics + pass/fail above  
- [ ] Confirmed ChatRAG did **not** use playground LLM URL  
- [ ] If ship: open follow-up to flip `VECINITA_RAG_RERANK_CE` on staging first  

## References

- Prior reject (R3 / `bge-reranker-base`):  
  `docs/sessions/S019-retrieval-quality/reports/spike-a4-r3-cross-encoder.md`
- UJ-060 · TC-184 · AC-BB9 · feature-list F45
