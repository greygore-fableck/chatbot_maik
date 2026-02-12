#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$SCRIPT_DIR"
RASA_DIR="$APP_DIR/rasa"

if [[ -n "${VIRTUAL_ENV:-}" ]]; then
  VENV_BIN="$VIRTUAL_ENV/bin"
  RASA="$VENV_BIN/rasa"
  PYTHON="$VENV_BIN/python"
else
  RASA="$(command -v rasa || true)"
  PYTHON="$(command -v python || true)"
fi

if [[ -z "${RASA:-}" || -z "${PYTHON:-}" ]]; then
  echo "Could not find 'rasa' or 'python' in PATH or VIRTUAL_ENV." >&2
  exit 1
fi

cd "$RASA_DIR"

echo "Training Rasa model..."
"$RASA" train --config "$RASA_DIR/config.yml" --domain "$RASA_DIR/domain.yml" --data "$RASA_DIR/data" --out "$RASA_DIR/models"

cleanup() {
  if [[ -n "${RASA_PID:-}" ]]; then
    kill "$RASA_PID" 2>/dev/null || true
  fi
  if [[ -n "${ACTIONS_PID:-}" ]]; then
    kill "$ACTIONS_PID" 2>/dev/null || true
  fi
}
trap cleanup EXIT

"$RASA" run &
RASA_PID=$!

SANIC_HOST=127.0.0.1 "$RASA" run actions --port 5056 &
ACTIONS_PID=$!

cd "$APP_DIR"
exec "$PYTHON" app.py
