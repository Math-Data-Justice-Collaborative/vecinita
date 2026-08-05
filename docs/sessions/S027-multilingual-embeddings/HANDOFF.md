# HANDOFF — S027 / EV-025

| Field | Value |
|-------|--------|
| Session | S027-multilingual-embeddings |
| Cycle | EV-025 — multilingual embeddings (#159) |
| Branch | `evolve/EV-025-multilingual-embeddings` |
| Stage | **07-build M120** — T120.1 red landed; next T120.2 |

## Done this turn

- **Merged** [PR #208](https://github.com/Math-Data-Justice-Collaborative/vecinita/pull/208) @`2c884bd` (main CI + deploy-preflight green)
- **S027-D34 CI split** @`11ef43a`: remote `pytest tests/unit` + coverage sticky PR comment; compose suites via local `make test-py` / `ci-push`
- **T120.1 red**: `test_uj075_multilingual_ask.py`, `test_uj076_embed_promote_report.py`, `test_f71_rebuild_tokenizer_stamps.py` (failing on `chunk_tokenizer_id` + tokenizer default)

## Next

1. Open M120 PR (evolve push does not trigger CI — needs PR event)
2. T120.2 — config/docs: default tokenizer id = embed pin
3. T120.3 / T120.3b — wire rebuild stamps + F36 embed-promote report

## Corpus

[Corpus: feature-list.md §F70] [Corpus: feature-list.md §F71] [Spec: ADR-048] [Spec: TC-232–241]
