# Copilot CI/CD Quality Hook

Use this checklist before submitting CI/CD topology changes.

## Topology and Isolation

- [ ] Mapping still matches canonical service ownership and deployment platform.
- [ ] Data Management API is a private Render service in Virginia.
- [ ] Data Management Frontend calls Data Management API directly.
- [ ] Agent backend and Data Management API route model/embedding/scraper calls directly to Modal endpoints.

## Workflow Quality

- [ ] Service-owned workflows are unchanged unless intentionally updated in those service repos.
- [ ] Root orchestrator only dispatches; it does not replace service test/deploy logic.
- [ ] Secrets are referenced via GitHub Secrets, never hardcoded.
- [ ] Failure mode is explicit when cross-repo token is missing or workflow file is wrong.

## Validation

- [ ] Backend contract tests pass for changed integration models.
- [ ] Frontend integration or unit tests pass for changed API contracts.
- [ ] Workflow YAML validates (actionlint or successful parsing in Actions UI).
