# Requirements quality checklist: Wiring and cross-service contracts

**Purpose**: Unit-test the *English* of feature `005-wire-services-dm-front`—completeness, clarity, consistency, and measurability of requirements for env wiring, integration vs contract testing, and Pact/OpenAPI alignment (not implementation verification).

**Created**: 2026-04-21

**Feature**: [spec.md](../spec.md) · [plan.md](../plan.md)

---

## Requirement completeness

- [ ] CHK001 Are **all** env vars that affect chat↔gateway↔agent resolution explicitly listed or cross-referenced in **FR-001** / **FR-002**, including proxy-only vars (`VITE_GATEWAY_PROXY_TARGET`) and schema URLs used for contracts? [Completeness, Spec §FR-001–FR-002, Plan §Technical Context]
- [ ] CHK002 Are requirements present for **both** DM connection modes (direct `VITE_VECINITA_SCRAPER_API_URL` vs gateway modal-jobs when `VITE_USE_GATEWAY_MODAL_JOBS` is set), not only the default path? [Completeness, Spec §FR-003, Spec §User Story 2]
- [ ] CHK003 Is the **complete** set of HTTP surfaces that **FR-007** and **FR-008** must cover enumerated (paths, methods, or reference to a pact catalog), or is intentional deferral marked as a gap? [Completeness, Gap, Spec §FR-007–FR-008]
- [ ] CHK004 Are requirements stated for **provider** verification artifacts (where results are published, who reads them) in addition to consumer runs on PR? [Completeness, Spec §FR-007–FR-008, Spec §SC-002–SC-005]
- [ ] CHK005 Does **FR-004** name the authoritative OpenAPI/schema artifact (file path, CI artifact name, or generation step) rather than only “alignment” in the abstract? [Completeness, Clarity, Spec §FR-004]

## Requirement clarity

- [ ] CHK006 Is “**documented** workflow” in **FR-006** / **SC-003** defined with measurable identifiers (workflow file name, branch filter, cron expression, or `workflow_dispatch` label)? [Clarity, Spec §FR-006, Spec §SC-003]
- [ ] CHK007 Is “**mock/fixture-first**” on PRs bounded—e.g. which layers may use MSW vs in-process fakes—so implementers do not interpret it as “no HTTP tests on PR”? [Clarity, Ambiguity, Spec §FR-006]
- [ ] CHK008 Are “**approved stubs**” for provider verification defined with acceptance rules (who approves, when stubbing is disallowed)? [Clarity, Gap, Spec §FR-007–FR-008]
- [ ] CHK009 Is “**equivalent**” to Pact (in **FR-007** / success criteria) constrained so alternative tools must meet the same consumer/provider guarantees? [Clarity, Spec §FR-007, Spec §SC-004–SC-005]
- [ ] CHK010 Are timeout relationships between **VITE_AGENT_*** and gateway **AGENT_*** timeouts referenced as explicit ordering requirements, not only implied by User Story 1? [Clarity, Plan §Technical Context, Spec §User Story 1]

## Requirement consistency

- [ ] CHK011 Do **FR-005**, **FR-007**, and User Story 3 scenario 2 agree on the **mandatory** pairing of Schemathesis (provider OpenAPI) and Pact (consumer) without contradicting **FR-006**’s “no full stack on PR”? [Consistency, Spec §FR-005–FR-007, Spec §User Story 3]
- [ ] CHK012 Are **SC-002** (main / default-branch emphasis) and **SC-004–SC-005** (PR consumer runs) consistent about which gates are **merge-blocking** vs informational? [Consistency, Spec §SC-002–SC-005]
- [ ] CHK013 Do **Assumptions** (scraper-compatible surface) align with **FR-008** when gateway modal-jobs mode points at a **different** host/path—any assumption conflict called out? [Consistency, Spec §Assumptions, Spec §FR-008]
- [ ] CHK014 Does **plan.md** Testing Strategy align with **FR-006–FR-008** on Pact and real-stack placement, or is divergence documented? [Consistency, Plan §Testing Strategy, Spec §FR-006–FR-008]

