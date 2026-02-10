#!/usr/bin/env bash
set -euo pipefail

pids="$(lsof -ti :3000 -ti :5005 -ti :5056 || true)"
if [[ -n "$pids" ]]; then
  # Use sudo to terminate processes that may be owned by another user.
  sudo kill $pids
  echo "Stopped servers on 3000/5005/5056."
else
  echo "No servers running on 3000/5005/5056."
fi
