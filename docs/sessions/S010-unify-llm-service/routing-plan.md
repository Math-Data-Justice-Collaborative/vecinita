# Routing plan — S010-unify-llm-service

**Approved:** 2026-07-10 (routing amendment after ADR-037 client-consolidation decisions)

| Stage | Required | Mode | Status | Notes |
|-------|----------|------|--------|-------|
| 00-context | yes | scoped + partial re-run | **completed** (2026-07-10) | ADR-037 + consolidation decisions; seed written |
| 01-requirements | yes | **delta re-open** | **completed** (2026-07-10) | RD-163–RD-172; report `01-requirements-client-consolidation.md` |
| 02-verify-plan | no | — | skipped | Tooling/docs already exist |
| 03-plan-tooling | no | — | skipped | Tooling already exists |
| 04-tech-plan | yes | **delta re-open** | **completed** (2026-07-10) | TP-S010-17–31; Phase 18 M77–M81 |
| 05-verify-tech | no | — | skipped | Tooling already exists |
| 06-tech-tooling | no | — | skipped | Tooling already exists |
| 07-build | yes | slices A–E | pending | Start **M77 / T77.1**; see build slices below |
| 08-verify-build | yes | full | completed (2026-07-08); re-run after build | Prior PASS; re-verify after slices |
| 09-qa | yes | full | pending | |
| 10-e2e | yes | full | pending | |
| 11-verify-impl | yes | full | pending | |
| 12-verify-deploy | yes | full | pending | |
| 13-deploy-smoke | yes | full | pending | |

## Build slices (07-build)

| Slice | Decisions | Focus |
|-------|-----------|--------|
| **A (first)** | 1 + 4 | One `LlmClient` surface + rename Ollama → playground (keep `/models/ollama` aliases) |
| **B** | 2 + 3 | Real vLLM token streaming + proxy key on all LLM routes |
| **C** | 5 + 6 | Shared HF `apply_chat_template` + catalog gated by `resolve_hf_repo` |
| **D** | 7 | Separate playground **Modal app** (`vecinita-llm-playground`); prod pinned; shared `llm-models` |
| **E** | 8 | Drop legacy Ollama env fallbacks; docstrings; `shared-schemas` on `llm-client` |

## Skip rationale

- **02 / 03 / 05 / 06** — project tooling and plan-verification gates already established; delta work is requirements + tech plan + build only.
- **Provider ABC (decision 9)** — explicitly out of scope; no stage for multi-provider framework.

## Next stage after 04

**07-build** — Phase 18 / M77 / T77.1 (Slice A: one client + rename).

**Tech-plan report:** [`reports/04-tech-plan-client-consolidation.md`](./reports/04-tech-plan-client-consolidation.md)
