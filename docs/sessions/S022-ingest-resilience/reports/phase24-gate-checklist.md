# Phase 24 gate checklist — EV-019 / S022

> **Date:** 2026-08-02 · **Stage:** 07-build M104 (T104.3)

| Criterion | Status | Evidence |
|-----------|--------|----------|
| M101–M104 tasks completed | in progress (M104 landing) | execution-plan Phase 24 |
| AC-IR1–IR6 at T2 | unit + e2e | TC-187–192; `test_uj062_*`; `test_chunk_hf_overlap` |
| AC-IR7 scope held | yes | `test_ac_ir7_scope.py`; no UJ-062 Playwright |
| OpenAPI `chunk_overlap_tokens` + ingest `force` | yes | `openapi/data-management.yaml` |
| Embed defaults 32 / 3 / 0.5s | yes | embedding-client + M102 |
| ADR-044 reused (no new ADR) | yes | ADR-044 |
| No #159 / #165 / CE flip / tag fail-open change | yes | AC-IR7 + decisions |
| Admin FE / Playwright skipped | yes | TP4 / M5 |
| ruff / basedpyright / UJ-062 pytest | pending 08-verify-build | — |

**Path A:** ship code with default overlap 32 for **new** ingest.  
**Path B:** operator `rechunk` rebuild when live corpus must match HF+overlap chunks (RD-227).
