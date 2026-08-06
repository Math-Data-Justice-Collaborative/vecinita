# E2E Behavior Report — EV-025 / S027 (F70–F71)

> Generated: 2026-08-05  
> Mechanism: API (FastAPI TestClient) — **no Playwright / UI** ([S027-D16](../../decisions/evolve-decisions.md))  
> Journeys: **UJ-075**, **UJ-076**  
> Branch: `evolve/EV-025-multilingual-embeddings` @ `c71e741`  
> Mode: evolve / delta · parallel with **09-qa**  
> Features: **F70** multilingual embed runtime · **F71** corpus re-embed + cutover  

[Corpus: feature-list.md §F70] [Corpus: feature-list.md §F71]  
[Spec: docs/user-journeys.md §UJ-075] [Spec: docs/user-journeys.md §UJ-076]  
[Spec: docs/test-plan.md §TC-232–241]  
[Spec: docs/decisions/evolve-decisions.md §S027-D16]  
[Spec: docs/decisions/evolve-decisions.md §S027-D35]  
[Corpus: WAIVED — compose UJ-076 e2e; reason: Docker userns / no local DB; decided: S027-D35]

## Summary

| # | Journey | Mechanism | Tier | Status | Notes |
|---|---------|-----------|------|--------|-------|
| 1 | UJ-075 Ask after multilingual cutover | Stubbed API e2e (TestClient) | T0 | **PASS** | TC-237, TC-238, TC-241 pin align · 3/3 |
| 2 | UJ-076 F36 EN/ES embed promote report | Compose-backed API e2e | T0 | **WAIVED** | TC-232/235–236/239/241 · S027-D35; 4 ERROR @ setup (no Postgres) |
| — | Browser / Playwright | — | T0-UI / T3 | **N/A** | S027-D16 — no UI for UJ-075/076 |
| — | T1 Integration | `tests/integration/` | T1 | **OUT OF SCOPE** | Delta mode; covered by unit + stub e2e |
| — | T2 Deploy smoke H1–H5 | staging | T2 | **DEFERRED** | 13-deploy-smoke (H4–H5 live cutover) |
| — | T3 Live UJ | staging/prod | T3 | **DEFERRED** | 13-deploy-smoke / 15-service-health |

**Overall T0 (EV-025 delta):** **PASS** (conditional on **S027-D35** compose waive) — stubbed UJ-075 **3 passed**; compose UJ-076 **WAIVED**.

## Connectivity columns

| Column | Result | Evidence |
|--------|--------|----------|
| **T0** | **PASS** (cond. S027-D35) | `uv run pytest tests/e2e/test_uj075_multilingual_ask.py -m "e2e and not live"` → **3 passed**; UJ-076 compose ERROR×4 recorded as **WAIVED** |
| **T2 connectivity** | **DEFERRED** | 13-deploy-smoke H1–H5 (live EN/ES ask + promote path after cutover) |
| **T3 browser** | **N/A** | S027-D16 — no Playwright for these journeys; live API smoke at 13 |

## Journey → test matrix

| Journey | Module | TCs | T0 | T3 |
|---------|--------|-----|----|-----|
| UJ-075 | `tests/e2e/test_uj075_multilingual_ask.py` | TC-237, TC-238 (+ TC-241 pin) | **PASS** (stubbed, no compose) | Live EN/ES ask @ 13 |
| UJ-076 | `tests/e2e/test_uj076_embed_promote_report.py` | TC-232, 235–236, 239, 241 | **WAIVED** (S027-D35) | Live F36/promote @ 13 |

## UJ-075 step results (T0 stubbed)

| Step | Assertion | Evidence | Status |
|------|-----------|----------|--------|
| 1 | EN `POST /api/v1/ask` → sources ≥ 1, `language=en` | TC-237 · `test_tc237_en_ask_after_cutover_returns_sources` | **PASS** |
| 2 | ES `POST /api/v1/ask` → sources ≥ 1, `language=es` | TC-238 · `test_tc238_es_ask_after_cutover_returns_sources` | **PASS** |
| 3 | Default chunk tokenizer == F70 embed pin | TC-241 · `test_tc241_cutover_tokenizer_default_matches_embed_pin` | **PASS** |

Stubbed ChatRAG retrieve/LLM — no compose, no live Modal embed. Prefix wiring covered by unit (out of this T0 surface).

## UJ-076 step results (compose — WAIVED)

| Step / TC | Assertion | Evidence | Status |
|-----------|-----------|----------|--------|
| TC-232/241 | Rebuild stamps E1 `embedding_model_id` + tokenizer | `test_tc232_241_rebuild_stamps_multilingual_pin_and_tokenizer` | **WAIVED** |
| TC-235–236 | F36 embed-promote report EN/ES vs E0 (+ dense) | `test_tc235_236_embed_promote_report_en_es_vs_e0` | **WAIVED** |
| TC-239 | Promote activates shadow; E0 retained | `test_tc239_promote_activates_shadow_e0_revision_retained` | **WAIVED** |
| TC-239 / AC-ME9 | E0 rollback restore via LEGACY_E0 rebuild | `test_tc239_e0_rollback_restores_live_text_and_stamps` | **WAIVED** |

**Observed without compose:** 4× `ERROR at setup` — `psycopg.OperationalError: Connection refused` on `localhost:5432` (expected; needs `DATABASE_URL` + compose).  
**Waiver:** [S027-D35](../../decisions/evolve-decisions.md) — local compose e2e waived this cycle (Docker userns class / S027-D32); unit + schema contracts + stubbed UJ-075 remain the gate. Re-run compose e2e when Docker works or at staging ops.

## Commands

```bash
# Stubbed UJ-075 (no compose) — PASS
uv run pytest tests/e2e/test_uj075_multilingual_ask.py -m "e2e and not live" -v --tb=short
# 3 passed in ~1.1s @ c71e741

# Compose-backed UJ-076 — expected ERROR without Postgres; WAIVED S027-D35
uv run pytest tests/e2e/test_uj076_embed_promote_report.py -m "e2e and not live" -v --tb=line
# 4 errors (setup: connection refused localhost:5432)
```

## AC mapping (delta)

| AC | Status @ 10-e2e |
|----|-----------------|
| AC-ME7 (EN sources) | **PASS** T0 (TC-237) |
| AC-ME8 (ES sources) | **PASS** T0 (TC-238) |
| AC-ME11 (tokenizer align) | **PASS** T0 pin assert (TC-241); compose stamp **WAIVED** |
| AC-ME3–ME6, AC-ME9–ME10 | **WAIVED** compose T0 (UJ-076); unit contracts prior; live @ 13 |

## Playwright / browser

**Not run** — S027-D16: no new Playwright/UI for UJ-075/076 (Jobs UI unchanged).

## Recommendation

**10-e2e can be marked `completed`** (conditional on S027-D35) for this cycle:

- T0 stubbed UJ-075 green  
- Compose UJ-076 documented **WAIVED**  
- T2/T3 / H4–H5 deferred to **13-deploy-smoke**  

Collect with 09-qa results at **11-verify-impl**.
