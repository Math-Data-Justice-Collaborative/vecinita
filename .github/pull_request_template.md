## Summary

<!-- What changed and why (required). -->

## Type of change

- [ ] Bug fix (non-breaking change which fixes an issue)
- [ ] New feature (non-breaking change which adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to change)
- [ ] Documentation only
- [ ] Chore / tooling / CI

## Checklist

### All submissions

- [ ] I have read the contributing guidelines and project rules in `.cursor/rules/`
- [ ] I checked there are no other open PRs for the same update
- [ ] My code follows this repo's style (ruff, basedpyright, ESLint strict)
- [ ] I did not commit secrets, `.env` files, or operator spec exports (`*-spec.yaml` at repo root)

### Features and fixes

- [ ] I added or updated tests for my changes
- [ ] Tests cover the changed behavior (including edge cases where relevant)
- [ ] All new and existing tests pass locally
- [ ] CI (`ci.yml`) is green on this branch

### Documentation and issues

- [ ] I updated documentation when behavior or APIs changed
- [ ] This PR links issues with `Closes #` or `Fixes #` where applicable

### Deploy / connectivity (check if applicable)

- [ ] Frontend: `VITE_*` env wiring verified (H5)
- [ ] API/CORS: connectivity checks considered (H4)
- [ ] OpenAPI specs updated if API contract changed
- [ ] Database migrations included if schema changed

## Test plan

<!-- How reviewers can verify this PR. -->

## Reviewer notes

<!-- Optional context for reviewers. -->
