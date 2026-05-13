---
name: doc-verification
description: Verify documentation produced by the service-documentation skill by decomposing each document into verifiable statements, cross-referencing them against the codebase with a disprove-first stance, then interviewing the user for True/False/Modify verdicts. Use when verifying service docs, auditing specs under specs/authoritative/, or when the user mentions doc verification, spec verification, or documentation review.
---

# Documentation Verification

Systematically verify documentation produced by the `service-documentation` skill.
The agent assumes every statement is **false until proven true** by codebase evidence.

## Workflow

### Phase 0 — Identify the target

Determine which service documentation to verify. Look under `specs/authoritative/<service-name>/`
for the 14-document suite produced by `service-documentation`.

If multiple services exist, ask the user which to verify. If none exist, stop and tell
the user to run the `service-documentation` skill first.

### Phase 1 — Collect documents

Read every document in the service directory:

```
specs/authoritative/<service-name>/
├── 01-behavior.md
├── 02-data-models.md
├── 03-integration-points.md
├── 04-user-personas.md
├── 05-user-journeys.md
├── 06-data-flow.md
├── 07-architecture.md
├── 08-api-contract.md
├── 09-dependencies.md
├── 10-technical-decisions.md
├── 11-testing-plan.md
├── 12-infrastructure-plan.md
├── 13-modal-integration-plan.md
├── 14-render-integration-plan.md
└── diagrams/*.md
```

Skip any document that does not exist. Track which documents were found.

### Phase 2 — Decompose into verifiable statements

For **each document**, extract every claim that can be independently verified against
source code, config, or infrastructure. A verifiable statement is a single assertion
about one thing: a file path, an endpoint, a model field, a dependency, a behavior,
a config value, a deployment setting.

Ignore filler text, section headers, and formatting-only content.

#### Statement extraction rules

