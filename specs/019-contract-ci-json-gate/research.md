# Research: Contract-based CI attestation (019-contract-ci-json-gate)

## R-001 — Validator implementation

**Decision**: Implement the attestation validator as a **Python 3** script under `scripts/ci/` (e.g. `ci_attestation_validate.py`), invoked from a single GitHub Actions job and from `make` for local parity.

**Rationale**: Matches existing `scripts/ci/impacted_corpus_test_suites.py` style; easy JSON and time parsing; contributors already use `uv`/Python for backend CI.

**Alternatives considered**: Pure Node (rejected: splits tooling surface); `jq` + shell only (rejected: schema and error messages get unwieldy for FR-009).

## R-002 — JSON Schema validation library

**Decision**: Use **stdlib-only validation** for v1 (required keys, types, ISO-8601 parse, manifest id set equality) unless tasks explicitly add `jsonschema` as a dev dependency with lockfile updates.

**Rationale**: Keeps the gate job minimal and avoids dependency drift for a small file format.

**Alternatives considered**: `jsonschema` + pinned schema (preferred if format grows; defer to follow-up).

## R-003 — Committed file paths

**Decision**: Store **manifest** at `.ci/required-checks.json` and **attestation** at `.ci/ci-attestation.json` (both at repo root).

**Rationale**: Clear separation; `.ci/` is a conventional prefix for CI-only artifacts; easy to document and `.gitignore` nothing (both committed).

**Alternatives considered**: `artifacts/` (rejected: often gitignored in other repos); `specs/019-.../` (rejected: attestation is operational, not spec prose).

## R-004 — Freshness default

**Decision**: Default maximum attestation age **48 hours** wall clock relative to GitHub Actions runner UTC at validation time, overridable via workflow input or env (e.g. `CI_ATTESTATION_MAX_AGE_HOURS`).

**Rationale**: Balances “must rerun before merge” vs contributor friction; spec requires configurability (FR-006).

**Alternatives considered**: 24h (stricter); tied to commit author date (rejected: conflates code age with evidence age).

## R-005 — Run identifier

**Decision**: `run_id` is a **UUID v4** generated at attestation creation time; optional second field `git_head` (abbrev SHA) for human correlation.

**Rationale**: Satisfies FR-002 uniqueness without requiring network; correlates with local tree when present.

## R-006 — Partial reruns vs full suite

**Decision**: **Full-suite attestation only** for v1: the local generator always runs the complete manifest (including `make ci`) in one shot; no merge of partial results.

**Rationale**: Spec edge case “project picks one approach”—simplest to implement and to explain; avoids ambiguous merged state.

**Alternatives considered**: Incremental attestation merge (deferred: higher tamper and UX complexity).

## R-007 — Migration from current GitHub workflows

**Decision**: Implementation tasks will (a) add manifest + generator + validator + one workflow; (b) **reconfigure branch protection / required checks** to require only the new gate job for merge (per product owner); (c) **demote or remove** redundant hosted jobs from **required** status—not necessarily delete workflows if teams want advisory runs.

**Rationale**: Spec FR-010 forbids hosted re-execution as merge requirement for manifest checks; branch protection must align or the feature is incomplete.

**Alternatives considered**: Keep all current jobs required **and** attestation (rejected: contradicts clarified Option A intent).

## R-008 — Constitution alignment (`make ci`)

**Decision**: Manifest **must** contain a stable id (e.g. `make-ci`) whose command is `make ci` at repo root, documented as the constitutional merge-ready bar.

**Rationale**: Constitution IV explicitly references `make ci`; attestation replaces hosted repetition, not the bar itself.
