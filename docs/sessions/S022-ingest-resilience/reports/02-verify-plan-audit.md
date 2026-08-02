# 02-verify-plan audit — EV-019 / F47–F49

> **Session:** S022 · **Cycle:** EV-019 · **Date:** 2026-08-02  
> **Mode:** evolve delta · **Status:** in_progress (awaiting medium verdicts / Gate A→B)

## Inventory (delta)

| # | Document | Status |
|---|----------|--------|
| 1 | feature-list.md (F47–F49; F1 knobs) | audited |
| 2 | spec.md (ingest algorithm + data-flow) | audited — duplicate stage-7 numbering **fixed** |
| 3 | config-spec.md (overlap, tokenizer, embed retry) | audited |
| 4 | api-contract.md (ingest JobOptions) | audited |
| 5 | user-journeys.md (UJ-002 + UJ-062) | audited |
| 6 | test-plan.md (TC-187–192) | audited |
| 7 | acceptance-criteria.md (AC-IR1–IR7; AC-RB4 note) | audited — AC-RB4 clarify applied |
| 8 | dependency-inventory.md (transformers ingest) | audited |
| 9 | ADR-044 | audited |
| 10 | decisions.md RD-219–228 + evolve-decisions | audited |
| 11 | openapi/shared-schemas (cross-check) | audited — gaps deferred to 04/07 (M3) |

## Consistency

| Check | Result |
|-------|--------|
| Feature ↔ Spec | Pass — F47 hash gate; F48 embed retry; F49 chunk HF+overlap |
| Feature ↔ Journey | Pass — UJ-062 covers F47–F49; UJ-002 extended |
| Journey ↔ Test | Pass — UJ-062 ↔ TC-187–190; F49 unit TC-191–192 |
| Feature ↔ Test | Pass — F47↔187/188; F48↔189/190; F49↔191/192 |
| Spec ↔ Config | Pass — overlap 32, tokenizer id, embed batch/retry knobs |
| Test ↔ Acceptance | Pass — AC-IR1–6 ↔ TC-187–192; AC-IR7 scope |
| RD ↔ Spec / journeys | Pass — RD-219–228 mirror S022-D14–D19 |
| Scope boundaries | Pass — AC-IR7 / RD-228 |
| Connectivity | Pass — API e2e primary; Playwright optional if FE knobs (M5) |
| Naming | Pass — `chunk_overlap_tokens`, `force`, content_hash |
| OpenAPI SoT | Deferred — M3 (schema lag expected until 04/07) |
| AC-RB4 vs F47 | Clarified — rebuild vs ingest (M4 fix applied) |

## Verdicts

### Auto-approved (high confidence)

From S022-D8–D19 / RD-219–228 / Phase 0C `1,1,1,2,2,1`:

- F47–F49 Planned; investigate→ship; order F47+F48 then F49
- F47: refresh metadata; skip chunks+embed unless `force`
- F48: fail URL after retry exhaust; dim mismatch hard-fail; tags stay ADR-023 fail-open
- F49: overlap default **32**; HF tokenizer for `BAAI/bge-small-en-v1.5` (ADR-044)
- UJ-062 + extend UJ-002; TC-187–192; AC-IR1–IR7
- Deploy Path A; shared write/embed path only
- Out of scope: #159, #165 packing, CE flag, ADR-023 tag change

**Count:** 12 high-confidence auto-approved.

### Medium — pending user review

| ID | Statement | Source |
|----|-----------|--------|
| M1 | Embed defaults: `VECINITA_EMBED_BATCH_SIZE=32`, `MAX_RETRIES=3`, `RETRY_BACKOFF_S=0.5` | Inferred RD-226 |
| M2 | Job metrics field names (`skipped_unchanged`, etc.) finalized in 04/OpenAPI — not Gate A blockers | api-contract SHOULD |
| M3 | OpenAPI + `JobOptions` lack `chunk_overlap_tokens`; `force` description still rebuild-centric — update in 04/07 | ADR-011 lag |
| M4 | AC-RB4 = rebuild force wiring; ingest skip = AC-IR1/IR2 (prose clarified) | Contradiction resolved |
| M5 | Admin FE force/overlap knobs optional this cycle; Playwright only if UI ships | UJ-062 note |
| M6 | Spec data-flow duplicate stage 7 → renumber Browse+ (applied) | Doc bug fix |

### Low / open contradictions

None remaining after M4/M6 surgical fixes.

## Source updates (pre-verdict)

| File | Change |
|------|--------|
| `docs/spec.md` | Renumber data-flow stages 8–15 after Persist |
| `docs/acceptance-criteria.md` | AC-RB4 note: rebuild vs EV-019 ingest |

## Gate A→B

**Pending** medium approvals (recommend approve all M1–M6) → then Phase B `04-tech-plan`.
