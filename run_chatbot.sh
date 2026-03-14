#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$SCRIPT_DIR"
RASA_DIR="$APP_DIR/rasa"

# Prefer an explicit project-local venv, then active venv, then PATH.
VENV_CANDIDATES=(
  "${APP_DIR}/.venv"
  "$(cd "${APP_DIR}/.." && pwd)/.venv"
)

RASA=""
PYTHON=""

for venv in "${VENV_CANDIDATES[@]}"; do
  if [[ -x "${venv}/bin/rasa" && -x "${venv}/bin/python" ]]; then
    RASA="${venv}/bin/rasa"
    PYTHON="${venv}/bin/python"
    break
  fi
done

if [[ -z "${RASA}" || -z "${PYTHON}" ]]; then
  if [[ -n "${VIRTUAL_ENV:-}" && -x "${VIRTUAL_ENV}/bin/rasa" && -x "${VIRTUAL_ENV}/bin/python" ]]; then
    RASA="${VIRTUAL_ENV}/bin/rasa"
    PYTHON="${VIRTUAL_ENV}/bin/python"
  else
    RASA="$(command -v rasa || true)"
    PYTHON="$(command -v python3 || command -v python || true)"
  fi
fi

if [[ -z "${RASA:-}" || -z "${PYTHON:-}" ]]; then
  echo "Could not find usable 'rasa' and 'python'. Checked project .venv, parent .venv, VIRTUAL_ENV, and PATH." >&2
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
    ACTIONS_PORT="${RASA_ACTIONS_PORT:-5056}"
    ACTION_ENDPOINT="${RASA_ACTION_ENDPOINT:-http://127.0.0.1:${ACTIONS_PORT}/webhook}"
    cd "$RASA_DIR"
    RASA_ACTION_ENDPOINT="$ACTION_ENDPOINT" exec "$RASA" run --port "$PORT" --enable-api --cors "*" --model "$MODEL_PATH" --interface "$HOST" --endpoints "$RASA_DIR/endpoints.yml"
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
