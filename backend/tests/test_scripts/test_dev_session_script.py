"""Regression checks for local dev launcher script modes."""

from pathlib import Path

SCRIPT_PATH = Path("run/dev-session.sh")
if not SCRIPT_PATH.exists():
    SCRIPT_PATH = Path("../run/dev-session.sh")


def _script_text() -> str:
    return SCRIPT_PATH.read_text(encoding="utf-8")


def test_dev_session_script_exists() -> None:
    assert SCRIPT_PATH.exists(), "Expected run/dev-session.sh to exist"


def test_dev_session_defaults_to_single_terminal_mode() -> None:
    content = _script_text()
    assert "start_single_terminal_session" in content
    assert 'echo "Starting local dev stack in single-terminal cascading log mode"' in content
    assert 'echo "Press Ctrl+C to stop all services"' in content
    assert 'run_with_prefix "frontend"' in content


def test_dev_session_supports_legacy_tmux_mode() -> None:
    content = _script_text()
    assert "start-tmux)" in content
    assert "start_session" in content
    assert 'tmux new-session -d -s "$SESSION_NAME" -n dev' in content


def test_dev_session_waits_for_frontend_before_attach() -> None:
    content = _script_text()
    assert "wait_for_http_ready()" in content
    assert (
        'wait_for_http_ready "Frontend" "http://localhost:5173/" "${DEV_FRONTEND_READY_TIMEOUT:-180}"'
        in content
    )

    wait_idx = content.find(
        'wait_for_http_ready "Frontend" "http://localhost:5173/" "${DEV_FRONTEND_READY_TIMEOUT:-180}"'
    )
    attach_idx = content.rfind('tmux attach -t "$SESSION_NAME"')
    assert wait_idx != -1
    assert attach_idx != -1
    assert wait_idx < attach_idx, "Frontend readiness check must run before tmux attach"


def test_dev_session_resets_existing_state_before_start() -> None:
    content = _script_text()
    assert "reset_existing_state_if_needed" in content
    assert "reset_existing_state_if_needed" in content
    assert "clear_managed_ports" in content
    assert 'tmux kill-session -t "$SESSION_NAME"' in content
    assert "Managed dev ports already in use:" in content
    start_idx = content.find("reset_existing_state_if_needed")
    new_session_idx = content.find('tmux new-session -d -s "$SESSION_NAME" -n dev')
    assert start_idx != -1
    assert new_session_idx != -1
    assert start_idx < new_session_idx


def test_dev_session_manages_expected_ports() -> None:
    content = _script_text()
    assert "managed_ports()" in content
    assert 'echo "5173 8000 8001 8002 8004"' in content
    assert "kill -9 $pids" in content


def test_dev_session_warns_instead_of_exiting_on_readiness_timeout() -> None:
    content = _script_text()
    assert "frontend readiness check timed out; attaching" in content
    assert "gateway readiness check timed out; attaching" in content


def test_dev_session_does_not_quote_proxy_token_parameter_expansion() -> None:
    content = _script_text()
    assert "PROXY_AUTH_TOKEN='\\${PROXY_AUTH_TOKEN:-vecinita-local-proxy-token}'" not in content
    assert 'resolve_proxy_auth_token()' in content
    assert 'proxy_auth_token="$(resolve_proxy_auth_token)"' in content
    assert "PROXY_AUTH_TOKEN='$proxy_auth_token'" in content
