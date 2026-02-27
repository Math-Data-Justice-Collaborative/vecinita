#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SESSION_NAME="vecinita-dev"

detect_compose_cmd() {
  if command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
    echo "docker compose"
    return 0
  fi

  if command -v docker-compose >/dev/null 2>&1; then
    echo "docker-compose"
    return 0
  fi

  echo ""
  return 1
}

print_usage() {
  cat <<EOF
Usage: ./run/dev-session.sh [start|attach|stop|restart]

Commands:
  start    Start all local dev services in a tmux session (default)
  attach   Attach to the existing tmux session
  stop     Stop tmux session and stop Chroma container
  restart  Stop and start again
EOF
}

require_command() {
  local cmd="$1"
  if ! command -v "$cmd" >/dev/null 2>&1; then
    echo "Missing required command: $cmd"
    exit 1
  fi
}

tmux_has_session() {
  tmux has-session -t "$SESSION_NAME" 2>/dev/null
}

start_session() {
  require_command tmux
  require_command uv
  require_command npm

  local compose_cmd
  compose_cmd="$(detect_compose_cmd)"
  if [[ -z "$compose_cmd" ]]; then
    echo "Missing Docker Compose. Install either 'docker compose' (v2) or 'docker-compose' (v1)."
    exit 1
  fi

  if tmux_has_session; then
    echo "Session '$SESSION_NAME' already exists. Attaching..."
    tmux attach -t "$SESSION_NAME"
    exit 0
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

  tmux send-keys -t "$SESSION_NAME":dev.0 "cd '$ROOT_DIR' && echo '[chroma] $compose_cmd up chroma' && $compose_cmd up chroma" C-m
  tmux send-keys -t "$SESSION_NAME":dev.1 "cd '$ROOT_DIR/backend' && echo '[embedding] uv run -m uvicorn src.embedding_service.main:app --reload --port 8001' && uv run -m uvicorn src.embedding_service.main:app --host 0.0.0.0 --port 8001 --reload" C-m
  tmux send-keys -t "$SESSION_NAME":dev.2 "cd '$ROOT_DIR/backend' && echo '[agent] uv run -m uvicorn src.agent.main:app --reload --port 8000' && CHROMA_HOST='localhost' CHROMA_PORT='8002' CHROMA_SSL='false' uv run -m uvicorn src.agent.main:app --host 0.0.0.0 --port 8000 --reload" C-m
  tmux send-keys -t "$SESSION_NAME":dev.3 "cd '$ROOT_DIR/backend' && echo '[gateway] uv run -m uvicorn src.api.main:app --reload --port 8004' && AGENT_SERVICE_URL='http://localhost:8000' EMBEDDING_SERVICE_URL='http://localhost:8001' CHROMA_HOST='localhost' CHROMA_PORT='8002' CHROMA_SSL='false' SUPABASE_URL='http://localhost:3001' SUPABASE_KEY='test-anon-key-local-development-only' DEV_ADMIN_ENABLED='true' DEV_ADMIN_BEARER_TOKEN='vecinita-dev-admin-token-2026' SUPABASE_UPLOADS_BUCKET='documents' DEMO_MODE='false' uv run -m uvicorn src.api.main:app --host 0.0.0.0 --port 8004 --reload" C-m
  tmux send-keys -t "$SESSION_NAME":dev.4 "cd '$ROOT_DIR/frontend' && echo '[frontend] npm run dev -- --host 0.0.0.0 --port 5173' && npm run dev -- --host 0.0.0.0 --port 5173" C-m

  echo ""
  echo "Session '$SESSION_NAME' started."
  echo "Attach: tmux attach -t $SESSION_NAME"
  echo "Stop:   ./run/dev-session.sh stop"
  echo ""
  tmux attach -t "$SESSION_NAME"
}

stop_session() {
  require_command tmux

  local compose_cmd
  compose_cmd="$(detect_compose_cmd || true)"

  if tmux_has_session; then
    tmux kill-session -t "$SESSION_NAME"
    echo "Stopped tmux session '$SESSION_NAME'."
  else
    echo "No tmux session named '$SESSION_NAME' is running."
  fi

  (
    cd "$ROOT_DIR"
    if [[ -n "$compose_cmd" ]]; then
      $compose_cmd stop chroma >/dev/null 2>&1 || true
    fi
  )
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
