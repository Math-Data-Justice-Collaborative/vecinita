# HANDOFF — S026 / EV-024

| Field | Value |
|-------|--------|
| Session | S026-frontend-ux-polish |
| Cycle | EV-024 — ChatRAG + Admin UX polish (F64–F69) |
| Branch | `evolve/EV-024-frontend-ux-polish` |
| Stage | 07-build **M118 complete** — Gate C→D pending |
| Milestone | **M118** OpenAPI + UJ e2e + Phase 27 gate — T118.3 done |
| Head | (T118.3 commit after this handoff) |
| Main tip | `eb65837` (M117 #206) |

## Merged

| PR | Milestone | Merge |
|----|-----------|-------|
| #200 | M112 ActionIcon (#104) | merged |
| #202 | M113 Tooltip (#106) | merged |
| #203 | M114 cold-start tips (#87) | merged @ `f3f7dec` |
| #205 | M115+M116 energy + feedback (#93/#186) | merged @ `0c1d838` |
| #206 | M117 actor email (#170) | merged @ `eb65837` |

## Open / next

- **M118 PR:** OpenAPI + secrets matrix + Phase 27 gate docs (T118.1–T118.3) — create/merge next
- **Gate C→D** AskQuestion → 08-verify-build (M118 tip) → 09-qa → 10-e2e → …
- **Issues:** #87 CLOSED; #104/#106/#93/#186/#170/#193 still OPEN — close per [t118-3](./reports/t118-3-phase-27-gate.md) after smoke / secret sync
- **Ops:** no local `prod.env` — sync `SUPABASE_SECRET_KEY` when available

## Local notes

- Vitest: use **Node 24** (`nvm use 24`); Node 26 breaks jsdom `localStorage`
- Local API e2e Postgres: Colima volume perms fail; rely on GitHub CI

## Reports

- [t118-1 UJ suite](./reports/t118-1-uj-suite.md)
- [t118-3 Phase 27 gate](./reports/t118-3-phase-27-gate.md)
- [verification M117](./reports/verification-report.md)
