# Feature Specification: Contract-based CI via local test attestation

**Feature Branch**: `019-contract-ci-json-gate`  
**Created**: 2026-05-04  
**Status**: Draft  
**Input**: User description: "Instead of the current CI testing we have, I want to make it contract based, so basically we write a JSON for local runs that will check to see if all of the required tests are passing, have it time-stamp IDed and if it's stale or old, then we fail, otherwise we pass if ALL are passing. One CI Job @GitHub Actions"

## Clarifications

### Session 2026-05-04

- **Q:** After this feature ships, how should required checks relate to hosted CI execution on pull requests? **→ A:** **Option A — Local-only proof.** Required checks are satisfied only through local runs recorded in the attestation; merge does **not** depend on hosted CI re-executing those same checks.

## Normative paths and serialization

- **Interchange format**: The attestation file MUST be **JSON** text on disk so contributors, reviewers, and the validator share one serialization; this aligns with plan and contract artifacts without prescribing tooling beyond “valid JSON.”
- **Canonical locations**: Until contributor guides absorb them, **canonical relative paths** for the committed manifest and attestation are defined in `specs/019-contract-ci-json-gate/plan.md` and `specs/019-contract-ci-json-gate/quickstart.md` (same paths in implementation). The spec otherwise refers to them as “the committed manifest” and “the committed attestation.”

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Developer produces a fresh attestation before pushing (Priority: P1)

A contributor runs the agreed local verification workflow before opening or updating a pull request. That workflow writes a structured attestation file that lists every required check by name (or stable identifier), marks each as passed or failed, and records when the run finished and a unique run identifier.

**Why this priority**: Without a correct, complete local attestation, the central gate cannot trust that required work was done.

**Independent Test**: Run the local workflow on a clean change where all required checks pass; confirm the attestation lists every required item as passed and includes a **UUID `run_id`** and **`generated_at` in UTC ISO-8601** per **FR-002** (suitable for **FR-006** freshness checks).

**Acceptance Scenarios**:

1. **Given** the repository defines a fixed set of required checks, **When** the contributor runs the local workflow and every required check passes, **Then** the generated attestation lists each required check as passed and includes a **UUID version 4 `run_id`** and **`generated_at` in UTC ISO-8601** per **FR-002** (suitable for **FR-006** freshness checks).
2. **Given** at least one required check fails locally, **When** the contributor runs the local workflow, **Then** every manifest `id` is still listed in `checks`, failed items use `status: failed`, no id is marked `passed` unless it passed, the workflow exits non-zero, and the documentation MUST NOT describe any alternate “partial success” attestation state for merge.

---

### User Story 2 - Central integration rejects invalid, stale, or incomplete gate files (manifest + attestation) (Priority: P1)

When a change is proposed, the single central integration job loads the **committed manifest and attestation** and **validates those files only** (it does not re-run the underlying manifest commands on hosted infrastructure). If either file is missing, fails validation per **FR-005** (including parse/encoding/shape failures for manifest or attestation), fails **FR-006** staleness, or fails **FR-007** completeness or pass status, the job fails and blocks merge. If both files satisfy FR-005 through FR-007, the job succeeds.

**Why this priority**: This is the core guarantee: outdated or partial evidence cannot substitute for a current, complete pass.

**Independent Test**: Provide branches where the **manifest**, the **attestation**, or both are missing, stale, incomplete, invalid JSON/shape, or fully valid; confirm the job fails for each negative case and passes only when **both** files satisfy FR-005 through FR-007.

**Acceptance Scenarios**:

1. **Given** no attestation file at the **canonical path** while the manifest is valid, **When** the central integration job runs, **Then** the job fails with a message indicating missing or invalid **attestation** evidence (FR-009 category appropriate to failure, e.g. `missing_file`).
2. **Given** no manifest file at the **canonical path** while the attestation is otherwise present, **When** the central integration job runs, **Then** the job fails with a message indicating missing or invalid **manifest** evidence (FR-009 category appropriate to failure, e.g. `missing_file`).
3. **Given** a manifest that is not valid UTF-8 JSON or does not match the documented manifest shape (e.g. duplicate `id` in `checks`), **When** the central integration job runs, **Then** the job fails with a message that identifies the **manifest** and an FR-009 category such as `io_or_parse` or `schema`.
4. **Given** a valid manifest and an attestation file that is not valid UTF-8 JSON, or that parses but **fails the active attestation schema** for its declared `format_version` (while the manifest remains valid), **When** the central integration job runs, **Then** the job fails with a message that identifies the **attestation** and an FR-009 category such as `io_or_parse` or `schema`.
5. **Given** an attestation whose generation time is outside the configured freshness window relative to the job’s clock, **When** the central integration job runs, **Then** the job fails with a message indicating stale evidence.
6. **Given** an attestation that is well-formed and fresh but omits one or more required checks or marks any required check as not passed, **When** the central integration job runs, **Then** the job fails.
7. **Given** a well-formed, fresh attestation and a valid manifest in which every required check is marked passed, **When** the central integration job runs, **Then** the job succeeds.

---

