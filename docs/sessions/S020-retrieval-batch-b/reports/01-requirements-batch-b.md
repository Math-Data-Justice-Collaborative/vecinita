# 01-requirements — EV-017 Retrieval Batch B (S020)

> **Status:** completed (delta) · **Date:** 2026-08-02  
> **Features:** F43, F44, F45 · **Decisions:** S020-D9–D14 · **RD:** RD-197–RD-208

## Seed

Loaded `checkpoints/01-requirements-seed.md`. Locked L1–L12 approved (D9). Open Q1–Q5
resolved (D10–D14).

## Document manifest (written)

| Document | Delta |
|----------|-------|
| `docs/feature-list.md` | F43–F45 Planned; F42 → Implemented |
| `docs/spec.md` | ChatRAG algorithm + query path + changelog |
| `docs/config-spec.md` | Cache / soft language / CE env vars + validation |
| `docs/api-contract.md` | `cache_hit` on `/ask` + stream `done` |
| `docs/user-journeys.md` | UJ-057–060 |
| `docs/test-plan.md` | TC-176–184 + UJ mapping + thresholds |
| `docs/acceptance-criteria.md` | AC-BB1–BB10 + CE benches |
| `docs/decisions.md` | RD-197–RD-208 |
| `docs/decisions/evolve-decisions.md` | §EV-017 D9–D14 |

**No new ADR** this stage — ADR-004/006/041 constraints carried; CE Modal spike reuses prior
pattern. OpenAPI `openapi/chat-rag.yaml` update deferred to **07-build** with contract tests.

## Fn summary

| Fn | Ship intent |
|----|-------------|
| F43 | Ship H1 cascade (cost) |
| F44 | Ship config-gated L1 default off + empty-hit fixture |
| F45 | Spike `bge-reranker-v2-m3`; prod only if gate (0.28 / 0.91) |

## Next

**02-verify-plan** — consistency + statement audit on changed sections.
