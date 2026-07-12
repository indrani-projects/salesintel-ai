#!/bin/sh
# stack.sh — one command to run the SalesIntel_AI local stack (macOS / Linux).
#   ./stack.sh [start|stop|restart|status]     (default: start)
# Windows users: use  .\stack.ps1  instead.
#
# Runs backend (:8000) + frontend (:5173) in the background, logging to .logs/.
# PIDs tracked in .logs/*.pid so `stop` can kill the whole tree. First-time setup:
# see docs/RUNBOOK.md section 2 (on macOS/Linux the venv python is .venv/bin/python).

ROOT="$(cd "$(dirname "$0")" && pwd)"
BACKEND="$ROOT/backend"
FRONTEND="$ROOT/frontend"
LOGDIR="$ROOT/.logs"
PY="$BACKEND/.venv/bin/python"

port_up() { # $1 = port
  if command -v lsof >/dev/null 2>&1; then
    lsof -iTCP:"$1" -sTCP:LISTEN -t >/dev/null 2>&1
  else
    (exec 3<>"/dev/tcp/127.0.0.1/$1") 2>/dev/null && { exec 3>&-; return 0; } || return 1
  fi
}

kill_pidfile() { # $1 = name
  f="$LOGDIR/$1.pid"
  [ -f "$f" ] || return 0
  pid="$(cat "$f" 2>/dev/null)"
  if [ -n "$pid" ]; then
    pkill -TERM -P "$pid" 2>/dev/null || true   # children first
    kill  -TERM "$pid"    2>/dev/null || true
    sleep 1
    pkill -KILL -P "$pid" 2>/dev/null || true
    kill  -KILL "$pid"    2>/dev/null || true
  fi
  rm -f "$f"
}

stop_stack() {
  kill_pidfile backend
  kill_pidfile frontend
  for p in 8000 5173; do                        # fallback: free the ports
    if command -v lsof >/dev/null 2>&1; then
      for pid in $(lsof -iTCP:"$p" -sTCP:LISTEN -t 2>/dev/null); do
        kill -KILL "$pid" 2>/dev/null || true
      done
    fi
  done
  sleep 1
}

start_stack() {
  [ -x "$PY" ] || { echo "Backend venv not found at $PY — run setup first (docs/RUNBOOK.md §2)."; exit 1; }
  mkdir -p "$LOGDIR"
  if port_up 8000 || port_up 5173; then
    echo "A stack is already running — stopping it first."
    stop_stack
  fi

  echo "Starting backend  -> http://localhost:8000 ..."
  ( cd "$BACKEND" && "$PY" -m uvicorn app.main:app --port 8000 >"$LOGDIR/backend.out.log" 2>"$LOGDIR/backend.err.log" ) &
  echo $! > "$LOGDIR/backend.pid"

  echo "Starting frontend -> http://localhost:5173 ..."
  ( cd "$FRONTEND" && npm run dev >"$LOGDIR/frontend.out.log" 2>"$LOGDIR/frontend.err.log" ) &
  echo $! > "$LOGDIR/frontend.pid"

  beok=1; i=0
  while [ $i -lt 45 ]; do
    curl -fsS "http://localhost:8000/health" >/dev/null 2>&1 && { beok=0; break; }
    sleep 1; i=$((i + 1))
  done
  feok=1; i=0
  while [ $i -lt 45 ]; do
    curl -fsS "http://localhost:5173" >/dev/null 2>&1 && { feok=0; break; }
    sleep 1; i=$((i + 1))
  done

  echo ""
  [ $beok -eq 0 ] && echo "  Backend   UP    http://localhost:8000   (API docs: /docs)" || echo "  Backend   ...   not answering — see .logs/backend.err.log"
  [ $feok -eq 0 ] && echo "  Frontend  UP    http://localhost:5173" || echo "  Frontend  ...   not answering — see .logs/frontend.out.log"
  echo ""
  echo "Open http://localhost:5173    (stop with: ./stack.sh stop)"
}

status() {
  port_up 8000 && echo "  backend   :8000   UP" || echo "  backend   :8000   down"
  port_up 5173 && echo "  frontend  :5173   UP" || echo "  frontend  :5173   down"
}

case "${1:-start}" in
  start)   start_stack ;;
  stop)    echo "Stopping the stack ..."; stop_stack
           if ! port_up 8000 && ! port_up 5173; then echo "Stopped — ports 8000 and 5173 are free."
           else echo "Some ports still busy — run ./stack.sh stop again."; fi ;;
  restart) stop_stack; start_stack ;;
  status)  status ;;
  *)       echo "usage: ./stack.sh [start|stop|restart|status]"; exit 1 ;;
esac
