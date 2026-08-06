# HANDOFF — S028-chat-source-ux

**Updated:** 2026-08-06  
**Stage:** 12-verify-deploy **completed** → next **13-deploy-smoke** (AskQuestion)  
**Branch:** `evolve/EV-026-chat-source-ux`  
**Tip:** `bbff787`  
**Cycle:** EV-026 · F72 / F73 / F74  
**env_role:** `staging_as_live` (live = prod)

## Status

- 11 PASS; #222–#224 closed
- **12 ready** (S028-D34): GHA outage → local parity + CLI deploy
- Local: pytest 1765; Vitest 190+740; FE builds PASS; DM coverage fail = QA-S028-004 accepted
- Live stack still @ `c942971` until CLI redeploy

## Next

1. **AskQuestion** → start **13-deploy-smoke** (CLI: alembic → write → chat BE → FEs → H4–H5)
2. Need `prod.env` sourced for secrets / doctl

## Links

- [deploy-checklist](./reports/deploy-checklist.md)
- [verify-impl](./reports/verify-impl.md)
