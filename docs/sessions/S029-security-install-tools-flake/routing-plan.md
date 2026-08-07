# Routing plan — S029-security-install-tools-flake (hotfix preset)

Approved: 14-hotfix Phase 0 (`confirm_hotfix_plan` → Proceed).

| Stage | Required | Status | Notes |
|-------|----------|--------|-------|
| 14-hotfix | yes | in_progress | Phase 0 complete → repro RED → fix → PR |
| 15-service-health | no | pending | Optional; skip unless main CI needs live follow-up |

## Orchestrator

**14-hotfix** — one bug, one repro, one fix.

## Next

Phase 1.25 — failing repro for GitHub API transient failure → user confirms → harden script.
