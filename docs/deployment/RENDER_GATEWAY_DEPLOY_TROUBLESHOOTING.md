# Render Gateway Deploy Troubleshooting Loop

Scope for this runbook:
- vecinita-gateway (production)
- vecinita-gateway-staging (staging)

Goal:
- Keep gateway deploys on Docker runtime.
- Prevent native Python buildpack fallback paths that trigger Rust compilation failures.

## Known Failure Signature

When runtime drifts to non-Docker/native, builds may fail with this pattern:
- pip attempts to build py-rust-stemmers from source
- maturin/cargo write into read-only filesystem
- build ends with metadata-generation-failed for py-rust-stemmers

## Preflight

1. Confirm gateway runtime in Render Dashboard is Docker for both environments.
2. Confirm Render service IDs are set as GitHub secrets:
- RENDER_STAGING_GATEWAY_SERVICE_ID
- RENDER_GATEWAY_SERVICE_ID
3. Confirm Render API key secret exists:
- RENDER_API_KEY

## Automated Guardrail

This repository validates gateway runtime before staging and production deploy triggers in:
- .github/workflows/render-deploy.yml

Validation script:
- scripts/github/validate_render_runtime.py

Dependency profile validation script:
- scripts/github/validate_gateway_dependency_profile.py

Native Python runtime fallback pin:
- runtime.txt (python-3.13.2)

Manual usage:

python3 scripts/github/validate_render_runtime.py --service-id <srv-id> --service-name vecinita-gateway --expect docker

python3 scripts/github/validate_gateway_dependency_profile.py

## One-Command Iteration Execution

Use the iteration runner to execute: validate runtime -> trigger deploy -> wait for live -> smoke checks.

Script:
- scripts/github/run_gateway_deploy_iteration.sh

Examples:

bash scripts/github/run_gateway_deploy_iteration.sh staging

bash scripts/github/run_gateway_deploy_iteration.sh production

## Iteration Loop (Staging First)

Use this sequence for each troubleshooting cycle.

1. Form one hypothesis.
- Example: runtime drifted to native buildpack.

2. Apply one minimal change.
- Example: set runtime back to Docker and verify Dockerfile path.

3. Trigger staging deploy.

4. Evaluate staging outcomes.
- Build phase must not show native pip/maturin/cargo compilation path.
- /health must return 200.
- Representative gateway endpoint must return success.

5. Promote to production only if staging is green.

6. Record evidence.
- Deploy ID, timestamp, change applied, pass/fail, next hypothesis.

Stop after two consecutive successful cycles in both environments.

## Escalation Path

If unresolved after 3 cycles:
1. Audit runtime ownership and remove manual dashboard drift.
2. Verify gateway install profile does not include scraper-heavy extras.
3. Add explicit non-Docker fallback controls if native runtime is ever intentionally reintroduced.

## Recovery Checklist

- [ ] Staging runtime validated as Docker.
- [ ] Staging deploy completed successfully.
- [ ] Staging health and representative endpoint checks passed.
- [ ] Production runtime validated as Docker.
- [ ] Production deploy completed successfully.
- [ ] Production health and representative endpoint checks passed.
- [ ] Evidence logged for all cycles.
