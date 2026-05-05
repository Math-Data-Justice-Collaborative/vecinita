# SC-001 / SC-002 / SC-004 controlled trial runbook

Templates for success-criteria evidence (`spec.md` **SC-001**, **SC-002**, **SC-004**). Fill rows during rollout; link completed tables from `sc-success-criteria-evidence.md` (**T018**).

## SC-001 — Seven synthetic PR cases (letters a–g)

| Case | Branch / PR | Setup (manifest / attestation) | Expected gate | Actual | Notes |
|------|-------------|--------------------------------|---------------|--------|-------|
| (a) Missing attestation | | Valid manifest; remove or omit `.ci/ci-attestation.json` | Fail | | |
| (b) Missing manifest | | Valid attestation; remove or omit `.ci/required-checks.json` | Fail | | |
| (c) Invalid manifest | | Use e.g. duplicate `id` or `checks: []` | Fail | | |
| (d) Invalid attestation | | Valid manifest; non-UTF-8 or schema-breaking JSON | Fail | | |
| (e) Stale | | Valid pair; set `generated_at` older than max age | Fail | | |
| (f) Incomplete / failed | | Omit a manifest `id` or set a check to `failed` | Fail | | |
| (g) Valid pair | | Regenerate with `make ci-attestation` after a clean `make ci` | Pass | | |

## SC-002 — Maintainer-certified regeneration log (≥20 attempts)

| # | Date | PR / branch | Maintainer attests full regen steps in order | First validation pass? | Notes |
|---|------|-------------|-----------------------------------------------|-------------------------|-------|
| 1 | | | | | |
| … | | | | | |

Target: ≥ **95%** first-attempt pass across ≥ **20** rows.

## SC-004 — Manifest adds a new `id`

1. Add a new check to `.ci/required-checks.json` on a test branch; **do not** regenerate attestation.
2. Push → next run of **attestation-gate** must **fail**.
3. Run `make ci-attestation`, commit refreshed `.ci/ci-attestation.json` → next run **passes**.

| Step | Timestamp / run URL | Outcome |
|------|----------------------|---------|
| Push without new attestation | | Fail |
| Push with fresh attestation | | Pass |
