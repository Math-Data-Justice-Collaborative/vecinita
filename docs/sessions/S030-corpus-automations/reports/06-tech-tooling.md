# 06-tech-tooling report — S030 / EV-027

> **Session:** S030 · **Cycle:** EV-027 · **Date:** 2026-08-07  
> **Mode:** evolve delta · **Status:** **completed** (S030-D33)  
> **Gate B→C:** PASS (S030-D32)  
> **Citations:** [Corpus: feature-list.md §F77] [Spec: docs/adr/ADR-053]
> [Spec: docs/dependency-inventory.md] [Spec: TP10]

## Plan (approved)

User chose **Approve all** + **exact `==` pins** (option 1 + pin-exact).

## Delta scope

| Area | Action |
|------|--------|
| Rules / hooks / CI | **Reuse** (03 + existing) — no new Cursor rules/hooks |
| Connectivity | **Verified** — `test_cors_policy.py`, staging smoke, `verify_connectivity.sh`, H4–H5 docs |
| FT train pins | **New** exact Modal-image pins + unit tests |

## Exact pins (Modal `vecinita-llm-finetune` only)

Source: `infra/modal/finetune_pins.py` → `FINETUNE_IMAGE_PIPS`

| Package | Pin | Notes |
|---------|-----|-------|
| peft | `==0.20.0` | Apache-2.0 |
| trl | `==1.9.2` | Apache-2.0; needs datasets≥4.7 |
| transformers | `==4.57.6` | Train image; **≠** llm serve `==4.51.3` |
| accelerate | `==1.14.0` | Apache-2.0 |
| datasets | `==4.8.5` | Apache-2.0 |
| bitsandbytes | **deferred** | QLoRA out of v1 |

Do **not** add these to DO app runtime or bump `llm_app` transformers without ADR.

## Artifacts

| Artifact | Path |
|----------|------|
| Pins module | `infra/modal/finetune_pins.py` |
| Unit tests | `tests/unit/modal/test_finetune_pins.py` (3 passed) |
| Inventory | `docs/dependency-inventory.md` (EV-027 rows + note) |

## Verification

| Check | Result |
|-------|--------|
| `pytest tests/unit/modal/test_finetune_pins.py` | ✓ 3 passed |
| basedpyright / ruff on new files | ✓ |
| Connectivity layout (CORS / smoke / script / H4–H5) | ✓ present |

## Phase B complete

- ✓ 05-verify-tech (S030-D31)
- ✓ Gate B→C (S030-D32)
- ✓ 06-tech-tooling (S030-D33)
- → Ready for Phase C: **07-build** M127

## Next

**07-build** — Phase 30 M127 (F75); wire `FINETUNE_IMAGE_PIPS` when implementing M129 `finetune_app.py`.
