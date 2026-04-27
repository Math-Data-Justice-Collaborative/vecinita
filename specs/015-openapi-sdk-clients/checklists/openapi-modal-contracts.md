# Requirements Quality Checklist: OpenAPI clients, env consolidation, and Modal SDK boundaries

**Purpose**: Unit-test the *written requirements* (not implementation) for clarity, completeness, consistency, and measurability before merge-ready implementation.  
**Created**: 2026-04-24  
**Feature**: [spec.md](../spec.md) · [plan.md](../plan.md) · [tasks.md](../tasks.md)

**Audience / depth**: PR reviewer · **Standard** rigor (empty `/speckit-checklist` arguments—defaults applied).

**Review status**: Items CHK001–CHK022 were closed against [spec.md](../spec.md) on **2026-04-24** (normative clarifications to FR/SC/edge cases/assumptions). Re-open an item if the spec regresses.

## Clarifying context (no answers received)

| # | If answered, would change checklist emphasis |
|---|-----------------------------------------------|
| Q1 | Should items stress **operator/release** gates (SC-004, staging) over **developer codegen** ergonomics (SC-003)? |
| Q2 | Is **browser-only** TypeScript (Axios/fetch) in scope for FR-001 static rules at the *requirements* level, or left entirely to contracts/tasks? |
| Q3 | Should **fork / optional CI** (schema URLs unset) be treated as a first-class requirements gap or an acceptable documented exception? |

---

## Requirement completeness

- [x] CHK001 Are all outbound connection kinds (database, gateway, agent, data-management API, three schema documents) explicitly covered by named requirements or user stories without leaving an unnamed “misc URL” class? [Completeness, Spec US1, Spec FR-004]
- [x] CHK002 Are post-migration obligations for each deprecated variable in **FR-005** scoped consistently across application code, deployment manifests, and example env files in the requirements text itself? [Completeness, Spec FR-005, Spec SC-001]
- [x] CHK003 Does the specification require a documented enforcement mechanism for **FR-001** at the success-criterion level (not only in plan/contracts)? [Completeness, Spec SC-005, Spec FR-001]

## Requirement clarity

- [x] CHK004 Is “Modal-assigned hostnames” in **FR-001** / **SC-005** clearly anchored to an authoritative pattern or definition a reader can find from the spec alone, or is it only inferable from external contracts? [Clarity, Traceability, Spec FR-001, Spec SC-005]
- [x] CHK005 Is “application logic” in **FR-002** distinguished from generated client internals, tests, and tooling in normative language, or could a reader disagree on what must migrate? [Ambiguity, Spec FR-002]
- [x] CHK006 Is “explicit offline mode” for OpenAPI artifacts defined with entry/exit criteria distinct from “fail loudly” in the edge-case list? [Clarity, Spec Edge Cases — Schema fetch failures]
- [x] CHK007 Is “maintained application packages” in **SC-002** bounded so the 95% ratio is computable without implicit repository folklore? [Clarity, Spec SC-002]

## Requirement consistency

- [x] CHK008 Do **FR-004**, **FR-006**, and User Story 1 jointly forbid parallel “shadow” base URLs for the same logical destination without contradicting “plus unrelated secrets”? [Consistency, Spec FR-004, Spec FR-006, Spec US1]
- [x] CHK009 Is Clarification **Option B** (no Modal HTTP in any checked-in code) fully aligned with **FR-001** and the Modal HTTP edge-case paragraph—no residual allowance for Modal product HTTP surfaces in-repo? [Consistency, Spec Clarifications, Spec FR-001, Spec Edge Cases]
- [x] CHK010 Do **FR-007** and **FR-002** agree on what “demonstrate reachability” means versus “all traffic must use generated clients”? [Consistency, Spec FR-007, Spec FR-002]

## Acceptance criteria quality

- [x] CHK011 Can **SC-004**’s p95 error-rate comparison be assessed from requirements plus the referenced operator checklist artifact, or does measurable acceptance still depend on undefined metrics ownership? [Measurability, Spec SC-004]
- [x] CHK012 Is **SC-003**’s “under 30 minutes” bounded by which steps count (codegen only vs full `make ci`), or is that boundary only in tasks/docs? [Measurability, Spec SC-003]
- [x] CHK013 Does **SC-001**’s “excluding generated vendor trees” use exclusion rules stable enough for objective automation, or are ignore rules underspecified at the requirement level? [Measurability, Spec SC-001]

## Scenario coverage

- [x] CHK014 Are **recovery / escalation** requirements stated when a team believes a feature cannot meet **FR-001** without HTTP to Modal (beyond a single edge-case sentence)? [Coverage, Exception flow, Spec Edge Cases — Modal HTTP shortcuts]
- [x] CHK015 Are **partial migration** obligations for multi-language runtimes expressed as measurable requirements, not only as process imperatives? [Coverage, Spec Edge Cases — Partial migration]
- [x] CHK016 Are **caller placement** scenarios (inside Modal app modules vs outside) explicitly covered for model/embedding behavior without leaving gaps between **FR-001** and **FR-002**? [Coverage, Spec FR-001, Spec FR-002, Spec US3]

## Edge case coverage

- [x] CHK017 Are **secrets embedded in `DATABASE_URL`** requirements limited to documentation/logging, or is broader secret-handling in scope for this feature? [Edge case, Spec Edge Cases — Secrets in URLs]
- [x] CHK018 When schema URLs are unset in some CI contexts, do requirements state whether skipping generation is allowed versus failing—without contradicting “fail loudly” for unreachable URLs? [Conflict risk, Spec Edge Cases, Spec FR-003]

## Non-functional and cross-cutting

- [x] CHK019 Are **stability / breaking-change** expectations for generated client surfaces stated relative to constitution “breaking changes” discipline, or deferred entirely to other docs? [Dependency, Spec Assumptions — Constitution alignment]
- [x] CHK020 Does the specification separate **normative MUSTs** from **Assumptions** (e.g., specific OpenAPI Generator generator IDs) so readers know which can change without a spec amendment? [Consistency, Spec Assumptions vs FR-002/FR-003]

## Ambiguities and conflicts

- [x] CHK021 Is there any residual ambiguity between “no HTTP to Modal hosts” and legitimate HTTP to **Render-hosted** services that might share naming or future host patterns? [Ambiguity, Spec FR-001, Spec FR-004]
- [x] CHK022 Do success criteria identifiers and the note on non-sequential ordering eliminate mis-reads of dependency order between **SC-005** and **SC-002**? [Clarity, Spec Success Criteria preamble]

## Notes

- Check items off as findings are resolved in the spec/plan: `[x]`
- Prefer updating [spec.md](../spec.md) over “answering” only in this file when a gap is real.
