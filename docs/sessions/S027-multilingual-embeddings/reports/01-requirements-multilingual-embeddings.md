# 01-requirements report — S027 / EV-025 (#159)

**Date:** 2026-08-05  
**Status:** completed (delta)  
**Features:** F70, F71  
**Decisions:** S027-D1–D23; RD-290–RD-301; **ADR-048** (Proposed)

## Summary

Product requirements for multilingual 384-d embeddings: runtime + shared client pin (F70)
and staging-then-prod corpus cutover via F41 (F71). Builds on S019 E0/E1/E2 spike; expands
#159 from investigation-only to implement + cutover (user override), with staging full pass
before prod (D21 amends D5).

## Artifacts updated

| Doc | Delta |
|-----|--------|
| `docs/feature-list.md` | F70, F71; F41 OOS note |
| `docs/spec.md` | ChatRAG + ingest/rebuild embed pin (ADR-048) |
| `docs/config-spec.md` | `VECINITA_EMBEDDING_MODEL_ID`, `VECINITA_EMBED_RUNTIME`, `VECINITA_EMBED_E5_PREFIXES`; tokenizer defer note |
| `docs/user-journeys.md` | UJ-075, UJ-076 |
| `docs/test-plan.md` | TC-232–240 |
| `docs/acceptance-criteria.md` | AC-ME1–ME10 |
| `docs/decisions.md` | RD-290–RD-301 |
| `docs/adr/ADR-048-*.md` | New (supersedes ADR-008) |
| `docs/adr/ADR-008-*.md` | Status → Superseded |
| `docs/adr/README.md` | Index + deferred tokenizer align |
| `docs/decisions/evolve-decisions.md` | EV-025 scope + D1–D23 |

## Intake highlights

- Promote: **operator judgment** after F36 (no hard numeric gate)
- Runtime: FastEmbed first → ST/ONNX fallback
- Prefixes: e5 `query:` / `passage:` in shared client
- Cutover: staging shadow→F36→promote, then prod; E0 restorable
- F44: tune only if post-pin harm; fold into F71
- Tokenizer align: deferred

## Next

**02-verify-plan** — consistency pass across delta docs.