### User Story 3 - Maintainers evolve the required-check contract safely (Priority: P2)

Maintainers can add, rename, or retire required checks by updating a single authoritative contract (the manifest of required checks and rules) so that contributors and the central job agree on what “all passing” means.

**Why this priority**: The system must stay maintainable as the test suite grows; this is secondary to establishing the attestation and gate behavior.

**Independent Test**: Change the manifest to add a new required check; confirm local generation fails until that check is included and passing, and that CI enforces the updated list.

**Acceptance Scenarios**:

1. **Given** an updated manifest that adds a new required check, **When** a contributor uses an old local workflow that does not record the new check, **Then** the central job fails until tooling and attestations include the new requirement.

---

### Edge Cases

- **Clock skew**: Freshness is evaluated using the central job’s notion of time; contributors in skewed environments still fail if the attestation reads as too old when validated centrally.
- **Concurrent branches**: Each change under review carries its own **manifest and attestation**; the job validates those committed files bundled with that revision, not evidence from another branch.
- **Partial reruns**: Attestation generation for merge is **full-suite only**: each run MUST execute **every** manifest command and emit outcomes for every manifest `id`; partial reruns or stitched-together results are **out of scope** for a merge-valid attestation.
- **Tampering or manual edits (v1 integrity)**: Validation is **schema + completeness vs manifest + freshness + explicit per-id status** only; cryptographic signatures, Merkle proofs, or remote attestation are **out of scope** unless added in a future spec revision. Manual edits that contradict executed outcomes are discouraged and caught only insofar as they break schema, omit ids, or mismatch manifest commands on the next honest regeneration cycle—requirements do **not** claim cryptographic non-repudiation for v1.
- **Trust boundary vs hosted CI**: Because merge proof is local-only for manifest checks, contributors and reviewers accept that outcomes reflect **machines that ran the local workflow** (not a canonical hosted runner). Contributor documentation MUST explicitly list at least these **accepted risks**: **fork PRs** (untrusted contributors can push attestations generated on their machines), **environment drift** (local dependency skew vs another machine), and **bad-faith or mistaken attestation** (claims pass without running commands). Documentation MUST separately list **optional mitigations** (e.g., advisory hosted workflows, maintainer review policy) as non-merge-blocking unless promoted via manifest + FR-010 extension rules.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The project MUST maintain an authoritative **required-check manifest** listing every merge-blocking check with: a stable machine identifier (`id`), a human-readable `title`, and an invocable definition of the check (command or equivalent) from a documented working directory. **No shadow merge-blocking checks** are permitted for this gate: any check required for merge MUST appear in the manifest—branch protection or policy MUST NOT require additional hosted reruns of the same substantive checks outside the manifest + attestation model.
- **FR-002**: A local workflow MUST produce the committed **JSON** attestation containing at minimum: `format_version`, a `run_id`, `generated_at` (UTC ISO-8601), and a `checks` array with one entry per manifest `id` recording `status`. On a fully successful generation, every entry MUST be `passed`. The `run_id` MUST be a **UUID version 4** identifying that generation event (globally unique in intent; duplicates are impermissible in practice). Optional correlators (e.g., abbreviated commit SHA) MAY be included if documented.
- **FR-003**: The attestation carries a monotonic integer `format_version`. **Breaking** layout or semantic changes increment `format_version` and MUST update validators and schema in the same change. For **`format_version: 1`**, unknown top-level properties are **not allowed** (strict shape; see contract schema `additionalProperties`); **additive** top-level fields are introduced only with a **new `format_version`** and matching validator/schema updates. Future versions MAY relax or extend this rule explicitly in their schema text.
- **FR-004**: The hosted integration provider MUST define **exactly one** workflow file containing **exactly one** job that validates the **committed manifest and attestation** for merge under this spec for the repository. Multiple workflows each defining their own merge-blocking attestation validator, or multiple required jobs for the same mechanism, are **not allowed**. For branch protection, **at most one required status context** may correspond to this mechanism; similarly named checks for unrelated workflows MUST NOT be confused with this gate in documentation.
- **FR-005**: That job MUST fail on **attestation** problems when any of the following holds: the attestation file is **absent** at the canonical path; the path is not a readable file; bytes are not valid **UTF-8** JSON; JSON parses but **fails the active attestation schema** for its declared `format_version`; or required top-level attestation fields are missing or wrong-typed. The same job MUST fail on **manifest** problems when any of the following holds: the manifest file is **absent** at its canonical path; not a readable file; bytes are not valid **UTF-8** JSON; JSON parses but **fails the documented required-check manifest shape** (including duplicate `id` values in `checks`, empty `checks`, missing `manifest_version`, or missing required fields per `specs/019-contract-ci-json-gate/contracts/required-checks-manifest.md`). For FR-009, manifest-side failures use the same primary categories **`missing_file`**, **`io_or_parse`**, and **`schema`** as for the attestation (message text MUST indicate **manifest** vs **attestation** so contributors know which file to fix).
- **FR-006**: That job MUST fail the **staleness** rule when `generated_at` (parsed as a UTC instant) is strictly older than a project-configured maximum duration **before** the validator’s start instant, where the validator’s clock is the **UTC wall clock at validation start on the hosted runner** executing the job (equivalently: the job’s notion of time in UTC). The maximum duration MUST be documented for contributors.
- **FR-007**: That job MUST fail when any manifest `id` is **missing** from `checks`, appears more than once, or any entry is not `status: passed` for merge eligibility.
- **FR-008**: That job MUST succeed only when **every clause of FR-005** is satisfied for **both** manifest and attestation, **and** FR-006 **and** FR-007 are satisfied.
- **FR-009**: Failure messages MUST name one **primary category** so contributors can remediate without reading implementation code. Categories MUST cover at least: **`missing_file`**, **`io_or_parse`**, **`schema`**, **`staleness`**, **`incomplete_manifest`**, **`failed_check`**. Each category MUST map to documented remediation: regenerate attestation, fix paths, refresh stale attestation, repair attestation or manifest JSON per contract/schema, repair schema/version drift, rerun failed manifest command, or update manifest/attestation pair after manifest edits.
- **FR-010**: Merge eligibility under this gate MUST be satisfied solely by the **manifest and attestation** meeting FR-005 through FR-008 without hosted re-execution of manifest commands; the central job MUST NOT treat hosted re-execution of manifest checks as a merge requirement. Optional advisory hosted jobs remain allowed; they MUST NOT be listed as merge-blocking substitutes unless the project extends the manifest with **separate attested steps** whose commands capture the hosted outcome in a way that still flows through the attestation file (documented per-check).
- **FR-011**: Moving checks off hosted runners MUST **not** remove substantive quality categories from the manifest: at minimum the manifest MUST include the repository’s documented full local CI aggregate (`make ci` or its documented successor) so constitution-style merge-ready verification is preserved in one place unless a deliberate, reviewed charter change retires a category.

