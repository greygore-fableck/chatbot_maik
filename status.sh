#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_DIR="${SCRIPT_DIR}/.pids"
unhealthy=0

check_service() {
  local name="$1"
  local port="$2"
  local url="$3"
  local pid_file="${PID_DIR}/${name}.pid"
  local pid="-"
  local state="down"
  local code

  if [[ -f "${pid_file}" ]]; then
    pid="$(cat "${pid_file}" 2>/dev/null || echo "-")"
    if [[ "${pid}" != "-" ]] && kill -0 "${pid}" 2>/dev/null; then
      state="running"
    fi
  fi

  code="$(curl -s -o /dev/null -w "%{http_code}" "${url}" || true)"
  if [[ "${state}" != "running" || "${code}" != "200" ]]; then
    unhealthy=1
  fi
  if [[ "${code}" == "200" ]]; then
    printf "%-8s pid=%-7s port=%-5s http=%s state=%s\n" "${name}" "${pid}" "${port}" "${code}" "${state}"
  else
    printf "%-8s pid=%-7s port=%-5s http=%s state=%s\n" "${name}" "${pid}" "${port}" "${code:-000}" "${state}"
  fi
}

check_service "flask" "3000" "http://127.0.0.1:3000/health"
check_service "rasa" "5005" "http://127.0.0.1:5005/"
check_service "actions" "5056" "http://127.0.0.1:5056/health"

exit "${unhealthy}"
