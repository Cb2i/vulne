#!/usr/bin/env bash
# Starts the VulnAssist web application (single process: API + built frontend).
#
# Usage: ./scripts/start.sh [port] [bind-address]
#   ./scripts/start.sh
#   ./scripts/start.sh 8080
#   ./scripts/start.sh 8000 127.0.0.1

set -euo pipefail

PORT="${1:-8000}"
BIND_ADDRESS="${2:-0.0.0.0}"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
VENV_PYTHON="$BACKEND_DIR/.venv/bin/python"

if [ ! -x "$VENV_PYTHON" ]; then
  echo "Virtual environment not found. Run ./scripts/install.sh first." >&2
  exit 1
fi

if [ ! -d "$ROOT_DIR/frontend/dist" ]; then
  echo "Warning: frontend/dist not found — the compiled UI won't be served. Run 'npm run build' in frontend/, or re-run install.sh." >&2
fi

echo "Starting VulnAssist on http://${BIND_ADDRESS}:${PORT} ..."
echo "Press Ctrl+C to stop."

cd "$BACKEND_DIR"
exec "$VENV_PYTHON" -m uvicorn app.main:app --host "$BIND_ADDRESS" --port "$PORT"
