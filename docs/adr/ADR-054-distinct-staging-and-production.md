# ADR-054: Distinct staging and production environments

**Status:** Accepted (EV-staging-do-supabase / F83)  
**Date:** 2026-08-28  
**Related:** ADR-002, ADR-007, ADR-010, ADR-049, ADR-050, ADR-026/027

## Context

ADR-049 recorded that a single deployed stack labeled “staging” was actually
**live/prod** (`env_role: staging_as_live`). Operators lacked a safe non-prod mirror.
EV-staging-do-supabase provisions a **second** environment that mirrors production
on DigitalOcean, Supabase, and a **separate Modal workspace**.

## Decision

1. **Two environments:** `staging` and `prod` (no `staging_as_live` once staging is healthy).
2. **Prod** = the pre-existing sole stack (DO apps/DB may still have legacy “staging”
   hostnames until a phased rename). Modal workspace **`vecinita`**. Supabase project
   ref currently `cfuvghdsuwactfeamtym`.
3. **Staging** = new resources:
   - DO App Platform: `vecinita-staging-*` (four apps) + Managed Postgres
     `vecinita-staging-db` in **nyc**
   - Supabase project display name **`vecinita-staging`** (separate project ref + secrets)
   - Modal workspace **`vecinita-staging`** (full app mirror; separate tokens/secrets)
4. **Parity:** Same deployable set as prod; ADR-007 still forbids `DATABASE_URL` on Modal.
5. **Staging data:** migrations + seed only by default; no live corpus clone without
   AskQuestion (`no-live-prod-corpus-push`).
6. **CD & merge gate (extends ADR-050):**
   - GitHub Environments: `staging` and `production`
   - Ruleset on `main`: require project CI **and** staging deploy + H1–H5 smoke for the
     PR tip SHA before merge
   - Prod CD remains post-merge on `main` into `production`
7. **Config:** `VECINITA_ENV` is `staging` \| `production` on the matching stack;
   `VECINITA_MODAL_WORKSPACE` selects Modal workspace (`vecinita` vs `vecinita-staging`).
8. **ADR-049:** Remains historical for the single-env era; operational use of
   `staging_as_live` ends when staging H1–H5 pass and docs point here.

## Consequences

- Double DO + Supabase + Modal cost for the pilot window.
- Deploy scripts and CI must accept workspace/env overlays (no hard-only `vecinita`).
- Skills/AskQuestions must resolve `env_role` before cutover.
- Modal staging provision uses Modal CLI **after** Spec→Build gate (session decision).

## Alternatives considered

| Alternative | Why not |
|-------------|---------|
| Share Modal workspace with env-prefixed secrets only | Operator required full Modal isolation |
| Rename current stack to staging and build new prod | Higher cutover risk; rejected at intake |
| Branch protection without staging smoke | Does not meet “staging passes before main” |

## References

- [Corpus: staging] [Corpus: deploy-integration] [Corpus: product] §F83  
- `docs/staging-runbook.md`, `docs/staging-secrets-matrix.md`  
- ADR-049, ADR-050
