#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "${SCRIPT_DIR}"

run_once() {
  ./restart.sh
  ./status.sh
  curl -fsS http://127.0.0.1:3000/health >/dev/null
}

if run_once; then
  echo "local app is ready: http://127.0.0.1:3000"
  exit 0
fi

echo "first start failed, retrying once..."
sleep 2

run_once
echo "local app is ready: http://127.0.0.1:3000"