## Acceptance criteria quality (measurability)

- [ ] CHK015 Can **SC-001** be judged pass/fail without subjective interpretation (“without reading scattered README fragments”)? [Measurability, Spec §SC-001]
- [ ] CHK016 Are **SC-004** and **SC-005** measurable as specific CI job names or required check contexts? [Measurability, Gap, Spec §SC-004–SC-005]
- [ ] CHK017 Does **SC-002** define what “**FR-008** provider verification meets the documented … policy” means in pass/fail terms? [Measurability, Clarity, Spec §SC-002]

## Scenario coverage (requirements for flows)

- [ ] CHK018 Are **recovery** requirements defined when real-stack integration (**FR-006**) fails intermittently (retry policy, flake handling, or owner escalation)? [Coverage, Gap, Exception Flow, Spec §FR-006]
- [ ] CHK019 Are **alternate** persona requirements distinguished (developer vs operator vs maintainer) where their env or contract obligations differ? [Coverage, Spec §User Stories 1–3]
- [ ] CHK020 Is the **first-time contributor** path in **SC-001** traceable to concrete doc sections (`quickstart.md` headings) in the spec or plan? [Traceability, Spec §SC-001, Plan §quickstart.md]

## Edge case coverage (requirements text)

- [ ] CHK021 Is “**same logical URLs**” for `window.__VECINITA_ENV__` vs `import.meta.env` specified with a resolution order or conflict rule? [Edge Case, Clarity, Spec §Edge Cases]
- [ ] CHK022 Are requirements for **non-localhost** relative `VITE_GATEWAY_URL=/api` quantified or explicitly delegated to named code modules with a “must not regress” clause? [Edge Case, Spec §Edge Cases, Spec §User Story 1]
- [ ] CHK023 Does the spec require documentation of **broker vs local pact file** authentication and secret handling beyond a single bullet? [Edge Case, Completeness, Spec §Edge Cases, Clarifications]

## Non-functional requirements (as written)

- [ ] CHK024 Are **security** requirements for pact broker credentials, OpenAPI fetch URLs, and CI env injection stated explicitly (forbidden in logs, rotation)? [NFR, Gap, Spec §Edge Cases, Constitution]
- [ ] CHK025 Are **performance** or **cost** ceilings for doubling Pact consumers (chat + DM) stated or explicitly “no new budget” with rationale? [NFR, Plan §Technical Context, Spec §FR-007–FR-008]

## Dependencies and assumptions

- [ ] CHK026 Is dependency on **`TESTING_DOCUMENTATION.md`** version or section pinned so contract gates do not silently move? [Dependency, Traceability, Spec §FR-005, Spec §User Story 3]
- [ ] CHK027 Is the assumption “**services/data-management-api** exposes scraper-compatible HTTP” validated with a link or version pin to that API’s contract doc? [Assumption, Spec §Assumptions]

## Ambiguities and conflicts

