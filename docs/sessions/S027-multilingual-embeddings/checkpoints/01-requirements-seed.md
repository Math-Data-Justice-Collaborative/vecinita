# 01-requirements seed — S027 / EV-025 (#159)

Seed for Stage 01 after Phase 0 Fn gate. Do not treat as approved scope until gate passes.

## Problem

Prod dense retrieval uses English-only `BAAI/bge-small-en-v1.5` (ADR-008). ADR-013 assumes
fair bilingual retrieval; Spanish chunks are structurally under-served.

## Approved intake (S027-D1–D8)

See [session-brief.md](../session-brief.md).

## Proposed features (pending gate)

| Fn | Title | Maps to |
|----|-------|---------|
| **F70** | Multilingual embedding runtime + model pin | Modal embed app, `embedding-client`, ADR-008 successor; prefer E1; ST/ONNX fallback (D7) |
| **F71** | Corpus re-embed + prod cutover | F41 rebuild with new `embedding_model_id`; promote; F36/dense EN vs ES evidence (D3, D5) |

## Spec / ADR touch list (expected)

- `docs/feature-list.md` — F70, F71
- `docs/spec.md` / `docs/api-contract.md` — embed model pin surface
- `docs/adr/ADR-008-*.md` — successor or amend
- `docs/adr/ADR-013-*.md` — language filter interaction note
- `docs/test-plan.md` / `docs/acceptance-criteria.md` — EN/ES retrieval AC
- `docs/dependency-inventory.md` — if ST/ONNX deps added
- F41 feature notes — remove “multilingual model pick OOS” once in-cycle

## Prior evidence to load in 01

- `docs/sessions/S019-retrieval-quality/reports/spike-multilingual-embed.md`
- Shadow rebuild `1fa1dec9…` (E1, not promoted)
- Scripts under `docs/sessions/S019-retrieval-quality/scripts/`

## Open risks for 01 interview (resolved in S027-D11–D23)

1. ~~Prod cutover with minimal staging (D5)~~ → **D21** staging-then-prod; **D11** operator judgment (no hard abort metrics)
2. ~~FastEmbed vs ST~~ → **D12** FastEmbed first, ST/ONNX fallback
3. ~~e5 prefixes~~ → **D13** enforced in shared client
4. Tokenizer align deferred (**D15**)
5. F44 tune only if post-pin harm; fold into F71 (**D19/D20**)
