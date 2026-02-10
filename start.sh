#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

nohup "${SCRIPT_DIR}/run_chatbot.sh" > /tmp/chatbot.log 2>&1 &
echo "Started. Open http://localhost:3000"
echo "Logs: /tmp/chatbot.log"