- [ ] CHK028 Is the **two-consumer** Pact strategy (**shared broker vs isolated flows**) resolved to a single authoritative requirement, not only an open edge-case bullet? [Ambiguity, Conflict, Spec §Edge Cases]
- [ ] CHK029 Are “**intentional gap**” exceptions in **FR-005** required to name the approver role and expiry/review cadence? [Gap, Spec §FR-005]
- [ ] CHK030 Do **Clarifications** session bullets map 1:1 to updated **FR**/**SC** text so no orphan clarification remains? [Consistency, Spec §Clarifications]

## Playwright end-to-end (requirements quality)

- [ ] CHK031 Are **which user journeys** count as “smoke compatibility” for the chat app spelled out beyond a generic phrase (e.g. config fetch, send message, stream optional)? [Completeness, Gap, Spec §FR-009]
- [ ] CHK032 Are **which DM dashboard surfaces** must appear in Playwright requirements listed (diagnostics, scrape job list, create/cancel scope)? [Completeness, Gap, Spec §FR-009]
- [ ] CHK033 Is “**isolated tests**” for Playwright given a requirement-level definition (fresh storage, no cross-test deps) rather than only a tool name? [Clarity, Spec §FR-009, Plan §Testing strategy]
- [ ] CHK034 Are requirements explicit for when Playwright may use **stubbed third-party** responses versus when it must hit **Vecinita-owned** backends? [Coverage, Ambiguity, Spec §FR-009, Plan §contracts/pact-schemathesis-playwright-pyramid.md]
- [ ] CHK035 Does **SC-006** name the workflow(s), branch, or check context so “documented Playwright E2E workflow(s) pass” is objectively auditable? [Measurability, Spec §SC-006]
- [ ] CHK036 Are **shard / parallelism** expectations for large Playwright suites stated as requirements or explicitly deferred with rationale? [NFR, Gap, Spec §FR-009]

## Typed integration DTOs (requirements quality)

- [ ] CHK037 Does **FR-010** require a **single canonical module path** (or naming pattern) per product line so “shared module” is not left implicit? [Clarity, Spec §FR-010, data-model.md §Typed testing artifacts]
- [ ] CHK038 Are **exceptions** to the no-duplicate-shapes rule (legacy endpoints, gradual migration) documented or forbidden? [Completeness, Gap, Spec §FR-010]
- [ ] CHK039 Is the relationship between **Zod vs OpenAPI codegen** as the source of types decided in requirements, or is implementer choice unconstrained in a way that splits teams? [Ambiguity, Spec §FR-010, Research §8 in plan-linked research.md]
- [ ] CHK040 Do **FR-010** and **FR-004** jointly state how OpenAPI drift is detected when types are codegen-based? [Consistency, Spec §FR-004, Spec §FR-010]

## Four-layer pyramid (plan, Schemathesis, Pact)

- [ ] CHK041 Does **plan.md** define non-overlapping **responsibilities** between Schemathesis (OpenAPI property stress) and Pact (consumer–provider agreement) so requirements cannot be read as redundant? [Clarity, Plan §Testing strategy, Spec §FR-005]
- [ ] CHK042 Are **Schemathesis** scope requirements updated to include **DM OpenAPI** (and gateway modal-jobs when applicable) wherever the spec still implies gateway/agent only? [Completeness, Gap, Plan §Testing strategy, Spec §FR-005]
- [ ] CHK043 Is there a requirement that **provider states** for Pact are named and owned (chat vs DM) in the spec or a normative contract doc, not only in `research.md`? [Traceability, Gap, Spec §FR-007–FR-008, Plan §contracts/pact-schemathesis-playwright-pyramid.md]
- [ ] CHK044 Are **Playwright** requirements aligned with **FR-006** on which path is PR-optional vs release-blocking without contradiction? [Consistency, Spec §FR-006, Spec §FR-009, Spec §SC-006]

## Documentation cross-references

- [ ] CHK045 Does **quickstart.md** list headings that satisfy **SC-001** traceability for Pact, Schemathesis, Playwright, and typed-DTO checks? [Traceability, Spec §SC-001, Plan §quickstart.md]
- [ ] CHK046 Is **plan.md** “Project structure” listing of `contracts/pact-schemathesis-playwright-pyramid.md` mirrored by an explicit pointer from **spec** or is the plan the sole authority—either way, is that intentional? [Consistency, Plan §Project Structure, Spec §FR-005–FR-010]

## Ambiguities and conflicts (post-extension)

- [ ] CHK047 After adding **FR-009–FR-010** and **SC-006**, does any earlier checklist item (e.g. CHK011–CHK014) need spec text updates to remain true? [Consistency, Spec global]
- [ ] CHK048 Are **accessibility or i18n** expectations for E2E-relevant flows cited where product constitution expects bilingual UX, or is exclusion explicit? [Coverage, Gap, Constitution §data stewardship / equity, Spec §FR-009]

## Notes

- Check items when the **spec/plan** text satisfies the criterion; use findings to drive spec edits or `/speckit.clarify`, not QA execution.
- **Append log (2026-04-21)**: Added **CHK031–CHK048** after plan/spec updates for **FR-009**, **FR-010**, **SC-006**, and the four-layer testing pyramid (`contracts/pact-schemathesis-playwright-pyramid.md`).
