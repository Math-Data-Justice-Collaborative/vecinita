#!/usr/bin/env python3
"""Update pipeline skills 00-17 with workflow-state-manager protocol and delta mode."""

from __future__ import annotations

import re
from pathlib import Path

SKILLS_ROOT = Path(__file__).resolve().parent.parent / ".cursor" / "skills"

SKILL_IDS = [
    "00-context",
    "01-requirements",
    "02-verify-plan",
    "03-plan-tooling",
    "04-tech-plan",
    "05-verify-tech",
    "06-tech-tooling",
    "07-build",
    "08-verify-build",
    "09-qa",
    "10-e2e",
    "11-verify-impl",
    "12-verify-deploy",
    "13-deploy-smoke",
    "14-hotfix",
    "15-service-health",
    "16-evolve",
    "17-retrospective",
]

DELTA_SECTIONS: dict[str, str] = {
    "00-context": """## Delta / feature-addition mode

When invoked from **16-evolve** or user adds features with new upstream paper/repo context:

- Run only for **new external context** not already in `docs/context-brief.md`.
- Merge findings into context-brief; do not regenerate unrelated sections.
- Tag agent updates with `evolve_cycle_id` and affected `feature_ids`.""",
    "01-requirements": """## Delta / feature-addition mode

When user adds features or `mode: delta` / active evolve cycle:

- Update **only** Fn sections and templates listed in `affected_artifacts`.
- Support **multiple Fn** in one cycle — one interview batch per feature or grouped by domain.
- Prefix decisions in `requirements-decisions.md` with `EV-NNN / Fnn`.
- Do not delete unrelated spec sections; mark deprecated Fn with status + ADR.""",
    "02-verify-plan": """## Delta / feature-addition mode

During evolve / feature addition:

- Run **full consistency pass** across all spec docs (contradictions hide at boundaries).
- Audit changed sections plus any doc referencing new/changed Fn or API identifiers.
- Block on `[Contradiction]` via AskQuestion before downstream stages proceed.""",
    "03-plan-tooling": """## Delta / feature-addition mode

When new features need guardrails:

- Add or update **rules, hooks, skills, agents** only for risks introduced by new Fn.
- Skip if pure code-only change behind existing plan-adherence rules (confirm via AskQuestion).
- Register **workflow-state-manager** in agents if not already present.""",
    "04-tech-plan": """## Delta / feature-addition mode

- **Append** tasks/milestones to `docs/execution-plan.md`; do not reset completed work.
- Tag new tasks with `evolve_cycle_id` and `feature_ids`.
- New phase/milestone only if scope warrants — user approves via AskQuestion.""",
    "05-verify-tech": """## Delta / feature-addition mode

- Verify **changed** technical statements and cross-doc consistency vs updated product specs.
- Focus audit on new Fn, new dependencies, and affected execution-plan tasks.""",
    "06-tech-tooling": """## Delta / feature-addition mode

Run when evolve cycle adds **new dependencies, hooks, CI steps, or formatters**:

- Update `docs/dependency-inventory.md` for new packages.
- Extend hooks/CI only for stack changes in cycle scope.""",
    "07-build": """## Delta / feature-addition mode

- Implement **only** pending tasks tagged with `evolve_cycle_id` or listed in cycle scope.
- Support multiple Fn in one branch (`evolve/{cycle-id}-{slug}`).
- PR title/body references evolve cycle and feature IDs.""",
    "08-verify-build": """## Delta / feature-addition mode

- Run at **07-build milestone boundaries** for delta tasks only.
- Scope verification to changed modules and tests tied to new Fn.""",
    "09-qa": """## Delta / feature-addition mode

- Scope QA report to **affected Fn**, apps, and journeys in the active evolve cycle.
- Do not re-audit entire codebase unless user requests full 09 pass.""",
    "10-e2e": """## Delta / feature-addition mode

- Add or extend E2E tests for **new user journeys** and acceptance scenarios per Fn.
- Run parallel with 09-qa; scope to cycle `feature_ids`.""",
    "11-verify-impl": """## Delta / feature-addition mode

- **Interactive approval per Fn** — present acceptance criteria status for each feature in cycle.
- Block deploy gate until user approves, denies, or modifies each new capability.""",
    "12-verify-deploy": """## Delta / feature-addition mode

- Pre-deploy checklist scoped to **changed surfaces** (API, UI, secrets, Modal) in this cycle.
- Re-run connectivity rows from connectivity-gates for browser-facing changes.""",
    "13-deploy-smoke": """## Delta / feature-addition mode

- Redeploy only services affected by new Fn; run H1-H5 for changed browser/API paths.
- Update deployment block via workflow-state-manager after smokes.""",
    "14-hotfix": """## Delta / feature-addition mode

If user request is **feature addition** (not a bug):

- workflow-state-manager will **block** — route to [16-evolve](16-evolve/SKILL.md).
- Hotfix remains surgical: one bug, one repro test, one fix.""",
    "15-service-health": """## Delta / feature-addition mode

If user request is **feature addition**:

- Recommend [16-evolve](16-evolve/SKILL.md) instead of health investigation.
- After feature deploy, optional health pass scoped to new Fn journeys.""",
    "16-evolve": """## Delta / feature-addition mode

This skill **orchestrates** delta mode for all child stages. See [reference.md](reference.md)
for multi-Fn cycles, intake batches, checkpoints, and routing matrix.""",
    "17-retrospective": """## Delta / feature-addition mode

If retrospective follows a feature cycle, mine `evolve_cycles[]` and feature IDs for evidence.
Does not implement features — process improvement only.""",
}

