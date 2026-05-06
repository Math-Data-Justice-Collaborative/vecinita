# CI attestation gate (committed JSON)

This directory holds the **required-check manifest** and **local test attestation** used by the merge gate described in [`specs/019-contract-ci-json-gate/spec.md`](../specs/019-contract-ci-json-gate/spec.md).

| File | Role |
|------|------|
| `required-checks.json` | Authoritative list of merge-blocking checks (`id`, `title`, `command`). |
| `ci-attestation.json` | JSON emitted by the local workflow: per-check outcomes with command output details, `run_id`, `generated_at`, `git_head`. |

## Trust boundary (Option A)

Merge eligibility for these checks is proven **locally** and recorded in `ci-attestation.json`. The single GitHub Actions gate job **validates only these committed files**; it does not re-run `make ci` on hosted runners. See the spec **Edge Cases** and **SC-005** for accepted risks (fork PRs, environment drift, bad-faith or mistaken claims) and optional mitigations.

## Regenerate

From the repository root (after `Makefile` targets exist):

```bash
make ci-attestation
make ci-attestation-validate
```

See [`specs/019-contract-ci-json-gate/quickstart.md`](../specs/019-contract-ci-json-gate/quickstart.md).
