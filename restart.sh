#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

"${SCRIPT_DIR}/stop.sh"
"${SCRIPT_DIR}/start.sh"
if ! "${SCRIPT_DIR}/status.sh"; then
  echo
  echo "restart check failed. recent logs:"
  echo "--- flask ---"
  tail -n 40 /tmp/chatbot-flask.log 2>/dev/null || true
  echo "--- rasa ---"
  tail -n 40 /tmp/chatbot-rasa.log 2>/dev/null || true
  echo "--- actions ---"
  tail -n 40 /tmp/chatbot-actions.log 2>/dev/null || true
  exit 1
fi
