# Routing plan — S024-website-scrape-crawl (Standard)

| Stage | Required | Status | Mode | Notes |
|-------|----------|--------|------|-------|
| 00-context | yes | completed | scoped | Session open 2026-08-03; S024-D1–D4 |
| 16-evolve | orchestrator | in_progress | — | EV-022; 12-verify-deploy |
| 01-requirements | yes | completed | delta | RD-252–263 |
| 02-verify-plan | yes | completed | delta | Gate A→B PASS (S024-D34) |
| 04-tech-plan | yes | completed | delta | TP1–TP6 + ADR-045 (S024-D35/D37) |
| 07-build | yes | completed | — | M108–M111 (T111.3 S024-D41) |
| 08-verify-build | yes | completed | — | PASS — verification-report |
| 09-qa | yes | completed | — | pass_with_advisories |
| 10-e2e | yes | completed | — | T0 PASS; TC-204 CI-gated |
| 11-verify-impl | yes | completed | — | S024-D46 Approve all — verify-impl.md |
| 12-verify-deploy | yes | completed | — | S024-D47 approved — deploy-checklist.md |
| 13-deploy-smoke | yes | completed | — | Path A CD + H1/H3/H4/H5; report deploy-smoke.md |

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

**13-deploy-smoke** — Path A merge/deploy + H1–H5 (+ optional live crawl per S024-D24)

## Ship targets

| Track | Target |
|-------|--------|
| **F59 / #69 scrape** | trafilatura; robots/politeness; Playwright JS-render; PDF via pypdf |
| **F60 / #71 crawl** | Seed → multi-page same-site; limits + job tree |
| **F61 / #70 tree UI** | Nested corpus browse + backend meta (no ChatRAG UI) |