### Key Entities

- **Required-check manifest**: The canonical set of checks that must appear in every valid attestation, maintained in the repository (or equivalent single source of truth).
- **Test attestation**: JSON file produced by the local workflow containing `run_id`, `generated_at`, `format_version`, and per-check outcomes aligned to the manifest.
- **Freshness window**: A documented duration defining how old an attestation may be when the central job evaluates it.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In a **controlled trial** of **at least seven** pull requests or equivalent protected branches—covering **(a)** missing attestation with valid manifest, **(b)** missing manifest with attestation otherwise present, **(c)** invalid manifest shape per FR-005, **(d)** invalid attestation parse or schema per FR-005 with valid manifest, **(e)** stale attestation, **(f)** incomplete ids vs manifest or any required check not `passed`, and **(g)** a fully valid **manifest and attestation** pair—the central validation job outcomes MUST match the spec for **100%** of those seven cases (reject a–f; accept g). This set aligns with **User Story 2** acceptance scenarios 1–7.
- **SC-002**: In the same trial class as SC-001, when a maintainer certifies that the contributor **followed every documented regeneration step in order without skipping** and committed the emitted JSON unchanged (aside from repository-normalized line endings), a valid attestation MUST be accepted on **first validation attempt** at least **95%** of the time across a sample of **at least 20** such attempts (binomial rationale left to program management; the requirement is the stated threshold).
- **SC-003**: **Documentation-only review**: a reviewer **not** involved in authoring the attestation gate docs, given **30 minutes** with only published contributor documentation, MUST answer a **five-question** checklist about pass/fail scenarios; **success** is defined as **≥4 correct** answers averaged across **three** independent reviewers on the same doc revision (deliberately operationalized “naive contributor” proxy).
- **SC-004**: When the manifest gains a new required `id` on a branch tip commit, the **next completed run** of the attestation validation job for that commit (same workflow/job defined in FR-004) MUST fail until a fresh attestation generated under the new manifest is present—without relying on unrelated workflows in the repository.
- **SC-005**: Published contributor documentation MUST state plainly that **manifest checks are proven locally for merge**, MUST list **minimum accepted risks** verbatim: **no mandatory hosted re-run of manifest checks for merge**, **fork/untrusted machine attestation**, **environment drift**, **bad-faith or mistaken claims**, and MUST list optional mitigations **separately** as advisory unless promoted through manifest + FR-010.

## Assumptions

- The repository already uses a hosted continuous integration provider; merge gating for this contract is **one** automated job that **validates the committed manifest and attestation only** (no hosted re-execution of manifest commands). Advisory hosted jobs MAY run for signal; they do **not** satisfy FR-005–FR-008 unless their results are represented through manifest/attestation per FR-010.
- The attestation and manifest are **stored with the change** at the **canonical relative paths** referenced in **Normative paths and serialization** so reviewers and automation read the same bytes as the diff under review.
- The freshness window, manifest location, regeneration commands, and FR-009 category meanings are **documented for contributors** and change through normal review.
- “Contract-based” here means **manifest + attestation + validator** behavior, not a specific vendor product name.
- This gate complements the constitution’s expectation that merge-ready work satisfies documented verification; **FR-011** guards against silently dropping categories of checks when moving work off hosted runners.
