# HANDOFF — S027 / EV-025

| Field | Value |
|-------|--------|
| Session | S027-multilingual-embeddings |
| Cycle | EV-025 — multilingual embeddings (#159) |
| Branch | `evolve/EV-025-multilingual-embeddings` |
| Stage | **07-build** — **M119 complete** (T119.1–5); next **08-verify-build** then PR / M120 |

## M119 shipped (local)

- `packages/embedding-client` — `prefixes.py` (e5 query/passage, runtime enum, dim assert)
- `modal_pins.py` — FE/ST/ONNX image ranges + 4GiB CPU / 300s timeout
- `infra/modal/embedding_app.py` — runtime switch + local package mount
- Tests: `test_embedding_prefixes_runtime.py`, `test_embedding_modal_pins.py` (32 unit green)

## Next

1. **08-verify-build** for M119 (then minor PR)
2. Continue **M120** T120.1 (staging rechunk e2e red)

## Uncommitted

Working tree has Phase A–B docs + M119 code — commit when you ask (atomic task commits preferred).

## Links

- [roadmap.md](./roadmap.md)
- Issue [#159](https://github.com/Math-Data-Justice-Collaborative/vecinita/issues/159)
