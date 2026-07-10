# Routing plan — S010-unify-llm-service

**Approved:** 2026-07-10 (routing amendment after ADR-037 client-consolidation decisions)

| Stage | Required | Mode | Status | Notes |
|-------|----------|------|--------|-------|
| 00-context | yes | scoped + partial re-run | completing | ADR-037 + 2026-07-10 consolidation decisions |
| 01-requirements | yes | **delta re-open** | pending | Spec F39 follow-on from R-S010-00-1…9 |
| 02-verify-plan | no | — | skipped | Tooling/docs already exist |
| 03-plan-tooling | no | — | skipped | Tooling already exists |
| 04-tech-plan | yes | **delta re-open** | pending | Client merge, rename map, engine split, streaming |
| 05-verify-tech | no | — | skipped | Tooling already exists |
| 06-tech-tooling | no | — | skipped | Tooling already exists |
| 07-build | yes | slices A–E | pending | See build slices below |
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
| **D** | 7 | Separate playground Modal class; prod pinned to fixed default model |
| **E** | 8 | Drop legacy Ollama env fallbacks; docstrings; `shared-schemas` on `llm-client` |

## Skip rationale

- **02 / 03 / 05 / 06** — project tooling and plan-verification gates already established; delta work is requirements + tech plan + build only.
- **Provider ABC (decision 9)** — explicitly out of scope; no stage for multi-provider framework.

## Next stage after 00

**01-requirements** (delta) — encode R1–R9 into feature-list / acceptance criteria under F39.
