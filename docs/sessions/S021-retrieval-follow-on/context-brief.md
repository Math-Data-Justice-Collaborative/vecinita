# Context brief — S021 / EV-018 (scoped, continues S020)

> **Mode:** delta / evolve — no paper or greenfield repo scan. Priors from S020 Path A close.

## Topology (unchanged)

Browser Admin + ChatRAG frontends → DO App Platform APIs → Modal LLM (`vecinita-llm` prod,
`vecinita-llm-playground` eval) + Supabase/Postgres corpus. Staging pin: `f24a620`
(PR #173). F42 packing + F43 H1 cache + F44 soft language **LIVE**; CE prod flag **off**.

## Why this session exists

| Observation (S020 Path A) | Implication |
|---------------------------|-------------|
| Golden CE ship gate: R0+P1 and CE+P1 both `retrieval=0.0`, faith **null** | Empty pools — not a CE quality comparison |
| Live H3 sample asks: empty `sources` | Retrieve path broken or mis-pinned on staging |
| F43 cache still worked (`none` → `exact`) | Ask path / cache OK; retrieve/index/corpus suspect |
| `ship_gate_pass=false` → spike-only | #83 stays open until non-empty re-gate |

## Hypotheses to investigate (Phase 0 / 01 / 07)

1. **Embed ↔ corpus pin drift** — staging corpus vectors not matching current embed model/dim
2. **`min_score` too high** — all candidates filtered (default 0.2 in prior spikes)
3. **Fixture / golden URLs** — staging golden points at docs not in live corpus
4. **Index / RPC / filter bug** — retrieve returns empty for other reasons (language, ACL, namespace)

## Constraints carried forward

- ADR-004: no identity-keyed chat history / cache keys
- ADR-006: LlamaIndex ChatRAG; LangGraph amend deferred (S019-D27)
- ADR-009 / ADR-037: prod synthesizer pin `qwen2.5:1.5b-instruct`
- ADR-041: H7+P1 packing shipped (F42)
- ADR-042: in-process H1 answer cache (F43)
- S020-D12: CE floors relevancy ≥ 0.28, faith ≥ 0.91
- S020-D21: Path A — F45 spike-only; prod CE off

## Sources

- `docs/sessions/S020-retrieval-batch-b/reports/evolve-summary.md`
- `docs/sessions/S020-retrieval-batch-b/reports/ce-ship-gate.md`
- `docs/sessions/S020-retrieval-batch-b/reports/spike-f45-ce-ship-gate.json`
- `docs/sessions/S020-retrieval-batch-b/reports/deploy-smoke.md`
- `docs/sessions/S020-retrieval-batch-b/reports/spike-f45-ce-runbook.md`
- `docs/user-journeys.md` § UJ-060
- `docs/feature-list.md` § F45
