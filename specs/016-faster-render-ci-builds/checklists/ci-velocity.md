# CI & deployment velocity — requirements quality checklist

**Purpose**: Unit-test the **written requirements** (spec, plan, tasks) for clarity, completeness, and consistency around faster CI and hosted builds—**not** to validate that pipelines or Render already run faster.  
**Created**: 2026-04-28  
**Feature**: [spec.md](../spec.md) · [plan.md](../plan.md) · [tasks.md](../tasks.md)

**Defaults** (no user override): **Standard** depth · **PR reviewer** audience · Focus: **measurability**, **skip auditability**, **equivalence / coverage** vs speed.

---

## Requirement completeness

- [x] CHK001 Are **all** change categories that qualify for segmented baselines and success claims enumerated or clearly derivable from the Key Entities list, not only the examples in FR-002/FR-003? [Completeness, Spec Key Entities, Gap]
- [x] CHK002 Are requirements stated for **what happens** if baseline history is too sparse (fewer than the implied N runs) to compute a stable median? [Completeness, Spec Assumptions, Gap]
- [x] CHK003 Does FR-001 explicitly require **both** (a) integration validation duration and (b) hosted **build-phase** duration baselines **per aligned change category**, or is alignment between (a) and (b) left implicit? [Completeness, Spec FR-001, Clarity]
- [x] CHK004 Are requirements present for documenting **written approval** fields (who, what artifact) when FR-004 waivers apply, beyond “explicitly approved in writing”? [Completeness, Spec FR-004, Gap]

## Requirement clarity

- [x] CHK005 Is “**high-frequency change category**” in FR-002 defined with objective selection criteria (e.g., share of PRs, team vote), or is interpreter discretion the only guide? [Clarity, Spec FR-002, Ambiguity]
- [x] CHK006 Is “**median**” unambiguous for skewed distributions (e.g., whether failed runs are excluded, whether warm-only samples are allowed)? [Clarity, Spec SC-001, Edge Cases]
- [x] CHK007 Is “**build phase**” distinguished from queueing, image pull, and post-build health checks in a way that two readers would measure the same interval? [Clarity, Spec Key Entities “Build phase”]
- [x] CHK008 Is “**same intent**” for faster equivalent checks under FR-004 / FR-007 defined or exemplified enough to resolve disputes during review? [Clarity, Spec FR-004, FR-007, Ambiguity]

## Requirement consistency

- [x] CHK009 Are Clarifications (“speed-only”, no net loss of checks) and FR-007 (no shrinking defect/security classes) **free of tension** with FR-002’s “without removing checks” wording when a check is **replaced** by an equivalent? [Consistency, Spec Clarifications, Spec FR-002, FR-004, FR-007]
- [x] CHK010 Do SC-003’s merge-blocking / correctness expectations align with User Story 3 acceptance scenarios without introducing stricter or looser merge policy than FR-004? [Consistency, Spec SC-003, User Story 3, Spec FR-004]
- [x] CHK011 Do plan.md performance goals (≥20%) match the spec’s default bar and the Assumption allowing stricter goals, without conflicting numeric obligations? [Consistency, Plan Summary, Spec Assumptions, SC-001]

## Acceptance criteria quality (measurability)

- [x] CHK012 Can SC-004’s engineer sentiment outcome be **objectively scored** (what counts as “majority experience,” tie-breakers, anonymous vs named)? [Measurability, Spec SC-004, Gap]
- [x] CHK013 Is the **twenty percent** improvement in SC-001/SC-002 defined against the **same** statistic (median vs mean) and **same** population as FR-002/FR-003? [Measurability, Spec SC-001–002 vs FR-002–003, Consistency]
- [x] CHK014 Are “**documented baseline**” and “**documented absolute cap**” in FR-003 tied to a single artifact or governance location in requirements, or only in plan/tasks? [Traceability, Spec FR-003, Plan/tasks]

## Scenario & edge-case coverage (requirements text)

