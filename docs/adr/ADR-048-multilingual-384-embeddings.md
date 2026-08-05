# ADR-048: Multilingual 384-d embeddings (ADR-008 successor)

**Status:** Accepted  
**Stage:** 07-build / M122 (EV-025 / S027) — implemented M119–M121; Phase 28 docs gate  
**Date:** 2026-08-05  
**Supersedes:** [ADR-008](ADR-008-fastembed-384-modal.md)  
**Related:** ADR-005 (pgvector 384), ADR-009 (self-hosted), ADR-013 (bilingual), ADR-040 (F41 rebuild),
ADR-044 (chunk tokenizer — **aligned to embed pin in EV-025**), F10/F70–F71, GitHub #159, S027-D1–D40

### Stage metadata (T122.2)

| Field | Value |
|-------|-------|
| Accepted | 01-requirements / 02-verify-plan (S027-D1–D25) |
| Implemented | 07-build M119–M121 (runtime + staging + prod runbook) |
| Gate docs | M122 (this milestone) |
| Live cutover smoke | **13-deploy-smoke** (H4–H5) — not claimed at 07 |

## Context

Prod dense retrieval is pinned to English-only `BAAI/bge-small-en-v1.5` (ADR-008 / F10).
ADR-013 assumes fair bilingual retrieval; Spanish chunks are under-served by an EN-centric
embedder. S019 spiked E0 vs E1 (`intfloat/multilingual-e5-small`) vs E2; E1 improved rank
signals; FastEmbed 0.4–0.6 could not load E1. Issue #159 + S027 intake expand from
investigation-only to **implement + staging-then-prod cutover** (S027-D5/D21).

Dimension must remain **384** (no dual-index, no dim migration this cycle — S027-D6).

## Decision

1. **Dimension:** Keep **384-d** pgvector columns (ADR-005 unchanged).
2. **Model:** Planned candidate **E1** `intfloat/multilingual-e5-small`. Final prod pin is
   chosen only after F36 operator review (S027-D11/D14) — not a hard numeric gate.
3. **Runtime:** Prefer **FastEmbed** on Modal; if the winner cannot load, allow
   **sentence-transformers** or **custom ONNX** on the Modal embedding app (S027-D7/D12).
   No hard $/latency budget; overnight re-embed OK (S027-D23).
4. **Shared client:** Ingest and ChatRAG query use one `packages/embedding-client` pin.
   For e5-family models, enforce **`passage:`** on ingest/re-embed texts and **`query:`** on
   ask-path query texts (S027-D13).
5. **Corpus cutover (F71):** Staging first — F41 rebuild (rechunk + re-embed so tokenizer
   matches pin) dry-run shadow → F36 advisory report (EN/ES relevancy + faithfulness Hy1 vs E0
   baseline + dense hit@k/mean_rank when available) → operator promote; then **repeat on prod**
   (S027-D21). Keep prior **E0** revision restorable via F41 rollback runbook (S027-D22).
6. **Tokenizer:** Align `VECINITA_CHUNK_TOKENIZER_ID` with the embed pin and **rechunk** the
   corpus this cycle (S027-D15 amended by 02 M2b). Updates ADR-044 default to the chosen pin.
7. **F44:** May tune soft language filter **only if** post-pin F36 shows ES/lang-filter harm;
   folded into F71 (no F72) (S027-D19/D20).
8. **Out of scope:** Dual-index; dim≠384; UI changes; bge-m3 multi-vector; paid embed APIs.

## Consequences

- ADR-008 status → **Superseded by ADR-048** (FastEmbed-only assumption relaxed; pin may leave BGE-en).
- Changing pin still requires F41 re-embed; dim change would still need a new ADR + migration.
- Modal embedding app may gain ST/ONNX deps (license + inventory in 04/06).
- F42 Hy1 “on E0” ship notes become historical; post-cutover retrieval assumes F70 pin.

## Alternatives rejected

| Option | Why rejected |
|--------|----------------|
| Keep E0 forever | Leaves ADR-013 bilingual quality gap |
| Dual-index EN + multilingual | Explicitly OOS (S027-D6) |
| Dim change / bge-m3 variable | Schema migration OOS |
| Hard numeric promote gate | Operator judgment after F36 (S027-D11) |
| FastEmbed-only hard constraint | Would block E1 (S019); ST/ONNX allowed (S027-D7) |

## References

- S027/EV-025 decisions D1–D23; `docs/decisions/evolve-decisions.md`
- S019 spike: `docs/sessions/S019-retrieval-quality/reports/spike-multilingual-embed.md`
- F70, F71; F10; F41; F44
