# Success-criteria evidence (019)

Templates and procedures: `sc-controlled-trial-runbook.md`. SC-003 questions: `CONTRIBUTING.md` (answer key: `sc-003-review-answer-key.md`).

## Implementation / automation baseline (supplements but does not replace SC-001 / SC-002)

| Item | Evidence |
|------|----------|
| Validator FR-009 categories | `apis/gateway/tests/contracts/test_ci_attestation_validate_contract.py` — subprocess coverage for `schema`, `staleness`, `incomplete_manifest`, `failed_check`, `io_or_parse`, and a passing valid pair |
| Committed gate files | `.ci/required-checks.json` (includes `make-ci` → `make ci` per FR-011) and `.ci/ci-attestation.json` regenerated via `scripts/ci/ci_attestation_generate.py` |
| Local parity | `make ci-attestation-validate` / `scripts/ci/ci_attestation_validate.py` exits 0 when run at repo root after a fresh attestation |

## SC-001 (seven controlled PR cases)

**Status:** Pending human execution. Complete the results table in `sc-controlled-trial-runbook.md`, then paste or link the filled table here.

## SC-002 (≥20 maintainer-certified attempts, ≥95% first-pass)

**Status:** Pending. Use the log template in `sc-controlled-trial-runbook.md`; summarize N, first-pass rate, and threshold here when complete.

## SC-004 (new manifest `id` without attestation → next job fails)

**Status:** Pending. Record run URLs or timestamps in the runbook SC-004 section, then link or paste here.

## SC-003 (three reviewers, five questions, ≥4/5 each)

**Status:** Pending. Record reviewer identities (or anonymized ids), scores, and average here after documentation review.
