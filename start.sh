#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_DIR="${SCRIPT_DIR}/.pids"
LOG_DIR="/tmp"

mkdir -p "${PID_DIR}"

start_service() {
  local name="$1"
  shift
  local pid_file="${PID_DIR}/${name}.pid"
  local log_file="${LOG_DIR}/chatbot-${name}.log"

  if [[ -f "${pid_file}" ]]; then
    local existing_pid
    existing_pid="$(cat "${pid_file}" 2>/dev/null || true)"
    if [[ -n "${existing_pid}" ]] && kill -0 "${existing_pid}" 2>/dev/null; then
      echo "${name} already running (pid ${existing_pid})"
      return 0
    fi
    rm -f "${pid_file}"
  fi

  nohup "$@" >"${log_file}" 2>&1 &
  local pid=$!
  echo "${pid}" > "${pid_file}"
  echo "started ${name} (pid ${pid}) log=${log_file}"
}

wait_http_200() {
  local label="$1"
  local url="$2"
  local tries="${3:-40}"
  local sleep_s="${4:-2}"
  local i code

  for ((i=1; i<=tries; i++)); do
    code="$(curl -s -o /dev/null -w "%{http_code}" "${url}" || true)"
    if [[ "${code}" == "200" ]]; then
      echo "${label} healthy (${url})"
      return 0
    fi
    sleep "${sleep_s}"
  done

  echo "${label} failed health check (${url})" >&2
  return 1
}

start_service "actions" env CHATBOT_SERVICE=actions "${SCRIPT_DIR}/run_chatbot.sh"
start_service "flask" env CHATBOT_SERVICE=flask "${SCRIPT_DIR}/run_chatbot.sh"
start_service "rasa" env CHATBOT_SERVICE=rasa RASA_MODEL_PATH="${SCRIPT_DIR}/rasa/models/latest.tar.gz" "${SCRIPT_DIR}/run_chatbot.sh"

wait_http_200 "actions" "http://127.0.0.1:5056/health"
wait_http_200 "flask" "http://127.0.0.1:3000/health"
wait_http_200 "rasa" "http://127.0.0.1:5005/"

echo "all services are up"