STATE_AGENT_LINE = (
    "**State agent:** [workflow-state-manager](../../agents/workflow-state-manager.md) "
    "— mandatory read/update.\n"
)

STATE_MGMT_REPLACEMENT = """## State management

**Agent protocol:** [workflow-state-agent-protocol.md](../workflow-state-agent-protocol.md).
**Stage key:** `stages.{key}`.

Invoke **workflow-state-manager** `read_context` before any other action; `update` after each
substep. **Do not** edit `workflow-state.yaml` directly.

"""


def stage_key(skill_id: str) -> str:
    return skill_id


def patch_skill(skill_id: str) -> bool:
    path = SKILLS_ROOT / skill_id / "SKILL.md"
    if not path.exists():
        print(f"SKIP missing: {path}")
        return False

    text = path.read_text(encoding="utf-8")
    original = text

    # Remove legacy 18-add-feature references
    text = text.replace("stages 00\u201318", "stages 00-17")
    text = text.replace("00\u201318", "00-17")
    text = re.sub(
        r"\[18-add-feature\]\([^\)]+\)",
        "[16-evolve](../16-evolve/SKILL.md)",
        text,
    )
    text = text.replace("18-add-feature", "16-evolve")

    if "**State agent:**" not in text and "**Cross-cutting:**" in text:
        text = text.replace(
            "**Cross-cutting:**",
            "**Cross-cutting:**",
            1,
        )
        # Insert state agent line after cross-cutting line
        text = re.sub(
            r"(\*\*Cross-cutting:\*\*[^\n]+\n)",
            r"\1" + STATE_AGENT_LINE,
            text,
            count=1,
        )

    # Replace State management opening if old canonical pattern
    key = stage_key(skill_id)
    if skill_id != "16-evolve":
        pattern = r"## State management\n\n\*\*Canonical:\*\*[^\n]+\n(?:Rules:[^\n]+\n)?"
        if re.search(pattern, text):
            repl = STATE_MGMT_REPLACEMENT.format(key=key)
            text = re.sub(pattern, repl, text, count=1)

    # Add delta section if missing
    delta = DELTA_SECTIONS.get(skill_id, "")
    if delta and "## Delta / feature-addition mode" not in text:
        # Insert before ## Workflow or ## Phase or first major section after state mgmt
        for anchor in (
            "\n## Workflow",
            "\n## Phase ",
            "\n## Throughput",
            "\n## Prerequisites",
            "\n## Hotfix",
            "\n## Purpose",
            "\n## Interactive",
            "\n## Output rules",
        ):
            if anchor.strip() in text:
                text = text.replace(anchor, "\n" + delta + anchor, 1)
                break
        else:
            # Append before Additional resources if exists
            if "\n## Additional resources" in text:
                text = text.replace(
                    "\n## Additional resources",
                    "\n" + delta + "\n## Additional resources",
                    1,
                )

    # Update frontmatter description for add feature triggers on key stages
    if skill_id == "01-requirements" and "add feature" not in text[:800].lower():
        text = text.replace(
            "requirements interview",
            "requirements interview, add feature delta specs",
            1,
        )

    if text != original:
        path.write_text(text, encoding="utf-8")
        print(f"UPDATED: {skill_id}")
        return True
    print(f"UNCHANGED: {skill_id}")
    return False


def main() -> None:
    for sid in SKILL_IDS:
        patch_skill(sid)


if __name__ == "__main__":
    main()
