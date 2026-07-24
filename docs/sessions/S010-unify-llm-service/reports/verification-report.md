# Verification Report

> Generated: 2026-07-23  
> Scope: M79 — Slice C: chat-template + catalog gate (T79.1–T79.6)  
> Branch: `feat/S010-unify-llm-service`  
> Session: S010-unify-llm-service / EV-011 / F39

## Summary

| Check | Status | Findings | Auto-Fixed | Tool |
|-------|--------|----------|------------|------|
| Lint (M79 paths) | PASS | 0 | 0 | ruff |
| Format | PASS | — | 0 | ruff format --check |
| Typecheck (M79 paths) | PASS | 0 | — | basedpyright |
| Tests (unit TC-145 / TC-141) | PASS | chat_template + catalog_gate + related | — | pytest |
| Tests (UJ-048 e2e + TC-141) | PASS | 3 passed with `with_local_postgres.sh` | — | pytest |
| Connectivity (H0c CORS) | PASS | `test_cors_policy.py` | — | pytest |
| Security | SKIPPED | No new third-party deps in M79 (embedded ChatML tokenizer; transformers still Modal-only) | — | — |
| Connectivity artifacts | PASS | H0c unit present; staging scripts unchanged | — | connectivity-gates |

Overall: **PASS** (M79 scope)

## Milestone notes

- T79.1–T79.3: shared `apply_chat_template` / `format_instruct_prompt` in `packages/llm-client`.
- T79.4: chat-rag, tagging, eval call shared helper; hand-rolled Qwen wraps removed.
- T79.5–T79.6: Modal list/pull + write-api pull gated by `resolve_hf_repo`; unmapped → HTTP 400 (TC-141 / UJ-048).
- PR policy: **TP-S010-21** — single evolve **PR-53** after slices A–E; no minor PR at M79.

## Commits (M79)

| SHA | Message |
|-----|---------|
| `e7103ca` | `[T79.1] test: lock apply_chat_template Qwen + non-Qwen fixtures (TC-145)` |
| `cf672a2` | `[T79.2] test: lock catalog ⊆ registry and unmapped pull 400 (TC-141)` |
| `c7529d8` | `[T79.3] feat: shared apply_chat_template helper in llm-client` |
| `e616043` | `[T79.4] feat: wire chat-rag/tagging/eval to shared chat-template helper` |
| `51d97a7` | `[T79.5] feat: gate list/pull to resolve_hf_repo; 400 on unmapped` |
| `4b1370e` | `[T79.6] test: UJ-048 e2e unmapped pull returns 400 (TC-141)` |

## Next

Continue **07-build** at **M80 / T80.1** (Slice D: two Modal apps + prod pin).

---

# Verification Report — Phase 18 final (T80.7)

> Generated: 2026-07-24  
> Scope: Phase 18 / T80.7 operator deploy + live smoke + deploy-path regressions  
> Branch: `feat/S010-unify-llm-service`  
> Session: S010-unify-llm-service / EV-011 / F39

## Summary

| Check | Status | Findings | Tool |
|-------|--------|----------|------|
| Lint (T80.7 fix paths) | PASS | 0 | ruff |
| Format | PASS | — | ruff format --check |
| Typecheck (fix paths) | PASS | 0 | basedpyright |
| Unit (lazy init, ASGI volume, catalog, isolation) | PASS | 26 | pytest |
| Live T80.7 smoke | PASS | pull + prod isolation + ChatRAG `modal_llm=ok` | operator |
| DO secrets verify | PASS | `do_verify_required_secrets.sh` | deploy |

Overall: **PASS** (Phase 18 / T80.7) — pending commit + push for **PR-53** (TP-S010-21).

## Live evidence

See `docs/sessions/S010-unify-llm-service/reports/t80.7-operator-smoke.md`.

## Uncommitted fix set (for PR-53)

- Lazy `vecinita_shared_schemas.__init__` (no eager PyJWT on Modal LLM image)
- ASGI `volumes={/models}` + `_commit_models_volume()` by name
- `scripts/deploy/modal.sh` → `uv run modal`
- Regression tests + phase gate / execution-plan bookkeeping

**Exclude from PR:** unrelated eval-golden-sweep WIP on this working tree.
