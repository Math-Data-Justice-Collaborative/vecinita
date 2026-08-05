# T122.1 — TC-232–241 green gate

**Session:** S027-multilingual-embeddings · **Cycle:** EV-025 · **Milestone:** M122  
**Date:** 2026-08-05  
**Decision:** S027-D40 (#211 merged) · compose e2e waiver **S027-D35**

[Corpus: feature-list.md §F70] [Corpus: feature-list.md §F71]  
[Spec: docs/test-plan.md §TC-232–241] [Spec: docs/acceptance-criteria.md §AC-ME1–ME11]

## Result

| Gate | Status | Evidence |
|------|--------|----------|
| Unit TC map + AC-ME1–11 | **PASS** | `tests/unit/test_f70_f71_m122_green_gate.py` |
| Unit TC-233–234, 235–236, 239–241 contracts | **PASS** | shared_schemas + prefixes + modal pins + runbook |
| Stubbed API e2e TC-237–238 (+ TC-241 pin align) | **PASS** | `tests/e2e/test_uj075_multilingual_ask.py` (no compose) |
| Compose-backed UJ-076 e2e TC-232/235–236/239/241 | **WAIVED** | S027-D35 (Docker userns); covered by unit + schema contracts |
| Playwright | **N/A** | S027-D16 — no UI for UJ-075/076 |

## Command (local)

```bash
uv run pytest \
  tests/unit/test_f70_f71_m122_green_gate.py \
  tests/unit/test_embedding_prefixes_runtime.py \
  tests/unit/test_embedding_modal_pins.py \
  tests/unit/shared_schemas/test_f71_*.py \
  tests/unit/test_f71_tc240_cutover_runbook.py \
  tests/unit/test_f71_m121_green_gate.py \
  tests/e2e/test_uj075_multilingual_ask.py -q
```

**Outcome:** 33 passed (2026-08-05).

## Next

T122.2 — api-contract / deployment-integration / inventory micros / ADR-048 stage metadata.