| Document | What to extract |
|----------|----------------|
| 01-behavior | Each claimed responsibility, trigger, outcome, boundary |
| 02-data-models | Each model name, field, type, constraint, relationship |
| 03-integration-points | Each service call direction, protocol, auth method |
| 04-user-personas | Each persona and their claimed role/access level |
| 05-user-journeys | Each step in each journey, claimed happy/failure paths |
| 06-data-flow | Each data source, transformation, destination, persistence claim |
| 07-architecture | Each component, framework, runtime, concurrency claim |
| 08-api-contract | Each endpoint, method, path, request/response shape, auth requirement |
| 09-dependencies | Each internal/external dependency, infrastructure requirement |
| 10-technical-decisions | Each decision, stated rationale, claimed alternatives |
| 11-testing-plan | Each test layer, tool, CI trigger, coverage claim |
| 12-infrastructure-plan | Each build config, deploy target, scaling setting |
| 13-modal-integration | Each Modal app, function, resource, volume, secret |
| 14-render-integration | Each Render service, plan, region, health check |
| diagrams/*.md | Each node, edge, and label in Mermaid diagrams |

For each statement, record:

- **ID**: `<doc-number>-S<n>` (e.g. `01-S3` = third statement from behavior doc)
- **Source document**: filename
- **Source line(s)**: line numbers where the claim appears
- **Statement**: the exact claim, quoted or closely paraphrased
- **Category**: `path`, `endpoint`, `model`, `config`, `behavior`, `dependency`, `infra`, `decision`, `diagram`

### Phase 3 — Disprove each statement

For every statement, **actively search the codebase for evidence that contradicts it**.
The agent's default stance is skepticism: assume the statement is wrong and look for proof.

#### Investigation procedure per statement

1. **Search for direct evidence** — Use Grep, Glob, SemanticSearch to find the code,
   config, or file the statement references.
2. **Check for contradictions** — Does the code say something different? Is the file
   missing? Is the field named differently? Is the endpoint on a different path?
3. **Check for staleness** — Has the code changed since the doc was generated?
   Look at recent git history for the referenced files.
4. **Assign a verdict**:

| Verdict | Meaning |
|---------|---------|
| **CONFIRMED** | Codebase evidence supports the statement |
| **CONTRADICTED** | Codebase evidence directly contradicts the statement |
| **UNVERIFIABLE** | No evidence found for or against (missing code, external claim) |
| **STALE** | Was true but code has since changed |

5. **Record sources** — For every verdict, list the specific files and line numbers
   that support the conclusion. Use code reference format:
   ```
   Source: apis/gateway/src/routes/embed.py:42-58
   Finding: Endpoint is POST /v1/embed, not GET /embed as documented
   ```

### Phase 4 — Present findings and interview user

Process documents **one at a time**. For each document:

1. **Show the statement table** with columns:

   | ID | Statement | Agent Verdict | Evidence | Sources |
   |----|-----------|---------------|----------|---------|

2. **For each CONTRADICTED or STALE statement**, present the conflict using AskQuestion:

   ```
   Statement 08-S5: "The /v1/embed endpoint accepts GET requests"
   
   Agent finding: CONTRADICTED
   Evidence: The route handler at apis/gateway/src/routes/embed.py:42
   registers a POST handler, not GET.
   
   Options: [True — keep as documented] [False — statement is wrong] [Modify — rewrite]
   ```

3. **For each UNVERIFIABLE statement**, present it similarly but note the lack of evidence.

4. **For CONFIRMED statements**, present as a batch summary. Only ask the user to
   review if the confirmation count is small enough (< 10). Otherwise summarize:
   "X statements confirmed with codebase evidence — see table above."

5. **If the user selects Modify**, ask them to provide the corrected text or offer
   a suggested correction based on what the code actually shows.

6. After the user responds, **record their verdict** alongside the agent verdict.

### Phase 5 — Generate verification report

After all documents are reviewed, produce a verification report at:

```
specs/authoritative/<service-name>/VERIFICATION-REPORT.md
```

#### Report structure

```markdown
# Verification Report: <Service Name>

> Verified: YYYY-MM-DD

## Summary

| Metric | Count |
|--------|-------|
| Total statements | N |
| Confirmed (agent + user) | N |
| Contradicted | N |
| Modified by user | N |
| Marked false by user | N |
| Unverifiable | N |

## Accuracy score

**X%** of verifiable statements confirmed against codebase.

## Document-level results

### 01-behavior.md — X/Y confirmed

| ID | Statement | Agent Verdict | User Verdict | Evidence | Sources |
|----|-----------|---------------|--------------|----------|---------|
| ... | ... | ... | ... | ... | ... |

(Repeat for each document)

## Corrections required

List every statement the user marked False or Modify, with:
- The original text
- The agent's finding
- The user's correction or rejection reason
- The source files that inform the fix

## Recommended doc updates

For each correction, provide the exact edit needed (file, line, old text, new text)
so the user can apply fixes or hand them to the service-documentation skill.
```

### Phase 6 — Offer to apply corrections

After generating the report, ask the user:

```
Options:
[Apply all corrections to docs now]
[Apply selected corrections]
[Save report only — I'll fix docs later]
```

If the user chooses to apply, use StrReplace to update each document with the
corrected text from the verification report.

## Behavioral rules

- **Disprove first**: Always try to find evidence against a statement before concluding
  it is true. Do not rubber-stamp documentation.
- **Cite sources**: Every verdict must include at least one file path and line range.
  Never say "this looks correct" without pointing to code.
- **Surface conflicts**: If agent verdict and user verdict disagree, note the
  disagreement in the report but respect the user's final decision.
- **Batch efficiently**: Group CONFIRMED statements to avoid question fatigue. Focus
  user attention on contradictions and gaps.
- **One document at a time**: Do not dump all findings at once. Process each document,
  get user verdicts, then move to the next.
- **Git-aware**: When checking for staleness, use `git log --oneline -5 <file>` to
  see if referenced files changed after the doc's `Auto-generated` date.
