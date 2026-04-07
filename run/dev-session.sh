#!/usr/bin/env bash

set -euo pipefail

# Resolve to repository root (parent of run/), not run/ itself.
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SESSION_NAME="vecinita-dev"
DEFAULT_MODAL_MODEL_URL="https://vecinita--vecinita-model-api.modal.run"
DEFAULT_MODAL_EMBEDDING_URL="https://vecinita--vecinita-embedding-web-app.modal.run"

DEV_CHILD_PIDS=()
DEV_RUNNING=0
UVICORN_RELOAD_ARGS=(
  --reload
  --reload-dir src
  --reload-exclude '.mypy_cache/*'
  --reload-exclude '.pytest_cache/*'
  --reload-exclude '.ruff_cache/*'
  --reload-exclude '.venv/*'
  --reload-exclude 'logs/*'
  --reload-exclude 'build/*'
  --reload-exclude 'coverage*'
  --reload-exclude '*.pyc'
)

uvicorn_reload_args_string() {
  local escaped_args=()
  local arg

  for arg in "${UVICORN_RELOAD_ARGS[@]}"; do
    escaped_args+=("$(printf '%q' "$arg")")
  done

  printf '%s' "${escaped_args[*]}"
}

trim_spaces() {
  local value="$1"
  value="${value#${value%%[![:space:]]*}}"
  value="${value%${value##*[![:space:]]}}"
  printf '%s' "$value"
}

