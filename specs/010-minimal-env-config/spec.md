# Feature Specification: Minimal environment configuration

**Feature Branch**: `012-minimal-env-config`  
**Created**: 2026-04-23  
**Status**: Draft  
**Input**: User description: "We're going to simplify the .env variables to a minimal set down from this please"

## Clarifications

### Session 2026-04-23

- Q: When someone still uses deprecated or duplicate environment names after consolidation, what should the product behavior be? → A: **Soft deprecation (Option C)** — legacy names keep working for a **published transition window**; users see a **clear, non-secret-leaking** warning that points to the **canonical** name; alias support then ends per the **migration documentation**.
- Q: What should “single canonical” mean for where that list lives? → A: **Option A** — **one authoritative root** committed example file holds the full minimal list and profiles; **component-specific** examples stay **minimal** and **point** to the root for shared keys.
- Q: For the default local path, what is the rule for database connectivity in the **required** minimal set? → A: **Option B** — **Supabase-facing** settings and a **direct PostgreSQL** connection both stay **required** whenever the **published setup guide** promises those default local flows **without** enabling an extra profile.
- Q: For SC-002’s “before” baseline, how should required-name counts be defined? → A: **Option B** — baseline = **deduplicated union** of names **treated as required** for default local onboarding across **all** committed examples **and** the **prior** setup guide, recorded in the migration documentation.
- Q: Where should the migration mapping and baseline methodology live? → A: **Option C** — a **short** summary and **prominent link** in the **primary onboarding entry point** (README or setup guide), **plus** a **dedicated** document for full tables, deprecation windows, and baseline methodology.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Fast local setup with a short required list (Priority: P1)

A new contributor wants to run the main product locally without reading a long, duplicated list of settings. They open the project’s setup guide and the **repository-root** canonical example file, set only what is marked **required**, and reach a working local session for the default developer path (chat experience and data-management flows that the repo documents as standard).

**Why this priority**: This is the primary pain of an oversized environment file—onboarding delay, copy-paste errors, and uncertainty about what is actually necessary.

**Independent Test**: Follow only the published “minimal setup” instructions on a clean machine; confirm the documented default flows start without adding undeclared settings.

**Acceptance Scenarios**:

1. **Given** a contributor with no prior project-specific settings, **When** they configure only the variables labeled required in the **root** canonical example and guide, **Then** they can complete the documented default local flows without hunting for missing names.
2. **Given** the **root** canonical example, **When** a reviewer inspects it, **Then** every entry has a plain-language purpose and is classified as required for default local use or optional for a named capability profile.
3. **Given** a **component-specific** committed example, **When** a reviewer opens it, **Then** it stays **minimal** and **directs** readers to the **root** example for shared keys (no competing full duplicate list).

---

### User Story 2 - Clear optional “profiles” instead of a flat wall of keys (Priority: P2)

A maintainer wants optional integrations (extra providers, hosted hooks, advanced jobs) grouped so that teams enable only what they need. Optional settings are documented in short add-on sections rather than mixed into the same flat list as essentials.

**Why this priority**: Reduces noise for the majority while preserving power users—supports operational simplicity without losing capability.

**Independent Test**: Disable all optional profiles; default local path still works. Enable one profile; only that profile’s variables need to be set for that capability.

**Acceptance Scenarios**:

1. **Given** a developer who needs only the default path, **When** they ignore optional profiles entirely, **Then** they are not blocked by variables that belong to optional capabilities.
2. **Given** a developer enabling a specific optional capability, **When** they follow that profile’s checklist, **Then** they can turn on that capability without configuring unrelated optional keys.

---

### User Story 3 - Safer handoff of examples (Priority: P3)

An operator or contributor shares example configuration with teammates or in docs. Examples never contain real secrets; redundant copies of the same secret under different names are eliminated so people are less likely to paste the wrong variable into the wrong slot.

**Why this priority**: Aligns with responsible stewardship and fewer accidental leaks when simplifying names.

**Independent Test**: Automated or manual audit of committed example files shows placeholders only; a mapping note explains any renamed or retired keys for existing installations.

**Acceptance Scenarios**:

1. **Given** committed example configuration files, **When** an auditor searches for patterns that indicate live secrets, **Then** none are present in those files.
2. **Given** a teammate upgrading from a previous long list, **When** they read the **migration documentation**, **Then** they can translate old names to the new minimal names (or confirm retirement) without guesswork.
3. **Given** a developer using a **deprecated** name inside the transition window, **When** they start a documented default local flow, **Then** the flow still succeeds and they receive a **warning** that identifies the **canonical** name without echoing secret material.
4. **Given** a contributor reading the **primary onboarding** env section, **When** they follow the **link** to migration documentation, **Then** they reach the **full** mapping, baseline counts, and alias timeline without searching the repository.

---

### Edge Cases

