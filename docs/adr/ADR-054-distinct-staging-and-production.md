# ADR-054: Distinct staging and production environments

**Status:** Accepted (EV-staging-do-supabase / F83) — amended 2026-08-28 (Modal Environments)  
**Date:** 2026-08-28  
**Related:** ADR-002, ADR-007, ADR-010, ADR-049, ADR-050, ADR-026/027

## Context

ADR-049 recorded that a single deployed stack labeled “staging” was actually
**live/prod** (`env_role: staging_as_live`). Operators lacked a safe non-prod mirror.
EV-staging-do-supabase provisions a **second** environment that mirrors production
on DigitalOcean, Supabase, and Modal.

## Decision

1. **Two environments:** `staging` and `prod` (no `staging_as_live` once staging is healthy).
2. **Prod** = the pre-existing sole stack (DO apps/DB may still have legacy “staging”
   hostnames until a phased rename). Modal workspace **`vecinita`**, Modal Environment
   **`main`** (empty web suffix). Supabase project ref currently `cfuvghdsuwactfeamtym`.
3. **Staging** = new resources:
   - DO App Platform: `vecinita-staging-*` (four apps) + Managed Postgres
     `vecinita-staging-db` in **nyc**
   - Supabase project display name **`vecinita-staging`** (separate project ref + secrets)
   - Modal: **same workspace `vecinita`**, Modal Environment **`staging`** with web
     suffix **`staging`** (native Environments — not a second workspace). Same app
     names; secrets/volumes isolated per Environment. Deploy via
     `modal deploy --env staging` / `MODAL_ENVIRONMENT=staging`.
4. **Parity:** Same deployable set as prod; ADR-007 still forbids `DATABASE_URL` on Modal.
5. **Staging data:** migrations + seed only by default; no live corpus clone without
   AskQuestion (`no-live-prod-corpus-push`).
6. **CD & merge gate (extends ADR-050):**
   - GitHub Environments: `staging` and `production`
   - Ruleset on `main`: require project CI **and** staging deploy + H1–H5 smoke for the
     PR tip SHA before merge
   - Prod CD remains post-merge on `main` into `production`
7. **Config:** `VECINITA_ENV` is `staging` \| `production` on the matching stack;
   `VECINITA_MODAL_WORKSPACE` stays **`vecinita`** for both; `MODAL_ENVIRONMENT` is
   `main` (prod) or `staging`. Staging web URLs use source prefix
   `vecinita-staging--` (workspace + env web suffix).
8. **ADR-049:** Remains historical for the single-env era; operational use of
   `staging_as_live` ends when staging H1–H5 pass and docs point here.

## Consequences

- Double DO + Supabase cost; Modal GPU cost for a second Environment deploy (scale-to-zero).
- One Modal token (workspace `vecinita`) can deploy both Environments; secrets stay
  Environment-scoped (do not cross-wire staging secrets into `main`).
- Deploy scripts pass `--env` / `MODAL_ENVIRONMENT`; do not create workspace
  `vecinita-staging`.
- Skills/AskQuestions must resolve `env_role` before cutover.

### Cost notes (operator 2026-08-28)

| Layer | Shared today? | Cheaper merge option | Risk |
|-------|---------------|----------------------|------|
| Modal | **Yes** — one workspace, Environments `main` / `staging` | Already optimal | Low |
| DO Postgres | **No** — separate managed clusters | One cluster, two logical DBs (`prod` / `staging`) | Shared blast radius, noisy neighbor, harder firewall; not default |
| Supabase Auth | **No** — separate projects | Keep separate (free tier OK for staging) | Shared JWT/users if merged — rejected |

Do **not** put staging and prod corpus on the same logical database. Immediate savings without
architecture change: destroy unused orphan clusters (e.g. leftover `vecinita-staging` if not
referenced) after AskQuestion confirm.

## Alternatives considered

| Alternative | Why not |
|-------------|---------|
| Separate Modal workspace `vecinita-staging` | Extra auth/tokens; operator chose native Environments instead (EV-STG-D1 amend) |
| Share Environment with env-prefixed secret names only | No deploy isolation; Environments give native secret/volume/app isolation |
| Rename current stack to staging and build new prod | Higher cutover risk; rejected at intake |
| Branch protection without staging smoke | Does not meet “staging passes before main” |
| One DO Postgres cluster for both envs (two DBs) | Possible cost cut; deferred — isolation preferred until AskQuestion (EV-STG-D7) |
| One Supabase project for staging+prod Auth | Same user pool / JWT issuer — unsafe |

## References

- [Corpus: staging] [Corpus: deploy-integration] [Corpus: product] §F83  
- [Modal Environments](https://modal.com/docs/guide/environments)  
- `docs/staging-runbook.md`, `docs/staging-secrets-matrix.md`  
- ADR-049, ADR-050
