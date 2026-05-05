# Requirements-writing checklist: CI attestation merge gate

**Purpose**: Unit-test the **written requirements** (spec/plan/tasks alignment) for the local attestation + single merge gate—not implementation behavior.  
**Created**: 2026-05-04  
**Feature**: [spec.md](../spec.md), [plan.md](../plan.md), [tasks.md](../tasks.md)

**Defaults used** (no `/speckit-checklist` arguments): standard depth; audience **PR reviewer + spec author**; focus **trust boundary**, **staleness/manifest completeness**, and **cross-artifact consistency**.

## Requirement completeness

- [x] CHK001 Are authoritative required checks defined with both stable identifiers and human-readable names in the requirements, not only implied by examples? [Completeness, Spec FR-001]
- [x] CHK002 Are the minimum contents of a successful attestation (per-check outcomes, unique run identifier, generation time) all explicitly mandated together? [Completeness, Spec FR-002]
- [x] CHK003 Is “versioned or evolvable” attestation format spelled out with enough precision that breaking vs additive changes can be distinguished in requirements? [Clarity, Spec FR-003]
- [x] CHK004 Are all failure classes the central gate must detect (missing file, unreadable, schema mismatch, staleness, incomplete manifest coverage, non-pass outcomes) enumerated without gaps relative to FR-005–FR-008? [Completeness, Spec FR-005–FR-008]
- [x] CHK005 Is the exclusivity of merge proof (attestation only; no hosted re-execution of manifest checks) stated without leaving a loophole for “shadow” required checks? [Completeness, Spec FR-010]
- [x] CHK006 Does published documentation success criterion name both **local proof for merge** and **minimum accepted risks** explicitly? [Completeness, Spec SC-005]

## Requirement clarity

- [x] CHK007 Is “project-configured maximum age” for staleness anchored to a defined clock reference (e.g., validator execution time) in the requirements text? [Clarity, Spec FR-006, Edge Cases — Clock skew]
- [x] CHK008 Is “unique run identifier” constrained enough to avoid conflicting interpretations (e.g., uniqueness scope: per run vs per repo vs global)? [Clarity, Spec FR-002]
- [x] CHK009 Are failure-message requirements tied to **categories** that map one-to-one to contributor remediation paths? [Clarity, Spec FR-009]
- [x] CHK010 Is “exactly one job” for this mechanism defined so readers know whether multiple workflows with one job each would violate FR-004? [Ambiguity, Spec FR-004]

## Requirement consistency

- [x] CHK011 Are User Story 2’s “validates that file only” and FR-010’s “solely by the attestation” mutually reinforcing without contradicting optional advisory hosted jobs in Assumptions? [Consistency, Spec User Story 2, Spec FR-010, Spec Assumptions]
- [x] CHK012 Do success criteria SC-001–SC-004 align with FR-005–FR-008 outcomes (no success criterion requiring hosted re-runs that FR-010 forbids)? [Consistency, Spec SC-001–SC-004, Spec FR-010]
- [x] CHK013 Does the plan’s “JSON attestation” language remain consistent with the spec’s “machine-readable” framing and contracts, or is any mismatch explained? [Consistency, Plan Summary / Technical Context, Spec FR-002]

## Acceptance criteria quality

- [x] CHK014 Can SC-001’s “controlled trial on sample pull requests” be executed without undefined trial size or pass/fail rubric? [Measurability, Spec SC-001]
- [x] CHK015 Is the “95% first-attempt acceptance” in SC-002 tied to observable inputs (“contributor instructions were followed”) in a way reviewers can apply consistently? [Measurability, Spec SC-002]
- [x] CHK016 Is SC-003’s “naive contributor” review criterion operationalized (e.g., role, time box) or intentionally left subjective—and is that choice explicit? [Measurability, Spec SC-003]
- [x] CHK017 Is SC-004’s “within one pipeline run” unambiguous for monorepo contexts where multiple workflows may exist? [Clarity, Spec SC-004]

## Scenario coverage (requirements narrative)

- [x] CHK018 Are primary flows covered for **generation**, **validation failure modes**, and **manifest evolution** as three distinguishable requirement arcs? [Coverage, Spec User Stories 1–3]
- [x] CHK019 Are alternate flows specified when local checks fail (how the attestation must not claim full success) with enough precision to avoid contradictory implementations? [Coverage, Spec User Story 1 acceptance scenario 2]

## Edge case coverage

- [x] CHK020 Is the **partial reruns** edge case resolved to a single chosen approach (“full rerun” vs “documented merge”) in requirements, not deferred only to planning artifacts? [Edge Case, Spec Edge Cases — Partial reruns]
- [x] CHK021 Are integrity expectations for tampering either fully specified or explicitly deferred with a “no integrity beyond manifest alignment” decision captured in requirements? [Edge Case, Spec Edge Cases — Tampering]
- [x] CHK022 Is the **trust boundary** requirement explicit about which risks must appear in contributor docs (fork PRs, drift, bad-faith attestation) vs optional mitigations? [Completeness, Spec Edge Cases — Trust boundary, Spec SC-005]

## Non-functional / trust & governance

- [x] CHK023 Are trust and non-repudiation expectations proportionate to Option A (local-only proof) documented as **accepted risks** rather than implied zero risk? [Non-functional, Spec Clarifications Session 2026-05-04, Spec SC-005]
- [x] CHK024 Is the relationship between this gate and the constitution’s merge-ready bar stated so “move checks local” does not silently drop mandatory quality categories? [Traceability, Spec Assumptions last bullet, Plan Constitution Check]

## Dependencies & assumptions

- [x] CHK025 Is the assumption “attestation stored with the change” matched to a requirement that the **path** or storage rule is part of the contract reviewers can rely on? [Assumption, Spec Assumptions, Spec FR-005]
- [x] CHK026 Are optional hosted jobs explicitly excluded from substituting attestation **unless** manifest extension rules exist—those extension rules themselves specified or marked [Gap]? [Dependency, Spec Assumptions first bullet]

## Ambiguities & conflicts

- [x] CHK027 If plan/tasks name concrete filenames (`.ci/*.json`, workflow names) not present in the spec, is that gap acknowledged as implementation detail vs a spec omission for “project-defined path”? [Traceability, Spec FR-005, Plan Project Structure]
- [x] CHK028 Is “duplicate or conflicting gates for this mechanism” defined sharply enough to settle disputes when similarly named checks appear in branch protection? [Ambiguity, Spec FR-004]

## Notes

- Check items off as findings are resolved in the spec or explicitly accepted as plan-only detail.
- Keep this file distinct from [requirements.md](./requirements.md) (spec authoring gate from `/speckit.specify`).

## Resolution log (2026-05-04)

Addressed in `specs/019-contract-ci-json-gate/spec.md`: added **Normative paths and serialization**; tightened **User Story 1** failure attestation behavior; resolved **partial reruns** to full-suite only; scoped **v1 integrity**; expanded **trust boundary** and **SC-005** mandatory doc strings; rewrote **FR-001–FR-011** (new FR-011), **FR-005–FR-007** enumerations, **FR-006** clock anchor, **FR-009** categories; operationalized **SC-001–SC-004**; reconciled **Assumptions** with advisory hosted jobs and canonical paths.
