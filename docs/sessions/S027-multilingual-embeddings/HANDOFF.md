# HANDOFF — S027 / EV-025

| Field | Value |
|-------|--------|
| Session | S027-multilingual-embeddings |
| Cycle | EV-025 — multilingual embeddings (#159) |
| Branch | `evolve/EV-025-multilingual-embeddings` |
| Stage | **08-verify-build** — M119 CONDITIONAL PASS; S027-D32 = open PR (CI + F62 hooks; no in-agent `test-py`) |

## M119 shipped (local)

- `packages/embedding-client` — `prefixes.py` (e5 query/passage, runtime enum, dim assert)
- `modal_pins.py` — FE/ST/ONNX image ranges + 4GiB CPU / 300s timeout
- `infra/modal/embedding_app.py` — runtime switch + local package mount
- Tests: `test_embedding_prefixes_runtime.py`, `test_embedding_modal_pins.py` (32 unit green)

## Next

1. Open/push **PR-67** (M119 minor); watch GitHub CI
2. Continue **M120** T120.1 after PR recorded

## Commits (M119)

Phase A/B docs + `[T119.1]`–`[T119.5]` on `evolve/EV-025-multilingual-embeddings`.  
08: CONDITIONAL PASS — full local pytest offloaded to Husky F62 + GitHub CI (S027-D32).

## Links

- [roadmap.md](./roadmap.md)
- Issue [#159](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/159)
