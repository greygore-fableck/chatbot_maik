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

SERVICE="${CHATBOT_SERVICE:-flask}"

case "$SERVICE" in
  flask)
    cd "$APP_DIR"
    exec "$PYTHON" app.py
    ;;

  rasa)
    MODEL_PATH="${RASA_MODEL_PATH:-$RASA_DIR/models/latest.tar.gz}"
    if [[ ! -f "$MODEL_PATH" ]]; then
      echo "Model file not found: $MODEL_PATH" >&2
      echo "Set RASA_MODEL_PATH or place a trained model at rasa/models/latest.tar.gz" >&2
      exit 1
    fi

    PORT="${PORT:-5005}"
    HOST="${RASA_HOST:-0.0.0.0}"
    cd "$RASA_DIR"
    exec "$RASA" run --port "$PORT" --enable-api --cors "*" --model "$MODEL_PATH" --host "$HOST"
    ;;

  actions)
    PORT="${PORT:-5056}"
    HOST="${RASA_ACTIONS_HOST:-0.0.0.0}"
    cd "$RASA_DIR"
    SANIC_HOST="$HOST" exec "$RASA" run actions --port "$PORT"
    ;;

  *)
    echo "Unsupported CHATBOT_SERVICE: $SERVICE" >&2
    echo "Use one of: flask, rasa, actions" >&2
    exit 1
    ;;
esac
