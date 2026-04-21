#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$SCRIPT_DIR"
BACKEND_DIR="$REPO_ROOT/AssetGuard AI"
FRONTEND_DIR="$REPO_ROOT/assetguard-ui"

if [[ ! -d "$BACKEND_DIR" ]]; then
  echo "Backend folder not found: $BACKEND_DIR" >&2
  exit 1
fi

if [[ ! -d "$FRONTEND_DIR" ]]; then
  echo "Frontend folder not found: $FRONTEND_DIR" >&2
  exit 1
fi

echo "== AssetGuard Backend Bootstrap =="
cd "$BACKEND_DIR"

if [[ ! -x ".venv/bin/python" && ! -x "venv/bin/python" ]]; then
  echo "[First-time] No backend virtual environment found. Creating .venv ..."
  python3 -m venv .venv
fi

if [[ -x ".venv/bin/python" ]]; then
  PY_EXE=".venv/bin/python"
  echo "Using backend venv: .venv"
else
  PY_EXE="venv/bin/python"
  echo "Using backend venv: venv"
fi

echo "Python executable path: $BACKEND_DIR/$PY_EXE"
"$PY_EXE" -m pip install --upgrade pip

echo "Ensuring backend dependencies from requirements.txt ..."
"$PY_EXE" -m pip install -r requirements.txt

BOOTSTRAP_MARKER=".dev_bootstrap_done"
DB_PATH="./instance/assetguard.db"
if [[ -f "$DB_PATH" ]]; then
  DB_EXISTED_BEFORE_UPGRADE=true
else
  DB_EXISTED_BEFORE_UPGRADE=false
fi

if [[ -f "$BOOTSTRAP_MARKER" ]]; then
  MARKER_EXISTS=true
else
  MARKER_EXISTS=false
fi

echo "Running database migrations: flask db upgrade ..."
"$PY_EXE" -m flask --app assetguard_app.py db upgrade

if [[ "$MARKER_EXISTS" == false || "$DB_EXISTED_BEFORE_UPGRADE" == false ]]; then
  if [[ "$DB_EXISTED_BEFORE_UPGRADE" == false ]]; then
    echo "[Bootstrap] Database file was missing before startup ($DB_PATH). Running flask seed ..."
  elif [[ "$MARKER_EXISTS" == false ]]; then
    echo "[First-time] Bootstrap marker missing. Running flask seed ..."
  fi

  "$PY_EXE" -m flask --app assetguard_app.py seed
  touch "$BOOTSTRAP_MARKER"
  echo "[First-time] Bootstrap completed. Marker file created."
else
  echo "[Normal] Bootstrap marker found and database existed before startup. Skip flask seed."
fi

echo "== AssetGuard Frontend Bootstrap =="
cd "$FRONTEND_DIR"

if [[ ! -d "node_modules" ]]; then
  echo "[First-time] node_modules not found. Running npm install ..."
  npm install
else
  echo "[Normal] node_modules exists. Skip npm install."
fi

echo "Starting backend and frontend dev servers ..."

cd "$BACKEND_DIR"
"$PY_EXE" -m flask --app assetguard_app.py run &
BACKEND_PID=$!

cd "$FRONTEND_DIR"
npm run dev &
FRONTEND_PID=$!

cleanup() {
  echo ""
  echo "Stopping backend and frontend..."
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
}

trap cleanup INT TERM
wait "$BACKEND_PID" "$FRONTEND_PID"
