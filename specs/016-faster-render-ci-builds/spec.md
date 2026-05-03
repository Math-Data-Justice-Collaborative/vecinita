# Feature Specification: Faster deployment and CI feedback

**Feature Branch**: `016-faster-render-ci-builds`  
**Created**: 2026-04-28  
**Status**: Draft  
**Input**: User description: "We need to reduce build times for the render services, and reduce the CI times for completion on GitHub Actions."

## Clarifications

### Session 2026-04-28

- Q: What is the priority between faster pipelines and preserving the functional coverage of validation, deployment correctness, and product behavior? → A: Preserve functionality and quality gates; reduce elapsed time only (no net loss of checks, detectable risk coverage, or user-visible behavior for the same inputs and change categories).
- **Replacing vs removing checks**: Replacing a required check with a **faster equivalent** under **FR-004** is **not** treated as “removing” that check for purposes of **FR-002** or **Clarifications**, provided **FR-004** documentation (approver, date, artifact) is complete and **same intent** holds per **Definitions**.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Faster feedback after a code change (Priority: P1)

A developer pushes a change and needs confidence that tests and checks pass—covering the same failure modes as before—without waiting longer than necessary. They want the integrated validation run to finish sooner so they can iterate, fix failures, or merge.

**Why this priority**: Short feedback loops directly reduce calendar time for fixes and releases and lower context-switching cost for the team.

**Independent Test**: Compare wall-clock time from push to “all required checks green” before and after improvements, using the same categories of change (for example, documentation-only vs. full application change).

**Acceptance Scenarios**:

1. **Given** a typical application change that triggers the full validation suite, **When** the run completes successfully, **Then** elapsed time from trigger to completion is measurably lower than the agreed baseline for that category of change.
2. **Given** a change that should skip heavy work (for example, documentation or configuration that does not affect build artifacts), **When** validation runs, **Then** elapsed time reflects only the work that is still required for safety, not a full redundant build of unchanged artifacts.

---

### User Story 2 - Faster deployment builds on the hosting platform (Priority: P2)

Someone triggers or merges a deployment; the hosted services’ build phase completes sooner so new versions reach staging or production faster, while the built artifact still meets the same quality and correctness expectations as before optimization.

**Why this priority**: Shorter deployment builds reduce risk windows and operational toil, but validation in CI remains the first line of defense (P1).

**Independent Test**: Compare build-phase duration for the same class of deployment (for example, code-only vs. dependency change) before and after improvements, using platform-reported or logged timings.

**Acceptance Scenarios**:

1. **Given** a deployment that only changes application source without changing declared dependencies or base images, **When** the build runs, **Then** build-phase duration is measurably lower than the agreed baseline for that class.
2. **Given** a failed build, **When** the developer inspects logs, **Then** they can still tell whether failure was due to tests, compile, or packaging (no loss of diagnosability in exchange for speed).

---

### User Story 3 - Visible improvement and guardrails (Priority: P3)

Engineering and leads can see that time-to-green and time-to-deploy improved, and that safety nets (required checks, deployment gates) were not removed to fake speed.

**Why this priority**: Sustained improvement requires measurement and trust that quality bars stayed intact.

**Independent Test**: A short before/after report exists with median (or agreed percentile) timings and a checklist confirming required checks and deployment gates are unchanged in intent.

**Acceptance Scenarios**:

1. **Given** the improvement initiative is complete, **When** stakeholders review the summary, **Then** they see at least one agreed metric (for example, median time to green) improved by at least the agreed margin relative to baseline.
2. **Given** the same merge policies and required checks as before the initiative, **When** a change is merged, **Then** the same categories of risk are still gated (no silent removal of mandatory validation).

---

### Edge Cases

