#!/usr/bin/env bash
# Installs VulnAssist on a Linux server. No Docker, no reverse proxy required to get started.
#
# Usage: ./scripts/install.sh

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/backend"
FRONTEND_DIR="$ROOT_DIR/frontend"
DATA_DIR="$ROOT_DIR/data"

echo "=== VulnAssist — Installation ==="

echo
echo "[1/6] Verifying prerequisites..."
if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 was not found on PATH. Install Python 3.11+ (e.g. 'apt install python3 python3-venv') and re-run this script." >&2
  exit 1
fi
echo "  Found $(python3 --version)"

if ! command -v node >/dev/null 2>&1; then
  echo "node was not found on PATH. Install Node.js LTS (e.g. via https://github.com/nodesource/distributions) and re-run this script." >&2
  exit 1
fi
echo "  Found Node.js $(node --version)"

echo
echo "[2/6] Creating Python virtual environment..."
VENV_DIR="$BACKEND_DIR/.venv"
if [ ! -d "$VENV_DIR" ]; then
  python3 -m venv "$VENV_DIR"
  echo "  Created $VENV_DIR"
else
  echo "  Virtual environment already exists, skipping."
fi

echo
echo "[3/6] Installing backend dependencies..."
"$VENV_DIR/bin/pip" install --upgrade pip >/dev/null
"$VENV_DIR/bin/pip" install -r "$BACKEND_DIR/requirements.txt"

echo
echo "[4/6] Preparing the database..."
mkdir -p "$DATA_DIR"
if [ ! -f "$BACKEND_DIR/.env" ]; then
  cp "$BACKEND_DIR/.env.example" "$BACKEND_DIR/.env"
  echo "  Created backend/.env from .env.example — edit it to set a real VULNASSIST_SECRET_KEY before going to production."
fi

(cd "$BACKEND_DIR" && "$VENV_DIR/bin/python" -m alembic upgrade head)
(cd "$BACKEND_DIR" && "$VENV_DIR/bin/python" -m app.seed)

echo
echo "[5/6] Installing and building the frontend..."
(cd "$FRONTEND_DIR" && npm install && npm run build)

echo
echo "[6/6] Installation complete."
echo
echo "Next step: run  ./scripts/start.sh  to launch VulnAssist,"
echo "then open http://localhost:8000 (or http://<server-name>:8000 from another machine on the network)."
