# HANDOFF — S024-website-scrape-crawl

> ADR-043 rolling digest · overwrite at safe-stops  
> **Updated:** 2026-08-03 — 12 COMPLETE (S024-D47 Decision A); start 13-deploy-smoke

| Field | Value |
|-------|--------|
| Session | `S024-website-scrape-crawl` **in_progress** |
| Evolve | `EV-022` — F59/F60/F61 |
| Branch | `evolve/EV-022-website-scrape-crawl` |
| Stage / action | **13-deploy-smoke** — merge/deploy Path A + H1–H5 |
| Issues | #185 · #69 → #71 → #70 |

## Progress

- 11-verify-impl **COMPLETE** (S024-D46)
- 12-verify-deploy **COMPLETE** (S024-D47) — mitigations + rollback + JS Decision A
- Checklist: `reports/deploy-checklist.md` · standing `docs/deploy-checklist.md`

## Next

1. Open/merge PR (or confirm tip) → Path A redeploy (Alembic + Modal DM + write + Admin FE)
2. H1–H3 → `verify_connectivity.sh` H4–H5 → optional live crawl smoke
3. Write `reports/deploy-smoke.md`; close EV-022
