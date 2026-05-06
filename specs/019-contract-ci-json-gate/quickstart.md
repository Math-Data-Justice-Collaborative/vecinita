# Quickstart: CI attestation gate (019-contract-ci-json-gate)

## Prerequisites

- Repo cloned; tooling sufficient to run `make ci` locally (see root `README.md` / `TESTING_DOCUMENTATION.md`).
- Python 3 on PATH (same as other `scripts/ci` usage).

## One-time understanding

1. Read [spec.md](./spec.md) — especially **Clarifications (Option A)** and **Edge Cases** (trust boundary).
2. Read manifest contract: [contracts/required-checks-manifest.md](./contracts/required-checks-manifest.md).
3. Read attestation schema: [contracts/ci-attestation.schema.json](./contracts/ci-attestation.schema.json).

## Produce a fresh attestation (local)

From the **repository root**:

```bash
make ci-attestation
```

This reads `.ci/required-checks.json`, runs each manifest `command` (including `make ci`), and writes `.ci/ci-attestation.json` with `format_version`, UUID v4 `run_id`, UTC ISO-8601 `generated_at`, current commit `git_head`, and per-check `status`.

Commit **both** `.ci/required-checks.json` (when changed) and `.ci/ci-attestation.json` with your PR.

## Validate locally before push

```bash
make ci-attestation-validate
```

Equivalent:

```bash
python3 scripts/ci/ci_attestation_validate.py \
  --manifest .ci/required-checks.json \
  --attestation .ci/ci-attestation.json \
  --max-age-hours 48
```

Override max age (hours) via `CI_ATTESTATION_MAX_AGE_HOURS` or `--max-age-hours`.

## CI behavior

- Pull requests and pushes to `main` / `develop` run workflow **`.github/workflows/ci-attestation-gate.yml`**, job **`attestation-gate`**, which executes `scripts/ci/ci_attestation_validate.py` against the **committed** `.ci/required-checks.json` and `.ci/ci-attestation.json` only (no hosted re-run of manifest commands).
- If either file is missing, malformed, stale, or any required check is not `passed`, the job fails with stderr containing an **FR-009** primary category (`missing_file`, `io_or_parse`, `schema`, `staleness`, `incomplete_manifest`, `failed_check`) and `[manifest]` / `[attestation]` scope.
- Staleness includes both age window validation and `git_head` parity with the branch tip being validated.

## Manual max-age override (optional)

Repository maintainers may run **Actions → CI attestation gate → Run workflow** and set `max_age_hours` (see workflow `workflow_dispatch` inputs).

## Changing required checks

1. Edit `.ci/required-checks.json` in a dedicated PR or alongside feature work.
2. Regenerate `.ci/ci-attestation.json` with `make ci-attestation` so every manifest `id` is `passed`.
3. Align GitHub branch protection with `artifacts/branch-protection-checklist.md` (single required check for this gate per **FR-004**).
