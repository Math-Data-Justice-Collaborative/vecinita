"""Regression: Publish Wiki CI must not pass --include-operator=false to argparse."""

from __future__ import annotations

from pathlib import Path

import pytest
from scripts.docs.sync_github_wiki import main, parse_args

REPO_ROOT = Path(__file__).resolve().parents[2]
WORKFLOW = REPO_ROOT / ".github/workflows/publish-wiki.yml"
ARGPARSE_USAGE_EXIT = 2


def test_ci_invocation_with_include_operator_equals_false_exits_2() -> None:
    """Matches Publish Wiki CI failure before fix (run 28749720275)."""
    with pytest.raises(SystemExit) as exc_info:
        parse_args(["--dry-run", "--include-operator=false"])
    assert exc_info.value.code == ARGPARSE_USAGE_EXIT


def test_no_include_operator_dry_run_succeeds(capsys: pytest.CaptureFixture[str]) -> None:
    """Workflow-equivalent invocation must build wiki pages without error."""
    exit_code = main(["--dry-run", "--no-include-operator"])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "Built" in captured.out


def test_publish_wiki_workflow_uses_boolean_flags_not_equals_syntax() -> None:
    r"""Guard against regressing to --include-operator="$INCLUDE_OP" in CI."""
    content = WORKFLOW.read_text(encoding="utf-8")
    assert '--include-operator="$INCLUDE_OP"' not in content
    assert "--include-operator=$INCLUDE_OP" not in content
    assert "--include-operator=" not in content
    assert "--no-include-operator" in content
