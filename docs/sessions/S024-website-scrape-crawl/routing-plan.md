# Routing plan — S024-website-scrape-crawl (Standard)

| Stage | Required | Status | Mode | Notes |
|-------|----------|--------|------|-------|
| 00-context | yes | completed | scoped | Session open 2026-08-03; S024-D1–D4 |
| 16-evolve | orchestrator | in_progress | — | EV-022; Phase B → Gate B→C |
| 01-requirements | yes | completed | delta | RD-252–263; locks confirmed → 02 |
| 02-verify-plan | yes | completed | delta | Gate A→B PASS (S024-D34); [02 audit](./reports/02-verify-plan-audit.md) |
| 04-tech-plan | yes | completed* | delta | *TP locks + Phase 26 drafted; Gate B→C AskQuestion |
| 07-build | yes | pending | — | M108–M111 after Gate B→C |
| 08-verify-build | yes | pending | — | Per-milestone / cycle |
| 09-qa | yes | pending | — | Full QA |
| 10-e2e | yes | pending | — | API + admin UI journeys |
| 11-verify-impl | yes | pending | — | Per-Fn AC + UI preview |
| 12-verify-deploy | yes | pending | — | Deploy checklist |
| 13-deploy-smoke | yes | pending | — | H1–H5 + ingest/crawl smokes |

## Skipped

| Stage | Rationale |
|-------|-----------|
| 03-plan-tooling | No new Cursor rules/hooks expected at open |
| 05-verify-tech | Fold into 02 / 08 unless tech plan adds ambiguity |
| 06-tech-tooling | No new tooling install expected |
| 15-service-health | Optional at close |

## Preset

**Standard** = Lean (`01 → 02 → 10 → 13`) + `04 → 07 → 08 → 09 → 11 → 12`.

## Approved

User answers **2026-08-03**:
1. Approve Standard for epic #185
2. Close S023/EV-020 as done, then open this session
3. **S024-D35** — TP1–TP6 + JS-render A (Playwright) + trafilatura + ADR-045

## Next

**Gate B→C** on Phase 26 / ADR-045 → on PASS start
`@.cursor/skills/07-build/SKILL.md` (05/06 skipped).

## Ship targets

| Track | Target |
|-------|--------|
| **F59 / #69 scrape** | trafilatura; robots/politeness; Playwright JS-render; PDF via pypdf |
| **F60 / #71 crawl** | Seed → multi-page same-site; limits + job tree |
| **F61 / #70 tree UI** | Nested corpus browse + backend meta (no ChatRAG UI) |