- [x] CHK015 Are **recovery** requirements defined when a regression in duration is detected after optimization (rollback policy, freeze, or re-baseline)? [Coverage, Gap, Exception flow]
- [x] CHK016 Do edge cases collectively require explicit handling of **resource contention** (concurrent runs) when claiming a 20% win, or is that only advisory prose? [Coverage, Spec Edge Cases “Concurrent runs”, Measurability]
- [x] CHK017 Are **flakiness** requirements limited to “must not increase,” without defining how flakiness is measured—leaving acceptance ambiguous? [Clarity, Spec Edge Cases “Flaky tests”, Gap]

## Dependencies & assumptions

- [x] CHK018 Is the assumption that baselines can be pulled from “**existing** platform and integration histories” risk-assessed if secrets or retention prevent access? [Assumption, Spec Assumptions, Dependency]
- [x] CHK019 Are cross-artifact dependencies (e.g., plan’s parallel Schemathesis jobs vs tasks T008–T009 vs constitution’s contract-test norms) called out in the **spec**, or is that appropriately delegated only to plan/tasks without a spec gap? [Traceability, Constitution vs Spec, Plan]

## Ambiguities & conflicts

- [x] CHK020 Does SC-003’s “**same inputs**” for merge outcomes introduce ambiguity for **nondeterministic** checks (flaky tests, timing-dependent gates) relative to FR-007? [Ambiguity, Spec SC-003, Spec FR-007]
- [x] CHK021 Is “**green but hollow**” in edge cases defined distinctly from FR-006’s traceable skips, so reviewers do not conflate malicious shortcuts with legitimate path filters? [Clarity, Spec Edge Cases, Spec FR-006, Consistency]

## Notes

- Use this checklist when reviewing **spec.md** amendments before merge; re-run after substantive edits to FR/SC or Assumptions.
- Items reference the feature spec **FR-** / **SC-** labels and headings where section numbers are not used in the source document.

---

## Resolution log (2026-04-28)

Checklist items addressed by updates to [spec.md](../spec.md), [plan.md](../plan.md), [tasks.md](../tasks.md), and [data-model.md](../data-model.md).

- [x] CHK001 — **Canonical change categories** enumerated in spec **Definitions**; Key Entities aligned.
- [x] CHK002 — **FR-001** provisional baseline when **N < 20**; engineering-lead exception path.
- [x] CHK003 — **FR-001** requires paired (a)/(b) per category with same labels and window.
- [x] CHK004 — **FR-004** extended with approver, date, check id, rationale, same-intent, storage in governance artifact.
- [x] CHK005 — **High-frequency / primary** defined as largest merged-PR count; tie-break by leads.
- [x] CHK006 — **Median** defined: successful only; failed/cancelled excluded; warm/cold labeling.
- [x] CHK007 — **Build phase** interval defined (start of build steps through image ready; excludes queue, traffic switch, health stabilization).
- [x] CHK008 — **Same intent** definition for faster equivalents in **Definitions**.
- [x] CHK009 — Clarifications bullet: replacement under **FR-004** not counted as removal in **FR-002**.
- [x] CHK010 — **SC-003** aligned with flaky policy and **same inputs**; consistent with User Story 3 and **FR-004**.
- [x] CHK011 — Assumption: stricter plan goals allowed if documented in governance artifact and FR minima met.
- [x] CHK012 — **SC-004** objective pass rule with **floor/ceil** counts and abstention note.
- [x] CHK013 — **SC-001**/**SC-002** reference same median and population rules as **FR-002**/**FR-003**.
- [x] CHK014 — **Governance artifact** path defined in **Definitions**; **FR-003** cap co-located.
- [x] CHK015 — **FR-008** regression / re-baseline / revert obligation.
- [x] CHK016 — Edge case: 20% claims require comparable load or annotated concurrency.
- [x] CHK017 — Flakiness assessment: job-level signals or written platform-owner assessment.
- [x] CHK018 — Assumption: measurement sprint if history blocked; retention/secrets called out.
- [x] CHK019 — Assumption: plan/tasks detail delegated without contradicting FR/constitution.
- [x] CHK020 — **SC-003**: nondeterminism via flaky-test policy unchanged; **same inputs** = commit + CI config.
- [x] CHK021 — Edge case: **green but hollow** vs **traceable skip** distinguished.
