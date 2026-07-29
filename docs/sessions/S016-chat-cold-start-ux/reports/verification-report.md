# Verification report — EV-014 / S016 F40 (08-verify-build)

**Date:** 2026-07-29  
**Branch:** `evolve/EV-014-chat-cold-start-ux`  
**Scope:** ChatRAG cold-start wait UX (F40)

## Results

| Check | Result | Notes |
|-------|--------|-------|
| `uv run ruff check` | PASS | via make check-fast (Python portion) |
| chat-rag-frontend `npm run lint` | PASS | |
| chat-rag-frontend `npm run typecheck` | PASS | |
| chat-rag-frontend Vitest (full) | PASS | 162 tests |
| Playwright TC-160 `uj052-cold-start-wait` | PASS | |
| `tests/unit/test_cors_policy.py` | PASS | no CORS change (H9) |
| `make check-fast` lint-fe gate | ADVISORY | shell Node 22; project requires ≥24 (`.nvmrc`) — FE lint/typecheck OK when run under workspace npm |

## Connectivity

- No API / CORS contract change (RD-185 / Gate A→B H9).
- FE-only preference cookie; not attached to ask/stream.

## Verdict

**PASS** — ready for Lean next stage **10-e2e** (Playwright already exercised TC-160; 10 may broaden).

## Uncommitted

Working tree has F40 implementation + docs; commit not created (await user request).
