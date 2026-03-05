#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MODELS_DIR="$SCRIPT_DIR/rasa/models"
LINK_PATH="$MODELS_DIR/latest.tar.gz"

if [[ ! -d "$MODELS_DIR" ]]; then
  echo "Models directory not found: $MODELS_DIR" >&2
  exit 1
fi

TARGET_INPUT="${1:-}"
TARGET_PATH=""

if [[ -n "$TARGET_INPUT" ]]; then
  if [[ "$TARGET_INPUT" = /* ]]; then
    TARGET_PATH="$TARGET_INPUT"
  else
    TARGET_PATH="$MODELS_DIR/$TARGET_INPUT"
  fi

  if [[ ! -f "$TARGET_PATH" ]]; then
    echo "Model file not found: $TARGET_PATH" >&2
    exit 1
  fi
else
  TARGET_PATH="$(ls -1t "$MODELS_DIR"/*.tar.gz 2>/dev/null | grep -v '/latest\.tar\.gz$' | head -n 1 || true)"
  if [[ -z "$TARGET_PATH" ]]; then
    echo "No model .tar.gz files found in $MODELS_DIR" >&2
    exit 1
  fi
fi

ln -sfn "$(basename "$TARGET_PATH")" "$LINK_PATH"
echo "latest.tar.gz -> $(readlink "$LINK_PATH")"
