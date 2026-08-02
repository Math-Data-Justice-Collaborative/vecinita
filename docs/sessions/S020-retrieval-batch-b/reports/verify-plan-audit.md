# 02-verify-plan audit — EV-017 / F43–F45

> **Session:** S020 · **Cycle:** EV-017 · **Date:** 2026-08-02  
> **Mode:** evolve delta · **Status:** awaiting medium verdicts

## Inventory (delta)

| # | Document | Status |
|---|----------|--------|
| 1 | feature-list.md (F43–F45; F42 Implemented) | audited |
| 2 | spec.md (ChatRAG algorithm + query path) | audited |
| 3 | user-journeys.md (UJ-057–060) | audited |
| 4 | test-plan.md (TC-176–184) | audited |
| 5 | config-spec.md (cache / soft / CE knobs) | audited |
| 6 | api-contract.md (`cache_hit`) | audited |
| 7 | acceptance-criteria.md (AC-BB1–BB10) | audited |
| 8 | decisions.md (RD-197–208) | audited |

## Consistency

| Check | Result |
|-------|--------|
| Feature ↔ Spec | Pass — F43–F45 on ChatRAG + `packages/rag` |
| Feature ↔ Journey | Pass — UJ-057–060 |
| Journey ↔ Test | Pass — TC-176–184 |
| Spec ↔ Config | Pass — cascade/L1/CE flags + defaults |
| Test ↔ Acceptance | Pass — AC-BB1–BB9 ↔ TC-176–184; AC-BB10 scope |
| RD ↔ Spec/Config | Pass — RD-197–208 mirrored |
| Scope boundaries | Pass — no LangGraph; CE/soft default off |
| Connectivity | Pass — no new UI; no new CORS; API e2e only |
| OpenAPI | **Deferred to 07** — contract MD updated; yaml in build |

## Verdicts

### Auto-approved (high confidence)

From S020-D4–D14 / RD-197–208 (user-locked):

- F43 full H1 cascade; F44 L1 default off + empty-hit fixture; F45 spike+gate
- CE model `BAAI/bge-reranker-v2-m3`; ship floors 0.28 / 0.91
- Content-hash keys; TTL+size cap; corpus/F41 bust; Path A deploy
- UJ-057–060 / TC-176–184 / AC-BB1–BB10 mapping
- No identity-keyed cache; no ADR-006 amend this cycle

### Medium — need user verdict

| ID | Statement | Recommendation |
|----|-----------|----------------|
| M1 | Default `VECINITA_RAG_CACHE_SEMANTIC_THRESHOLD` = **0.92** is the conservative cosine | Approve |
| M2 | Default cache **TTL=3600s**, **max_entries=1024** (in-process LRU) | Approve |
| M3 | CE spike uses **ephemeral Modal T4 app** (S019 pattern); prod CE (if gated) calls same model via ChatRAG-configured endpoint — no playground URL for ChatRAG | Approve |
| M4 | `openapi/chat-rag.yaml` `cache_hit` update lands in **07-build** with contract check | Approve |

### Low / contradictions

None found.

## Gate A→B

Pending medium M1–M4 approval → then Phase B `04-tech-plan` (03/05/06 skipped).
