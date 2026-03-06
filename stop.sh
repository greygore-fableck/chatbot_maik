#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_DIR="${SCRIPT_DIR}/.pids"

stopped_any=false

stop_pid_file() {
  local name="$1"
  local pid_file="${PID_DIR}/${name}.pid"
  if [[ ! -f "${pid_file}" ]]; then
    return 0
  fi

  local pid
  pid="$(cat "${pid_file}" 2>/dev/null || true)"
  if [[ -n "${pid}" ]] && kill -0 "${pid}" 2>/dev/null; then
    kill "${pid}" 2>/dev/null || true
    sleep 1
    if kill -0 "${pid}" 2>/dev/null; then
      kill -9 "${pid}" 2>/dev/null || true
    fi
    echo "stopped ${name} (pid ${pid})"
    stopped_any=true
  fi
  rm -f "${pid_file}"
}

stop_pid_file "rasa"
stop_pid_file "actions"
stop_pid_file "flask"

# Fallback for manually started processes on known ports.
fallback_pids="$(lsof -ti :3000 -ti :5005 -ti :5056 || true)"
if [[ -n "${fallback_pids}" ]]; then
  kill ${fallback_pids} 2>/dev/null || true
  sleep 1
  remaining="$(lsof -ti :3000 -ti :5005 -ti :5056 || true)"
  if [[ -n "${remaining}" ]]; then
    kill -9 ${remaining} 2>/dev/null || true
  fi
  echo "stopped remaining services on ports 3000/5005/5056"
  stopped_any=true
fi

if [[ "${stopped_any}" == "false" ]]; then
  echo "no services were running"
fi
