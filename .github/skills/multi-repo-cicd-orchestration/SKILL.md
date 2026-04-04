---
name: multi-repo-cicd-orchestration
description: 'Apply the canonical multi-repo deployment mapping, verify service boundaries, and update orchestrator workflows/docs for Render and Modal deployments.'
argument-hint: 'Describe the service/repo change, deployment target, and required CI/CD updates.'
user-invocable: true
disable-model-invocation: false
---

# Multi-Repo CI/CD Orchestration

Use this skill when changing deployment wiring, repo mapping, or cross-repo release automation.

## Canonical Mapping

- chat frontend -> Render frontend
- data-management frontend -> Render frontend
- data-management API -> Render private service in Virginia
- direct-routing -> Render private service in Virginia
- scraper -> Modal deploy
- embedding-modal -> Modal deploy
- model-modal -> Modal deploy

## Required Checks

1. Preserve private-network boundaries:
- data-management frontend -> data-management API directly
- agent backend and data-management API -> direct-routing for model/embedding/scraper

2. Preserve CI/CD ownership model:
- each service repo owns tests + deploy workflow
- root repo only orchestrates via dispatch workflow

3. Enforce quality gates:
- backend changes: run relevant pytest targets
- frontend changes: run relevant vitest/playwright targets
- deployment workflow changes: validate YAML and run dry-run dispatch where possible

## Files to Update in This Repo

- .github/workflows/multi-repo-release-orchestrator.yml
- .github/workflows/reusable-dispatch-repo-workflow.yml
- docs/deployment/MULTI_REPO_CICD_ORCHESTRATION.md
- .github/copilot-instructions.md

## Guardrails

- Do not hardcode production credentials.
- Do not remove private-service constraints for data-management API or direct-routing.
- Keep Virginia requirement explicit for Render private services in docs/policies.