read_env_var_from_file() {
  local file_path="$1"
  local var_name="$2"

  if [[ ! -f "$file_path" ]]; then
    return 1
  fi

  local line
  line="$(grep -E "^${var_name}[[:space:]]*=" "$file_path" | tail -n1 || true)"
  if [[ -z "$line" ]]; then
    return 1
  fi

  local value="${line#*=}"
  value="$(trim_spaces "$value")"
  if [[ ${#value} -ge 2 ]]; then
    if [[ ("${value:0:1}" == '"' && "${value: -1}" == '"') || ("${value:0:1}" == "'" && "${value: -1}" == "'") ]]; then
      value="${value:1:${#value}-2}"
    fi
  fi

  if [[ -n "$value" ]]; then
    printf '%s' "$value"
    return 0
  fi

  return 1
}

resolve_local_embed_token() {
  local env_keys=(
    "EMBEDDING_SERVICE_AUTH_TOKEN"
    "MODAL_TOKEN_SECRET"
    "MODAL_API_KEY"
    "MODAL_API_TOKEN_SECRET"
  )

  local key
  for key in "${env_keys[@]}"; do
    local value="${!key:-}"
    if [[ -n "$value" ]]; then
      printf '%s' "$value"
      return 0
    fi
  done

  local env_files=("$ROOT_DIR/backend/.env" "$ROOT_DIR/.env")
  local env_file
  for env_file in "${env_files[@]}"; do
    for key in "${env_keys[@]}"; do
      if value="$(read_env_var_from_file "$env_file" "$key")"; then
        printf '%s' "$value"
        return 0
      fi
    done
  done

  printf '%s' "dev-embed-token"
}

resolve_env_value() {
  local fallback="${1:-}"
  shift || true

  local key
  for key in "$@"; do
    local value="${!key:-}"
    if [[ -n "$value" ]]; then
      printf '%s' "$value"
      return 0
    fi
  done

  local env_files=("$ROOT_DIR/backend/.env" "$ROOT_DIR/.env")
  local env_file
  for env_file in "${env_files[@]}"; do
    for key in "$@"; do
      if value="$(read_env_var_from_file "$env_file" "$key")"; then
        printf '%s' "$value"
        return 0
      fi
    done
  done

  printf '%s' "$fallback"
}


print_usage() {
  cat <<EOF
Usage: ./run/dev-session.sh [start|attach|stop|restart]

Commands:
  start       Start all local dev services in one terminal with cascading logs (default)
  start-tmux  Start all local dev services in a tmux session (legacy)
  attach      Attach to the existing tmux session
  stop        Stop dev services
  restart     Stop and start again
EOF
}

require_command() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Missing required command: $cmd"
    exit 1
  fi
}

managed_ports() {
  echo "5173 8000 8001 8004"
}

list_port_pids() {
  local port="$1"

  if command -v lsof >/dev/null 2>&1; then
    lsof -ti tcp:"$port" 2>/dev/null || true
    return 0
  fi

  if command -v fuser >/dev/null 2>&1; then
    fuser -n tcp "$port" 2>/dev/null || true
    return 0
  fi

  return 0
}

port_in_use() {
  local port="$1"
  if command -v lsof >/dev/null 2>&1; then
    lsof -ti tcp:"$port" >/dev/null 2>&1
    return $?
  fi

  if command -v fuser >/dev/null 2>&1; then
    fuser -n tcp "$port" >/dev/null 2>&1
    return $?
  fi

  if command -v ss >/dev/null 2>&1; then
    ss -ltn "( sport = :$port )" 2>/dev/null | grep -q ":$port "
    return $?
  fi

  return 1
}

has_busy_managed_ports() {
  local required_ports=($(managed_ports))
  local busy_ports=()

  for port in "${required_ports[@]}"; do
    if port_in_use "$port"; then
      busy_ports+=("$port")
    fi
  done

  if [[ ${#busy_ports[@]} -gt 0 ]]; then
    echo "${busy_ports[*]}"
    return 0
  fi

  return 1
}

clear_managed_ports() {
  local ports=($(managed_ports))

  for port in "${ports[@]}"; do
    local pids
    pids="$(list_port_pids "$port")"

    if [[ -n "$pids" ]]; then
      echo "Clearing port $port (PID(s): $pids)"
      kill -9 $pids 2>/dev/null || true
    fi
  done
}

reset_existing_state_if_needed() {
  local reset_required=1

  if tmux_has_session; then
    echo "Session '$SESSION_NAME' already exists. Restarting managed dev session..."
    tmux kill-session -t "$SESSION_NAME" || true
    reset_required=0
  fi

  local busy_ports
  busy_ports="$(has_busy_managed_ports || true)"
  if [[ -n "$busy_ports" ]]; then
    echo "Managed dev ports already in use: $busy_ports"
    reset_required=0
  fi

  if [[ "$reset_required" -eq 0 ]]; then
    clear_managed_ports
  fi
}

wait_for_http_ready() {
  local service_name="$1"
  local url="$2"
  local timeout_seconds="$3"

  if ! command -v curl >/dev/null 2>&1; then
    # Skip HTTP-level readiness checks when curl is not available.
    return 0
  fi

  local elapsed=0
  while [[ "$elapsed" -lt "$timeout_seconds" ]]; do
    if curl -fsS -m 2 "$url" >/dev/null 2>&1; then
      echo "$service_name ready: $url"
      return 0
    fi

    if (( elapsed % 5 == 0 )); then
      echo "Waiting for $service_name... ($elapsed/${timeout_seconds}s)"
    fi

    sleep 1
    elapsed=$((elapsed + 1))
  done

  echo "Timed out waiting for $service_name at $url"
  return 1
}

probe_endpoint_status() {
  local service_name="$1"
  local url="$2"

  if ! command -v curl >/dev/null 2>&1; then
    return 0
  fi

  local status
  status="$(curl -sS -o /dev/null -m 4 -w '%{http_code}' "$url" || echo 000)"
  case "$status" in
    2*|3*|401|403)
      echo "$service_name reachable: $url (status $status)"
      return 0
      ;;
    *)
      echo "Warning: $service_name check failed: $url (status $status)"
      return 1
      ;;
  esac
}

wait_for_remote_endpoint_ready() {
  local service_name="$1"
  local url="$2"
  local timeout_seconds="$3"

  if ! command -v curl >/dev/null 2>&1; then
    return 0
  fi

  local elapsed=0
  while [[ "$elapsed" -lt "$timeout_seconds" ]]; do
    local status
    status="$(curl -sS -o /dev/null -m 8 -w '%{http_code}' "$url" || echo 000)"
    case "$status" in
      2*|3*|401|403)
        echo "$service_name reachable: $url (status $status)"
        return 0
        ;;
      *)
        if (( elapsed % 10 == 0 )); then
          echo "Waiting for $service_name cold-start... ($elapsed/${timeout_seconds}s, status $status)"
        fi
        ;;
    esac

    sleep 2
    elapsed=$((elapsed + 2))
  done

  echo "Warning: $service_name check failed after ${timeout_seconds}s: $url"
  return 1
}

run_remote_endpoint_preflight_checks() {
  local model_api_url
  model_api_url="$(resolve_env_value "$DEFAULT_MODAL_MODEL_URL" VECINITA_MODEL_API_URL MODAL_OLLAMA_ENDPOINT OLLAMA_BASE_URL)"
  local embedding_api_url
  embedding_api_url="$(resolve_env_value "$DEFAULT_MODAL_EMBEDDING_URL" VECINITA_EMBEDDING_API_URL MODAL_EMBEDDING_ENDPOINT EMBEDDING_SERVICE_URL)"
  local endpoint_timeout
  endpoint_timeout="${DEV_REMOTE_ENDPOINT_READY_TIMEOUT:-120}"

  echo ""
  echo "Running direct endpoint preflight checks..."

  if [[ -n "$model_api_url" ]]; then
    wait_for_remote_endpoint_ready "Model Endpoint" "${model_api_url%/}/health" "$endpoint_timeout" || true
  fi

  if [[ -n "$embedding_api_url" ]]; then
    wait_for_remote_endpoint_ready "Embedding Endpoint" "${embedding_api_url%/}/health" "$endpoint_timeout" || true
  fi
}

tmux_has_session() {
  if ! command -v tmux >/dev/null 2>&1; then
    return 1
  fi

  tmux has-session -t "$SESSION_NAME" 2>/dev/null
}

print_prefixed() {
  local service_name="$1"
  while IFS= read -r line; do
    printf '[%s] %s\n' "$service_name" "$line"
  done
}

run_with_prefix() {
  local service_name="$1"
  shift

  (
    "$@" 2>&1 | print_prefixed "$service_name"
  ) &
  DEV_CHILD_PIDS+=("$!")
}

cleanup_single_terminal() {
  if [[ "$DEV_RUNNING" -eq 0 ]]; then
    return 0
  fi

  DEV_RUNNING=0
  trap - INT TERM EXIT

  echo ""
  echo "Stopping local dev services..."

  for pid in "${DEV_CHILD_PIDS[@]:-}"; do
    if kill -0 "$pid" >/dev/null 2>&1; then
      kill "$pid" >/dev/null 2>&1 || true
    fi
  done

  sleep 1
  for pid in "${DEV_CHILD_PIDS[@]:-}"; do
    if kill -0 "$pid" >/dev/null 2>&1; then
      kill -9 "$pid" >/dev/null 2>&1 || true
    fi
  done

  clear_managed_ports
  echo "Dev services stopped."
}

start_single_terminal_session() {
  require_command uv
  require_command npm
  reset_existing_state_if_needed

  local embed_token
  embed_token="$(resolve_local_embed_token)"
  local uvicorn_reload_args
  uvicorn_reload_args="$(uvicorn_reload_args_string)"

  echo ""
  echo "Starting local dev stack in single-terminal cascading log mode"
  echo "Press Ctrl+C to stop all services"
  echo ""

  DEV_RUNNING=1
  trap cleanup_single_terminal INT TERM EXIT

  run_with_prefix "embedding" bash -lc "cd '$ROOT_DIR/backend' && EMBEDDING_SERVICE_AUTH_TOKEN='$embed_token' uv run -m uvicorn src.embedding_service.main:app --host 0.0.0.0 --port 8001 ${uvicorn_reload_args}"
  run_with_prefix "agent" bash -lc "cd '$ROOT_DIR/backend' && ANONYMIZED_TELEMETRY='false' OLLAMA_BASE_URL=\"\${VECINITA_MODEL_API_URL:-\${MODAL_OLLAMA_ENDPOINT:-\${OLLAMA_BASE_URL:-$DEFAULT_MODAL_MODEL_URL}}}\" OLLAMA_API_KEY=\"\${OLLAMA_API_KEY:-\${MODAL_API_KEY:-\${MODAL_API_TOKEN_SECRET:-\${MODAL_TOKEN_SECRET:-}}}}\" EMBEDDING_SERVICE_URL=\"\${VECINITA_EMBEDDING_API_URL:-\${MODAL_EMBEDDING_ENDPOINT:-\${EMBEDDING_SERVICE_URL:-$DEFAULT_MODAL_EMBEDDING_URL}}}\" EMBEDDING_SERVICE_AUTH_TOKEN='$embed_token' DEFAULT_PROVIDER='ollama' DEFAULT_MODEL='' uv run -m uvicorn src.agent.main:app --host 0.0.0.0 --port 8000 ${uvicorn_reload_args}"
  run_with_prefix "gateway" bash -lc "cd '$ROOT_DIR/backend' && AGENT_SERVICE_URL='http://localhost:8000' EMBEDDING_SERVICE_URL=\"\${VECINITA_EMBEDDING_API_URL:-\${MODAL_EMBEDDING_ENDPOINT:-\${EMBEDDING_SERVICE_URL:-$DEFAULT_MODAL_EMBEDDING_URL}}}\" EMBEDDING_SERVICE_AUTH_TOKEN='$embed_token' ANONYMIZED_TELEMETRY='false' DEV_ADMIN_ENABLED='true' DEV_ADMIN_BEARER_TOKEN='vecinita-dev-admin-token-2026' DEMO_MODE='false' uv run -m uvicorn src.api.main:app --host 0.0.0.0 --port 8004 ${uvicorn_reload_args}"
  run_with_prefix "frontend" bash -lc "cd '$ROOT_DIR/frontend' && npm run dev -- --host 0.0.0.0 --port 5173"

  if ! wait_for_http_ready "Frontend" "http://localhost:5173/" "${DEV_FRONTEND_READY_TIMEOUT:-180}"; then
    echo "Warning: frontend readiness check timed out; inspect logs above."
  fi

  if ! wait_for_http_ready "Gateway" "http://localhost:8004/health" "${DEV_GATEWAY_READY_TIMEOUT:-180}"; then
    echo "Warning: gateway readiness check timed out; inspect logs above."
  fi

  run_remote_endpoint_preflight_checks

  echo ""
  echo "Dev stack is running with merged logs."
  echo ""

  while true; do
    if ! wait -n; then
      echo "A service exited unexpectedly. Check logs above."
      exit 1
    fi
  done
}

start_session() {
  require_command tmux
  require_command uv
  require_command npm
  reset_existing_state_if_needed

  local embed_token
  embed_token="$(resolve_local_embed_token)"
  local uvicorn_reload_args
  uvicorn_reload_args="$(uvicorn_reload_args_string)"

  tmux new-session -d -s "$SESSION_NAME" -n dev
  tmux set-option -t "$SESSION_NAME" -g mouse on
  tmux set-option -t "$SESSION_NAME" -g history-limit 100000
  tmux set-window-option -t "$SESSION_NAME":dev mode-keys vi

  tmux split-window -h -t "$SESSION_NAME":dev.0
  tmux split-window -v -t "$SESSION_NAME":dev.0
  tmux split-window -v -t "$SESSION_NAME":dev.1
  tmux split-window -v -t "$SESSION_NAME":dev.2
  tmux split-window -v -t "$SESSION_NAME":dev.3
  tmux select-layout -t "$SESSION_NAME":dev tiled

  tmux send-keys -t "$SESSION_NAME":dev.0 "cd '$ROOT_DIR/backend' && echo '[embedding] EMBEDDING_SERVICE_AUTH_TOKEN=$embed_token uv run -m uvicorn src.embedding_service.main:app --port 8001 ${uvicorn_reload_args}' && EMBEDDING_SERVICE_AUTH_TOKEN='$embed_token' uv run -m uvicorn src.embedding_service.main:app --host 0.0.0.0 --port 8001 ${uvicorn_reload_args}" C-m
  tmux send-keys -t "$SESSION_NAME":dev.1 "cd '$ROOT_DIR/backend' && echo '[agent] uv run -m uvicorn src.agent.main:app --port 8000 ${uvicorn_reload_args}' && ANONYMIZED_TELEMETRY='false' OLLAMA_BASE_URL=\"\${VECINITA_MODEL_API_URL:-\${MODAL_OLLAMA_ENDPOINT:-\${OLLAMA_BASE_URL:-$DEFAULT_MODAL_MODEL_URL}}}\" OLLAMA_API_KEY=\"\${OLLAMA_API_KEY:-\${MODAL_API_KEY:-\${MODAL_API_TOKEN_SECRET:-\${MODAL_TOKEN_SECRET:-}}}}\" EMBEDDING_SERVICE_URL=\"\${VECINITA_EMBEDDING_API_URL:-\${MODAL_EMBEDDING_ENDPOINT:-\${EMBEDDING_SERVICE_URL:-$DEFAULT_MODAL_EMBEDDING_URL}}}\" EMBEDDING_SERVICE_AUTH_TOKEN='$embed_token' DEFAULT_PROVIDER='ollama' DEFAULT_MODEL='' uv run -m uvicorn src.agent.main:app --host 0.0.0.0 --port 8000 ${uvicorn_reload_args}" C-m
  tmux send-keys -t "$SESSION_NAME":dev.2 "cd '$ROOT_DIR/backend' && echo '[gateway] uv run -m uvicorn src.api.main:app --port 8004 ${uvicorn_reload_args}' && AGENT_SERVICE_URL='http://localhost:8000' EMBEDDING_SERVICE_URL=\"\${VECINITA_EMBEDDING_API_URL:-\${MODAL_EMBEDDING_ENDPOINT:-\${EMBEDDING_SERVICE_URL:-$DEFAULT_MODAL_EMBEDDING_URL}}}\" EMBEDDING_SERVICE_AUTH_TOKEN='$embed_token' ANONYMIZED_TELEMETRY='false' DEV_ADMIN_ENABLED='true' DEV_ADMIN_BEARER_TOKEN='vecinita-dev-admin-token-2026' DEMO_MODE='false' uv run -m uvicorn src.api.main:app --host 0.0.0.0 --port 8004 ${uvicorn_reload_args}" C-m
  tmux send-keys -t "$SESSION_NAME":dev.3 "cd '$ROOT_DIR/frontend' && echo '[frontend] npm run dev -- --host 0.0.0.0 --port 5173' && npm run dev -- --host 0.0.0.0 --port 5173" C-m
  tmux send-keys -t "$SESSION_NAME":dev.4 "cd '$ROOT_DIR' && echo '[idle] reserved pane for ad-hoc commands' && bash" C-m
  tmux send-keys -t "$SESSION_NAME":dev.5 "cd '$ROOT_DIR' && echo '[idle] reserved pane for ad-hoc commands' && bash" C-m

  if ! wait_for_http_ready "Frontend" "http://localhost:5173/" "${DEV_FRONTEND_READY_TIMEOUT:-180}"; then
    echo "Warning: frontend readiness check timed out; attaching so you can inspect live logs."
    echo "Hint: run make dev-clear-ports, then retry make dev if this persists."
  fi

  if ! wait_for_http_ready "Gateway" "http://localhost:8004/health" "${DEV_GATEWAY_READY_TIMEOUT:-180}"; then
    echo "Warning: gateway readiness check timed out; attaching so you can inspect live logs."
  fi

  run_remote_endpoint_preflight_checks

  echo ""
  echo "Session '$SESSION_NAME' started."
  echo "Attach: tmux attach -t $SESSION_NAME"
  echo "Stop:   ./run/dev-session.sh stop"
  echo ""
  tmux attach -t "$SESSION_NAME"
}

stop_session() {
  if tmux_has_session; then
    tmux kill-session -t "$SESSION_NAME"
    echo "Stopped tmux session '$SESSION_NAME'."
  else
    echo "No tmux session named '$SESSION_NAME' is running."
  fi

  clear_managed_ports
  echo "Stopped local dev session services."
}

attach_session() {
  require_command tmux

  if tmux_has_session; then
    tmux attach -t "$SESSION_NAME"
  else
    echo "No session found. Run: ./run/dev-session.sh start"
    exit 1
  fi
}

ACTION="${1:-start}"

case "$ACTION" in
  start)
    start_single_terminal_session
    ;;
  start-tmux)
    start_session
    ;;
  stop)
    stop_session
    ;;
  attach)
    attach_session
    ;;
  restart)
    stop_session
    start_session
    ;;
  -h|--help|help)
    print_usage
    ;;
  *)
    print_usage
    exit 1
    ;;
esac
