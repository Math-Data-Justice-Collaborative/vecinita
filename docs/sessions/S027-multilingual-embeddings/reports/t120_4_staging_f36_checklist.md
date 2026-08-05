# T120.4 — Staging shadow → F36 → promote checklist

**Session:** S027-multilingual-embeddings · **Cycle:** EV-025 · **Feature:** F71

Standing runbook: [docs/staging-runbook.md](../../../staging-runbook.md) §Shadow rebuild checklist
(updated 2026-08-05 for T120.3/T120.3b report endpoint + Alembic `20260805_0013`).

## Operator steps (staging)

1. Modal embed serves F70 pin @ 384-d
2. Rebuild `mode=rechunk` `dry_run=true` with matching embed + tokenizer stamps
3. Alembic includes `chunk_tokenizer_id` columns
4. F36 on shadow with EN/ES Hy1 vs E0 (+ dense when available)
5. `GET .../embed-promote-report` — review advisory columns (AC-ME3–ME4)
6. Operator promote (S027-D11); E0 revision retained (S027-D22)
7. Prod cutover only after staging (M121 / TC-240)

## Corpus cites

- [Corpus: feature-list.md §F71]
- [Spec: docs/acceptance-criteria.md §AC-ME3–ME4]
- [Spec: docs/test-plan.md §TC-235–236]
- [Spec: docs/user-journeys.md §UJ-076]
