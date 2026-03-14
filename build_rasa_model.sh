#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RASA_DIR="$SCRIPT_DIR/rasa"

VENV_CANDIDATES=(
  "${SCRIPT_DIR}/.venv"
  "$(cd "${SCRIPT_DIR}/.." && pwd)/.venv"
)

RASA_BIN=""

for venv in "${VENV_CANDIDATES[@]}"; do
  if [[ -x "${venv}/bin/rasa" ]]; then
    RASA_BIN="${venv}/bin/rasa"
    break
  fi
done

if [[ -z "${RASA_BIN}" ]]; then
  if [[ -n "${VIRTUAL_ENV:-}" && -x "${VIRTUAL_ENV}/bin/rasa" ]]; then
    RASA_BIN="${VIRTUAL_ENV}/bin/rasa"
  else
    RASA_BIN="$(command -v rasa || true)"
  fi
fi

if [[ -z "${RASA_BIN:-}" ]]; then
  echo "Could not find usable 'rasa' binary." >&2
  exit 1
fi

cd "$RASA_DIR"
"$RASA_BIN" train

LATEST_MODEL="$(ls -1t models/*.tar.gz 2>/dev/null | grep -v '/latest\.tar\.gz$' | head -n 1 || true)"
if [[ -z "$LATEST_MODEL" ]]; then
  echo "Training finished but no model artifact was found in $RASA_DIR/models." >&2
  exit 1
fi

ln -sfn "$(basename "$LATEST_MODEL")" models/latest.tar.gz
echo "latest.tar.gz -> $(readlink models/latest.tar.gz)"
