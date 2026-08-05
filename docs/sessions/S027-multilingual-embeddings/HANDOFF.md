# HANDOFF — S027 / EV-025

| Field | Value |
|-------|--------|
| Session | S027-multilingual-embeddings |
| Cycle | EV-025 — multilingual embeddings (#159) |
| Branch | `evolve/EV-025-multilingual-embeddings` |
| Stage | **08 done / PR-67 open** — [#208](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/208) CI green @`8e81ad3`; next M120 or merge |

## M119 shipped (local)

- `packages/embedding-client` — `prefixes.py` (e5 query/passage, runtime enum, dim assert)
- `modal_pins.py` — FE/ST/ONNX image ranges + 4GiB CPU / 300s timeout
- `infra/modal/embedding_app.py` — runtime switch + local package mount
- Tests: `test_embedding_prefixes_runtime.py`, `test_embedding_modal_pins.py` (32 unit green)

## Next

1. AskQuestion: continue **M120** T120.1 vs pause vs merge #208 first
2. Merge still needs explicit approval

## Commits (M119)

Phase A/B + `[T119.1]`–`[T119.5]` + coverage branch fix on `evolve/EV-025-multilingual-embeddings`.  
PR: https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/208 — CI green.  
Long jobs: Husky F62 (pre-commit) + GitHub CI (S027-D32); no in-agent `make test-py`.

## Links

- [roadmap.md](./roadmap.md)
- Issue [#159](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/159)
