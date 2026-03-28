#!/usr/bin/env bash

set -euo pipefail

# Resolve to repository root (parent of run/), not run/ itself.
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SESSION_NAME="vecinita-dev"

COMPOSE_CMD=()
DEV_CHILD_PIDS=()
DEV_RUNNING=0

set_compose_cmd() {
  if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD=(docker compose)
    return 0
  fi

  if command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD=(docker-compose)
    return 0
  fi

  COMPOSE_CMD=()
  return 1
}

detect_compose_cmd() {
  if set_compose_cmd; then
    echo "${COMPOSE_CMD[*]}"
    return 0
  fi

  echo ""
  return 1
}

print_usage() {
  cat <<EOF
Usage: ./run/dev-session.sh [start|attach|stop|restart]

Commands:
  start       Start all local dev services in one terminal with cascading logs (default)
  start-tmux  Start all local dev services in a tmux session (legacy)
  attach      Attach to the existing tmux session
  stop        Stop dev services and stop Chroma container
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
  echo "5173 8000 8001 8002 8004"
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

  if [[ ${#COMPOSE_CMD[@]} -gt 0 ]]; then
    (
      cd "$ROOT_DIR"
      EMBEDDING_SERVICE_AUTH_TOKEN='dev-embed-token' "${COMPOSE_CMD[@]}" stop chroma >/dev/null 2>&1 || true
    )
  fi

  clear_managed_ports
  echo "Dev services stopped."
}

start_single_terminal_session() {
  require_command uv
  require_command npm
  reset_existing_state_if_needed

  if ! set_compose_cmd; then
    echo "Missing Docker Compose. Install either 'docker compose' (v2) or 'docker-compose' (v1)."
    exit 1
  fi

  (
    cd "$ROOT_DIR"
    EMBEDDING_SERVICE_AUTH_TOKEN='dev-embed-token' "${COMPOSE_CMD[@]}" up -d chroma
  )

  echo ""
  echo "Starting local dev stack in single-terminal cascading log mode"
  echo "Press Ctrl+C to stop all services"
  echo ""

  DEV_RUNNING=1
  trap cleanup_single_terminal INT TERM EXIT

  run_with_prefix "chroma" bash -lc "cd '$ROOT_DIR' && EMBEDDING_SERVICE_AUTH_TOKEN='dev-embed-token' ${COMPOSE_CMD[*]} logs -f --tail=30 chroma"
  run_with_prefix "embedding" bash -lc "cd '$ROOT_DIR/backend' && uv run -m uvicorn src.embedding_service.main:app --host 0.0.0.0 --port 8001 --reload"
  run_with_prefix "agent" bash -lc "cd '$ROOT_DIR/backend' && CHROMA_HOST='localhost' CHROMA_PORT='8002' CHROMA_SSL='false' OLLAMA_BASE_URL='\${MODAL_OLLAMA_ENDPOINT:-\${OLLAMA_BASE_URL:-http://localhost:11434}}' OLLAMA_API_KEY='\${OLLAMA_API_KEY:-\${MODAL_API_PROXY_SECRET:-\${MODAL_API_KEY:-\${MODAL_API_TOKEN_SECRET:-}}}}' EMBEDDING_SERVICE_URL='\${MODAL_EMBEDDING_ENDPOINT:-\${EMBEDDING_SERVICE_URL:-http://localhost:8001}}' EMBEDDING_SERVICE_AUTH_TOKEN='\${EMBEDDING_SERVICE_AUTH_TOKEN:-\${MODAL_API_PROXY_SECRET:-\${MODAL_API_KEY:-\${MODAL_API_TOKEN_SECRET:-}}}}' DEFAULT_PROVIDER='ollama' DEFAULT_MODEL='' uv run -m uvicorn src.agent.main:app --host 0.0.0.0 --port 8000 --reload"
  run_with_prefix "gateway" bash -lc "cd '$ROOT_DIR/backend' && AGENT_SERVICE_URL='http://localhost:8000' EMBEDDING_SERVICE_URL='\${MODAL_EMBEDDING_ENDPOINT:-\${EMBEDDING_SERVICE_URL:-http://localhost:8001}}' EMBEDDING_SERVICE_AUTH_TOKEN='\${EMBEDDING_SERVICE_AUTH_TOKEN:-\${MODAL_API_PROXY_SECRET:-\${MODAL_API_KEY:-\${MODAL_API_TOKEN_SECRET:-}}}}' CHROMA_HOST='localhost' CHROMA_PORT='8002' CHROMA_SSL='false' SUPABASE_URL='http://localhost:3001' SUPABASE_KEY='test-anon-key-local-development-only' DEV_ADMIN_ENABLED='true' DEV_ADMIN_BEARER_TOKEN='vecinita-dev-admin-token-2026' SUPABASE_UPLOADS_BUCKET='documents' DEMO_MODE='false' uv run -m uvicorn src.api.main:app --host 0.0.0.0 --port 8004 --reload"
  run_with_prefix "frontend" bash -lc "cd '$ROOT_DIR/frontend' && npm run dev -- --host 0.0.0.0 --port 5173"

  if ! wait_for_http_ready "Frontend" "http://localhost:5173/" "${DEV_FRONTEND_READY_TIMEOUT:-180}"; then
    echo "Warning: frontend readiness check timed out; inspect logs above."
  fi

  if ! wait_for_http_ready "Gateway" "http://localhost:8004/health" "${DEV_GATEWAY_READY_TIMEOUT:-180}"; then
    echo "Warning: gateway readiness check timed out; inspect logs above."
  fi

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

  local compose_cmd
  compose_cmd="$(detect_compose_cmd)"
  if [[ -z "$compose_cmd" ]]; then
    echo "Missing Docker Compose. Install either 'docker compose' (v2) or 'docker-compose' (v1)."
    exit 1
  fi

  tmux new-session -d -s "$SESSION_NAME" -n dev
  tmux set-option -t "$SESSION_NAME" -g mouse on
  tmux set-option -t "$SESSION_NAME" -g history-limit 100000
  tmux set-window-option -t "$SESSION_NAME":dev mode-keys vi

  tmux split-window -h -t "$SESSION_NAME":dev.0
  tmux split-window -v -t "$SESSION_NAME":dev.0
  tmux split-window -v -t "$SESSION_NAME":dev.1
  tmux split-window -v -t "$SESSION_NAME":dev.2
  tmux select-layout -t "$SESSION_NAME":dev tiled

  tmux send-keys -t "$SESSION_NAME":dev.0 "cd '$ROOT_DIR' && echo '[chroma] EMBEDDING_SERVICE_AUTH_TOKEN=dev-embed-token $compose_cmd up chroma' && EMBEDDING_SERVICE_AUTH_TOKEN='dev-embed-token' $compose_cmd up chroma" C-m
  tmux send-keys -t "$SESSION_NAME":dev.1 "cd '$ROOT_DIR/backend' && echo '[embedding] uv run -m uvicorn src.embedding_service.main:app --reload --port 8001' && uv run -m uvicorn src.embedding_service.main:app --host 0.0.0.0 --port 8001 --reload" C-m
  tmux send-keys -t "$SESSION_NAME":dev.2 "cd '$ROOT_DIR/backend' && echo '[agent] uv run -m uvicorn src.agent.main:app --reload --port 8000' && CHROMA_HOST='localhost' CHROMA_PORT='8002' CHROMA_SSL='false' OLLAMA_BASE_URL='\${MODAL_OLLAMA_ENDPOINT:-\${OLLAMA_BASE_URL:-http://localhost:11434}}' OLLAMA_API_KEY='\${OLLAMA_API_KEY:-\${MODAL_API_PROXY_SECRET:-\${MODAL_API_KEY:-\${MODAL_API_TOKEN_SECRET:-}}}}' EMBEDDING_SERVICE_URL='\${MODAL_EMBEDDING_ENDPOINT:-\${EMBEDDING_SERVICE_URL:-http://localhost:8001}}' EMBEDDING_SERVICE_AUTH_TOKEN='\${EMBEDDING_SERVICE_AUTH_TOKEN:-\${MODAL_API_PROXY_SECRET:-\${MODAL_API_KEY:-\${MODAL_API_TOKEN_SECRET:-}}}}' DEFAULT_PROVIDER='ollama' DEFAULT_MODEL='' uv run -m uvicorn src.agent.main:app --host 0.0.0.0 --port 8000 --reload" C-m
  tmux send-keys -t "$SESSION_NAME":dev.3 "cd '$ROOT_DIR/backend' && echo '[gateway] uv run -m uvicorn src.api.main:app --reload --port 8004' && AGENT_SERVICE_URL='http://localhost:8000' EMBEDDING_SERVICE_URL='\${MODAL_EMBEDDING_ENDPOINT:-\${EMBEDDING_SERVICE_URL:-http://localhost:8001}}' EMBEDDING_SERVICE_AUTH_TOKEN='\${EMBEDDING_SERVICE_AUTH_TOKEN:-\${MODAL_API_PROXY_SECRET:-\${MODAL_API_KEY:-\${MODAL_API_TOKEN_SECRET:-}}}}' CHROMA_HOST='localhost' CHROMA_PORT='8002' CHROMA_SSL='false' SUPABASE_URL='http://localhost:3001' SUPABASE_KEY='test-anon-key-local-development-only' DEV_ADMIN_ENABLED='true' DEV_ADMIN_BEARER_TOKEN='vecinita-dev-admin-token-2026' SUPABASE_UPLOADS_BUCKET='documents' DEMO_MODE='false' uv run -m uvicorn src.api.main:app --host 0.0.0.0 --port 8004 --reload" C-m
  tmux send-keys -t "$SESSION_NAME":dev.4 "cd '$ROOT_DIR/frontend' && echo '[frontend] npm run dev -- --host 0.0.0.0 --port 5173' && npm run dev -- --host 0.0.0.0 --port 5173" C-m

  if ! wait_for_http_ready "Frontend" "http://localhost:5173/" "${DEV_FRONTEND_READY_TIMEOUT:-180}"; then
    echo "Warning: frontend readiness check timed out; attaching so you can inspect live logs."
    echo "Hint: run make dev-clear-ports, then retry make dev if this persists."
  fi

  if ! wait_for_http_ready "Gateway" "http://localhost:8004/health" "${DEV_GATEWAY_READY_TIMEOUT:-180}"; then
    echo "Warning: gateway readiness check timed out; attaching so you can inspect live logs."
  fi

  echo ""
  echo "Session '$SESSION_NAME' started."
  echo "Attach: tmux attach -t $SESSION_NAME"
  echo "Stop:   ./run/dev-session.sh stop"
  echo ""
  tmux attach -t "$SESSION_NAME"
}

stop_session() {
  set_compose_cmd || true

  if tmux_has_session; then
    tmux kill-session -t "$SESSION_NAME"
    echo "Stopped tmux session '$SESSION_NAME'."
  else
    echo "No tmux session named '$SESSION_NAME' is running."
  fi

  (
    cd "$ROOT_DIR"
    if [[ ${#COMPOSE_CMD[@]} -gt 0 ]]; then
      EMBEDDING_SERVICE_AUTH_TOKEN='dev-embed-token' "${COMPOSE_CMD[@]}" stop chroma >/dev/null 2>&1 || true
    fi
  )

  clear_managed_ports
  echo "Stopped Chroma container (if running)."
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