- **Cold cache / first run after a long idle period**: Timings may be higher; baseline comparisons should use comparable cache states or be labeled as “cold start” separately.
- **Large dependency or image updates**: These runs may legitimately take longer; expectations should be segmented by “dependency or base image change” vs. “code-only.”
- **Concurrent runs / runner contention**: Many simultaneous pipelines can contend for shared resources. A **twenty percent** (or stricter) improvement claim for **FR-002** / **SC-001** MUST use samples from **comparable load** periods **or** annotate runs with **concurrency context** (for example, queue time vs active CPU time) so spikes are not mistaken for regressions or wins.
- **Flaky tests**: Faster runs must not increase flakiness; if flakiness rises, that is treated as a quality regression, not a success. **Flakiness** is assessed by comparing **documented job-level** intermittent failure signals (for example, week-over-week retry counts or failure rate on unchanged integration jobs) before versus after optimization; if no automated metric exists, **platform or engineering-owner written assessment** satisfies this edge case until a metric is adopted.
- **“Green but hollow” vs traceable skips**: **Traceable skip** (**FR-006**): a **declared** path or condition omits a job subset and logs **which rule** fired. **Green but hollow**: success signals that **bypass** required detection (for example, neutered commands, always-pass stubs) **without** **FR-004** approval—these are **failure**, not success, and are **not** the same as legitimate path filters.
- **Sparse baseline history**: See **FR-001** and **Definitions** (provisional baseline).
- **Post-optimization regression**: See **FR-008**.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The organization MUST establish and document a baseline for **each change category** listed under **Canonical change categories** in Definitions: **(a)** wall-clock time from trigger until **all required** continuous-integration checks have **passed**, and **(b)** hosted deployment **build-phase** duration per Definitions—**where (b) applies** to that category (for example, **documentation_only** may omit (b) if documented). Categories **(a)** and **(b)** MUST use the **same labels and sampling window** so baselines are paired, not mixed across unrelated slices. If fewer than **twenty** successful samples exist for a category in the initial window, the baseline MUST be labeled **provisional** and the window extended **or** engineering leads MUST approve a **named minimum N** and rationale before declaring completion against that category.
- **FR-002**: For the **primary change category** (see Definitions: **high-frequency**), **median** time from trigger to all required checks passing MUST improve by at least twenty percent relative to the documented baseline, **without removing** checks whose purpose is to prevent defects or security issues from reaching the default branch—**except** replacements that satisfy **FR-004** and **same intent** in Definitions (**not** counted as removal).
- **FR-003**: For at least one deployment scenario where only application source changes (no declared dependency or base-image change), **median** **build-phase** duration on the hosting platform MUST improve by at least twenty percent relative to the documented baseline, **or** meet an **absolute time cap** documented in the **same governance artifact** as the baseline (see Definitions). The cap MUST name **approving role** and **date**.
- **FR-004**: The validation pipeline MUST continue to enforce all merge requirements that existed at the start of the initiative unless each waived requirement is **explicitly approved in writing** with: **(1)** named **approver** (role or person), **(2)** **date**, **(3)** **identifier** of the replaced or waived check, **(4)** **rationale**, and **(5)** confirmation that a **faster equivalent** meets **same intent** per Definitions. Approvals MUST be stored in the **governance artifact** location named in Definitions (or successor path approved by engineering leads).
- **FR-005**: Improvements MUST be reproducible: another engineer following internal documentation can understand what was changed to reduce wait time and why, without relying on tribal knowledge.
- **FR-006**: Where work is skipped for a given change (for example, paths that do not touch a service), the decision MUST be traceable in logs or job configuration so false negatives can be audited.
- **FR-007**: Time-reduction tactics MUST NOT shrink the set of defect, security, or correctness classes that required checks can catch for any defined change category below the baseline, except where **FR-004** applies (explicitly approved faster equivalent with **same intent**).
- **FR-008**: If **median** duration for a **FR-008 monitored dimension** (see Definitions) **regresses** by more than **ten absolute percentage points** versus the documented **post-optimization** snapshot **or** documented flakiness signals (Edge Cases) worsen beyond engineering-lead tolerance, the team MUST within **fourteen calendar days** choose and record: **re-baseline** with rationale, **revert** optimization, or **new approved target**—and MUST not leave the regression unexplained.

### Definitions *(normative for FR/SC)*

