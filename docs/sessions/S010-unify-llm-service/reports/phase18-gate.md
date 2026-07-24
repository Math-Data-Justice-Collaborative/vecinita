# Phase 18 gate checklist (F39 client consolidation)

> Session: S010-unify-llm-service / EV-011 / F39  
> Branch: `feat/S010-unify-llm-service`  
> Date: 2026-07-24  
> Spec: TP-S010-17–31, ADR-037, RD-163–RD-172

## Status summary

| Layer | Status | Notes |
|-------|--------|-------|
| M77–M79 (Slices A–C) | **complete** | Prior verify PASS — `verification-report.md` (M79) |
| M80 T80.1–T80.6 (Slice D) | **complete** | Two apps + prod pin + playground URL routing |
| M80 T80.7 | **blocked** | Operator live deploy + smoke (defer 13-deploy-smoke) |
| M81 T81.1–T81.4 (Slice E) | **complete** | Ollama fallbacks removed; shared-schemas on llm-client |
| M81 T81.5 | **this doc** | Gate checklist + verify pointer |

**Phase 18 gate:** **PENDING** until T80.7 operator smoke + final `08-verify-build`.

## Gate criteria

| Criterion | T2 (unit/CI) | T3 (live) |
|-----------|--------------|-----------|
| All M77–M81 tasks completed (T77.1–T81.5) | ⬜ T80.7 open | — |
| TC-141–TC-145 green; UJ-048/UJ-049 | ✅ unit/e2e local | ⬜ staging |
| AC-E34–AC-E38; engine isolation smoke | ✅ unit (TC-145) | ⬜ T80.7 |
| Single `LlmClient`; no `OllamaModelsClient`; FE rename + aliases | ✅ | — |
| Real vLLM SSE; proxy on non-health | ✅ | ⬜ |
| Two Modal apps + shared `llm-models` | ✅ code/scripts | ⬜ deploy |
| No Ollama env fallbacks; `shared-schemas` on llm-client | ✅ | — |
| No provider ABC | ✅ | — |
| ruff / basedpyright / ESLint; full suites | ⬜ final 08-verify | — |

## Verify pointer (08-verify-build)

When T80.7 unblocks (or is waived), run **08-verify-build** at Phase 18 scope:

1. `make check` + full pytest / Vitest per `ci-after-push.mdc`
2. Confirm `tests/unit/modal/test_llm_engine_isolation.py` green
3. Confirm no `VECINITA_MODAL_OLLAMA_URL` client fallbacks
4. Record results in this session folder:
   - `docs/sessions/S010-unify-llm-service/reports/verification-report.md` (append Phase 18 / final)
5. Per **TP-S010-21**: open single evolve **PR-53** after slices A–E (no per-milestone PRs)

## Key commits (M80–M81)

| SHA | Task |
|-----|------|
| `5788fb9` | T80.1 engine isolation tests |
| `4c2c149` | T80.2 playground Modal app |
| `60a30c6` | T80.3 prod pin |
| `895310c` | T80.4 playground URL routing |
| `05296ce` | T80.5 deploy both apps |
| `4e5c216` | T80.6 docs two-app order |
| `a0e38b2`–`64ccf9f` | T81.1–T81.4 Slice E |

## Next

1. **Operator:** approve T80.7 — `bash scripts/deploy/modal.sh`, sync `VECINITA_MODAL_LLM_PLAYGROUND_URL`, smoke playground pull + prod chat.
2. **08-verify-build** Phase 18 final.
3. Open **PR-53** (TP-S010-21).
