#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cleanup() {
  echo ""
  echo "[forensics] Shutting down backend and frontend..."
  [[ -n "${BACKEND_PID:-}" ]] && kill "$BACKEND_PID" 2>/dev/null || true
  [[ -n "${FRONTEND_PID:-}" ]] && kill "$FRONTEND_PID" 2>/dev/null || true
  exit 0
}
trap cleanup INT TERM

echo "[forensics] Starting FastAPI backend on http://127.0.0.1:8000 ..."
(
  cd "$ROOT_DIR/backend"
  exec "$ROOT_DIR/backend/.venv/bin/uvicorn" app.main:app --host 127.0.0.1 --port 8000
) &
BACKEND_PID=$!

echo "[forensics] Starting Next.js dashboard on http://localhost:3000 ..."
(
  cd "$ROOT_DIR/frontend"
  exec npm run dev
) &
FRONTEND_PID=$!

echo "[forensics] Dashboard: http://localhost:3000  |  API Docs: http://127.0.0.1:8000/docs"
wait
