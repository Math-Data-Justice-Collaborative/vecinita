# Research: Chat Message Presentation

## Decision 1: Render assistant output with safe markdown policy

- **Decision**: Use markdown rendering for assistant replies with explicit safety rules: strip/escape raw HTML, convert remote images to links, preserve tables with in-message horizontal scroll.
- **Rationale**: Matches clarified UX expectations while minimizing XSS/privacy risks and preserving readability for structured answers.
- **Alternatives considered**:
  - Plain text only: safest but fails rich readability goals.
  - Full HTML-enabled markdown: high security and layout risk.
  - Table-to-card transformation: harms fidelity of tabular responses.

## Decision 2: Reuse existing TypeScript libraries before introducing new dependencies

- **Decision**: Inventory currently installed frontend markdown/sanitization/utility libraries and build on them first; add new package only if a required behavior is not achievable with existing dependencies.
- **Rationale**: Reduces bundle churn and maintenance overhead, aligns with user request to use existing TS libraries where possible.
- **Alternatives considered**:
  - Introduce a new all-in-one renderer immediately: faster initial coding, but higher dependency risk.
  - Custom parser implementation: high complexity and ongoing maintenance burden.

## Decision 3: Validate rendering behavior with Playwright E2E

- **Decision**: Use Playwright for end-to-end chat rendering checks, including markdown blocks, table overflow behavior, remote image link conversion, and HTML stripping outcomes.
- **Rationale**: E2E testing verifies real browser behavior for layout and interaction details that unit tests can miss.
- **Alternatives considered**:
  - Unit tests only: insufficient confidence for layout/scroll behavior.
  - Snapshot-only visual tests: weaker behavioral guarantees for interactions.

## Decision 4: Keep tests deterministic and CI-friendly

- **Decision**: Scope Playwright to Chromium in CI by default, isolate tests from external network variability, and favor stable semantic locators.
- **Rationale**: Aligns with Playwright best practices for speed, reliability, and reproducible failures.
- **Alternatives considered**:
  - Full multi-browser matrix in every PR: high runtime cost for incremental UI change.
  - Unstubbed network-dependent tests: flaky under external variability.
