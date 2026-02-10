#!/usr/bin/env bash
set -euo pipefail

BASE_DIR="/Users/maik/PycharmProjects/kiChatbot"
APP_DIR="$BASE_DIR/chatbotFlask"
RASA_DIR="$APP_DIR/rasa"
VENV_BIN="$BASE_DIR/.venv/bin"

RASA="$VENV_BIN/rasa"
PYTHON="$VENV_BIN/python"

cd "$RASA_DIR"

echo "Training Rasa model..."
"$RASA" train

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
