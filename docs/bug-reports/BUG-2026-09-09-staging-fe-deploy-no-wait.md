# BUG-2026-09-09-staging-fe-deploy-no-wait

[Corpus: staging] [Corpus: tests]
[Spec: docs/adr/ADR-054-distinct-staging-and-production.md]

## Error description

Staging Deploy starts DigitalOcean frontend deployments and returns while phase is
still `PENDING_BUILD`. Staging smoke then passes against **stale** FE bundles, so
operators never see staging environment banners / UX-1…UX-4 from merged `stage`
commits (#369/#370) until a later build finishes (or never, if builds fail silently).

## Error logs

```
==> Deploying vecinita-staging-chat-fe
Deployment started for vecinita-staging-chat-fe: deployment_id=… phase=PENDING_BUILD
==> Deploying vecinita-staging-admin-fe
Deployment started for vecinita-staging-admin-fe: deployment_id=… phase=PENDING_BUILD
# staging-smoke begins ~10s later
```

Live FE JS (2026-09-09): no `environment-banner` / `envBanner` strings.

## Investigation

1. Confirmed `cmd_deploy` in `scripts/deploy/do_apps.py` did not poll for ACTIVE.
2. Browser probe: chat + admin `hasStagingText=false`, no `[data-testid=environment-banner]`.
3. Source on `stage` includes EnvironmentBanner; live bundles do not.

## Repro / regression test

- `tests/unit/scripts/test_do_apps_wait_deployment.py`
- `tests/smoke/test_staging_fe_environment_banner.py` (env-gated live)

## Fix

- `do_apps.py deploy --wait` polls until ACTIVE / ERROR
- `.github/workflows/deploy-staging.yml` uses `--wait --timeout-s 900`; job timeout 45m

## Status

**fixed in branch** `feat/staging-responsive-ux-regressions` (pending PR → `stage`)