- A developer still has an old local file with **deprecated names**: during the **published transition window**, loaders **accept** mapped legacy names, emit a **warning** that names the **canonical** replacement (no secret values in messages), and documentation states when aliases **stop** being accepted.
- A flow needs a setting that was removed as “duplicate”: the consolidation must not drop a genuinely distinct capability; if two names meant the same thing, one canonical name remains.
- Optional profile partially configured: user gets a clear, capability-scoped hint about what is missing rather than a generic failure.
- Hosted deployment platforms that inject their own settings: documented minimal set states what the repo owns vs what the platform supplies.
- A contributor follows a **component-specific** example that predates consolidation: they are routed to the **root** canonical list so they do not maintain two divergent full copies.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The project MUST publish a **single canonical** list of environment settings for default local development, each with a short plain-language description, in **one authoritative committed example file at the repository root**. Any **component-specific** committed examples MUST remain **minimal** and MUST **point** contributors to that **root** file for shared keys so onboarding has **one** source of truth.
- **FR-002**: Each setting in that canonical list MUST be classified as **required** for the default local path or **optional** under a named capability profile (for example: optional analytics, optional hosted deploy hooks, optional alternate model providers).
- **FR-003**: The **root** canonical example and every other committed example file MUST contain **placeholders only**—no real API keys, tokens, passwords, or connection strings with live values.
- **FR-004**: The set of distinct names required for the default local path MUST be **materially smaller** than the **pre-change baseline** (target: at least half as many required names, excluding pure documentation comments), while preserving the same default behaviors the setup guide promises. The **pre-change baseline** MUST be computed as the **deduplicated union** of names **treated as required** for default local onboarding across **all** committed examples and the **prior** setup guide, and that methodology plus counts MUST be recorded in the **migration documentation** (see **FR-010**).
- **FR-005**: Where two or more historical names represented the same intent, the specification MUST require **one canonical name** and a documented mapping or deprecation path for the others.
- **FR-006**: Setup documentation MUST be updated so a new contributor never needs to cross-reference multiple conflicting lists to know what to set first. The **primary onboarding entry point** MUST surface where to find **migration documentation** (summary + link per **FR-010**).
- **FR-007**: Any setting that remains only for narrow automation or hosted pipelines MUST be isolated into its profile section so it does not appear as required for default local onboarding.
- **FR-008**: For every renamed or retired duplicate, the project MUST document a **migration mapping** and a **transition window** during which **legacy names remain accepted**; during that window, configuration resolution MUST surface a **non-secret-leaking** notice directing users to the **canonical** name, and MUST document the **end of alias support** so upgrades are predictable. Those details MUST appear in the **migration documentation** (see **FR-010**).
- **FR-009**: For the **default local path**, whenever the **published setup guide** promises both **Supabase-backed** access and **direct PostgreSQL** access **without** asking the reader to enable an optional profile, the **required** minimal set MUST include the variables needed for **both**; neither may be moved behind a profile unless the guide is updated so the default path no longer depends on it.
- **FR-010**: **Migration documentation** MUST exist as a **dedicated** artifact containing the full **migration mapping**, **baseline** methodology and counts, **transition window**, and **end-of-alias** commitments. The **primary onboarding entry point** (README or equivalent setup guide section for environment setup) MUST include a **brief summary** of what changed and a **prominent link** to that dedicated artifact.

### Key Entities *(include if feature involves data)*

- **Environment setting**: A named piece of configuration supplied at runtime; has description, requirement class (required vs optional profile), and sensitivity (secret vs non-secret).
- **Capability profile**: A named bundle of optional settings that unlock a specific integration or workflow without expanding the required core set.
- **Canonical template**: The **single root** committed example file that lists **all** names (required and profile-grouped optional) with placeholders—the **authoritative** structure for onboarding; subsidiary examples only supplement with pointers.
- **Migration documentation**: The **dedicated** artifact holding the full **migration mapping**, **baseline** methodology and counts, and **alias timeline**; discoverable via **summary + link** from the **primary onboarding entry point**.
- **Migration mapping**: The portion of **migration documentation** that pairs retired or duplicate names to canonical replacements, **including** how the **pre-change baseline** for required-name counts was derived (union of examples + prior guide) and the **computed counts**.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: On a clean setup, a new contributor can identify every **required** setting for the default local path in **under five minutes** using only the updated setup guide and the **root** canonical example file.
- **SC-002**: The count of **required** names for that default path drops by **at least 50%** compared to the **pre-change baseline**, where the baseline is the **deduplicated union** of names treated as **required** for default local onboarding across **all** committed examples and the **prior** setup guide, with the methodology and counts **documented in the migration documentation** (linked from onboarding per **FR-010**).
- **SC-003**: **100%** of committed configuration examples contain no live credential material when checked against the project’s published safe-example checklist (human or automated review acceptable).
- **SC-004**: **90%** of trial users in a quick internal hallway test (three or more participants) report they understand “what is required vs optional” without asking a maintainer (measured with a one-question survey after following the guide).

## Assumptions

- “Default local path” means the flows the repository already documents for standard development (chat application and data-management stack), not every possible integration in the wider ecosystem.
- Some secrets will always exist; minimization is about **fewer names and clearer grouping**, not removing authentication entirely.
- Production and hosted environments may still inject additional values at the platform level; the spec focuses on what humans maintain in project-owned templates and docs.
- **Deprecation policy**: **Soft deprecation** is required—legacy names work for a **documented transition window** with **non-secret-leaking** warnings toward **canonical** names; **migration documentation** MUST state when aliases are removed.
- **Migration discoverability**: **Option C** — onboarding carries a **short** env-change summary and **link**; the **dedicated migration documentation** holds full tables and baseline math.
- **Canonical location**: The **full** variable catalog lives in the **repository-root** example file; other committed examples are **short** and **reference** the root for shared configuration.
- **Default local connectivity**: If the guide’s default local flows use **both** Supabase client configuration and a **direct Postgres** URL, **both** stay **required** in the minimal set until documentation intentionally changes that promise.
- **SC-002 baseline**: The “before” required-name count uses the **deduplicated union** across **all** committed examples and the **prior** setup guide, not a single file in isolation, so the metric matches real onboarding sprawl.