- **Canonical change categories** (closed set for baselines and reporting): **documentation_only**; **application_code_typical** (default **primary** category unless another wins frequency); **dependency_or_lockfile**; **container_image_or_base**; **infrastructure_or_workflow**; **full_span** (ambiguous or multi-area edits—use for conservative comparison). Mapping from pull-request file paths to a category MUST be documented in the governance artifact.
- **High-frequency / primary change category**: The canonical category with the **largest count of merged pull requests** in the baseline window; ties broken by **engineering-lead** selection, recorded once in the governance artifact.
- **Median (timing)**: The **median** is computed over **successful** outcomes only (all required checks passed for (a); image build succeeded for (b)). **Failed**, **cancelled**, or **skipped** runs are **excluded** from the median unless the metric explicitly measures those states. **Warm** vs **cold** cache state MUST be labeled when comparing samples (see Edge Cases).
- **Build phase**: The continuous interval from **first build-step execution** for the service image through **image build success** (image ready for deploy), **excluding** queue time before build starts, **excluding** traffic switch, and **excluding** post-deploy health-check stabilization, using timestamps from the hosting platform or a **once-documented** log-derived equivalent per environment.
- **Same intent (faster equivalent)**: A replacement check or job that would still **fail** on the **same** contract, security, and correctness defect classes as the baseline check for the **same change category**, without new blind spots—unless each new blind spot is listed and accepted under **FR-004**.
- **Governance artifact**: The committed document set under the active feature’s **`specs/<feature>/artifacts/`** directory (for example, `baseline-*.md`, `required-checks-inventory.md`) **or** a **single** engineering-wiki or runbook URL referenced from those files; baselines, caps, and **FR-004** waivers MUST live there or be linked from there without orphan approvals.
- **FR-008 monitored dimensions** (for regression detection vs **post-optimization** snapshot): **(M1)** metric **(a)** (time to all required checks green) for the **primary change category**; **(M2)** metric **(b)** (**build-phase**) for **application_code_typical** code-only deploys, **per** Render web service using `backend/Dockerfile` listed in root `render.yaml`. Engineering leads MAY record up to **three** additional named metrics (**M3–M5**) in the governance artifact (job id or category + phase), provided each is defined with the same median and success-only rules as above.

### Key Entities

- **Baseline window**: A defined calendar period and sampling method used to compute “before” timings; may be **extended** for provisional baselines per **FR-001**.
- **Change category**: One of the **Canonical change categories** in Definitions; used for paired (a)/(b) baselines.
- **Build phase**: As in Definitions (normative).

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For the **primary change category**, **median** time from trigger to all required checks passing improves by at least twenty percent versus the documented baseline, using the **same median and population rules** as **FR-002**.
- **SC-002**: For **application_code_typical** **code-only** deploys (no declared dependency or base-image change, per **FR-003** scenario), **median** **build-phase** duration improves by at least twenty percent versus the documented baseline **or** meets the **documented absolute cap** in the governance artifact (**FR-003**).
- **SC-003**: Zero required merge checks that existed for quality or security at baseline are removed without **FR-004** documentation; **check configuration** and declared pass-or-fail policy at merge time remain equivalent aside from faster duration. **Known nondeterministic checks** (flaky tests, timing-sensitive thresholds) are judged under the **organization’s flaky-test policy** if one exists; **SC-003** is **not** failed solely by benign rerun variance if that policy is **unchanged** from baseline. **Same inputs** means **same repository commit** and **same declared CI configuration** for the compared runs.
- **SC-004**: Within **fourteen calendar days** of completing changes, at least **three** engineers each submit one label: **faster**, **about the same**, or **slower** (anonymous or named per local practice). Let integer counts be **n_f**, **n_s**, **n_~** with **n = n_f+n_s+n_~ ≥ 3**. **Pass** if **n_s ≤ floor((n-1)/2)** (so slower is never a strict majority) **and** **n_f + n_~ ≥ ceil(n/2)** (e.g. **n=3** requires **n_f+n_~ ≥ 2**). **Abstentions** do not count toward **n** unless documented otherwise in the governance artifact.

## Assumptions

- Baseline metrics can be obtained from existing platform and integration histories (run duration logs, dashboards, or exports); if **access, retention, or secrets** block that, a **measurement sprint** MUST establish baselines before optimization work (**FR-001**).
- “Render services” and “GitHub” in the request refer to the project’s current hosted deployment builds and current continuous-integration provider; the specification stays outcome-focused so equivalent platforms would satisfy the same outcomes if migrated later.
- Optimization prioritizes developer-observed wait time and deployment build time without relaxing fraud, security, or correctness gates below organizational norms; **speed-only** changes are in scope, **coverage-reducing** shortcuts are not unless replaced under **FR-004**.
- Twenty percent is a default improvement bar; teams may adopt a **stricter** numeric goal in the implementation plan **without** conflicting **SC-001**/**SC-002**, provided the stricter goal is **documented in the governance artifact** and **FR-002**/**FR-003** minima are still met.
- **Implementation-plan detail** (for example, parallel jobs, cache keys) is delegated to **`plan.md`** / **`tasks.md`** and MUST **not** contradict **FR-004**, **FR-007**, or constitution-level contract-test obligations; any tension MUST be resolved by tightening implementation, not relaxing requirements here.

## Dependencies

- Organization **flaky-test policy** (if any) for interpreting **SC-003** and Edge Cases.
- Hosting platform and CI provider APIs or UIs for timestamps used in **Build phase** and **Median** definitions.
