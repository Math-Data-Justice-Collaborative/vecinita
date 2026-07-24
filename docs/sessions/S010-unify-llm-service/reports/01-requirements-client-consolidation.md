# 01-requirements — F39 client consolidation (EV-011 follow-on)

**Session:** S010-unify-llm-service  
**Date:** 2026-07-10  
**Stage:** 01-requirements (delta reopen)  
**ADR:** [ADR-037](../../adr/ADR-037-unified-vecinita-llm-modal-app.md) (amended)  
**Feature:** F39 follow-on (no F40)  
**Seed:** [checkpoints/01-requirements-seed.md](../checkpoints/01-requirements-seed.md)

## Interview outcomes

| # | Topic | Resolution |
|---|-------|------------|
| Q1 | Locked S1–S10 | **Approved all** → RD-163–RD-172 |
| Q2 | Document manifest | **Approved as-is** |
| Q3 | Open questions | **All recommended** — F39 follow-on; amend ADR-037; aliases-only Slice A; prod pin `qwen2.5:1.5b-instruct`; stream tests = API E2E + unit |

## Decisions recorded

RD-163–RD-172 in `docs/decisions.md` §EV-011 requirements decisions (2026-07-10).

## Documents updated

| Document | Delta |
|----------|--------|
| `docs/feature-list.md` | F39 follow-on slices A–E |
| `docs/spec.md` | LLM client + prompt helper component |
| `docs/user-journeys.md` | UJ-001 stream note; UJ-048 catalog/auth; **UJ-049** auth failure |
| `docs/test-plan.md` | TC-141–TC-145 |
| `docs/api-contract.md` | Proxy auth on generate/warm/models; real stream contract |
| `docs/config-spec.md` | Proxy required; `VECINITA_LLM_MODEL_ID` pin; drop Ollama fallbacks |
| `docs/acceptance-criteria.md` | AC-E34–AC-E38 |
| `docs/deployment-integration.md` | Slice D dual class; proxy everywhere |
| `docs/decisions.md` | RD-163–RD-172 |
| `docs/adr/ADR-037-*.md` | Amendment §§9–16 |
| `.cursor/rules/unified-vecinita-llm.mdc` | One client; auth; no provider ABC; slices |

## Test requirements (by layer)

| Change | Layer | TC |
|--------|-------|-----|
| Unified client + rename | Unit + integration | TC-144 |
| Real streaming | Unit + API E2E | TC-143 |
| Proxy auth | Unit + integration | TC-142 / UJ-049 |
| Catalog gate | Unit + UJ-048 e2e | TC-141 |
| Chat-template + engine isolate | Unit / smoke | TC-145 |

## Gaps

None — locked decisions confirmed; open questions accepted as recommended.

## Next step

**04-tech-plan** (delta) — map RD-163–RD-172 → tasks/milestones; Slice A first for 07-build.
