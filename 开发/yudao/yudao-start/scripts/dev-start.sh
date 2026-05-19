#!/usr/bin/env bash
set -euo pipefail

SCRIPT_NAME="$(basename "$0")"
PROJECT=""
PART="all"
CODE_ROOT="${CODE_ROOT:-${HOME}/code}"
FRONTEND_BASE_PORT="${FRONTEND_BASE_PORT:-3000}"
BACKEND_BASE_PORT="${BACKEND_BASE_PORT:-48080}"
SPRING_BOOT_PLUGIN_VERSION="${SPRING_BOOT_PLUGIN_VERSION:-3.4.5}"
DRY_RUN=false
YES=false

usage() {
  cat <<USAGE
Usage:
  ${SCRIPT_NAME} <project> [--frontend|--backend|--all|--db-up|--reset-db] [--frontend-port N] [--backend-port N] [--yes] [--dry-run]

Projects:
  effy       \${CODE_ROOT}/Effy
  checknm    \${CODE_ROOT}/checknm-system
  ruoqi      \${CODE_ROOT}/ruoqi-system
  yian       \${CODE_ROOT}/shanghai-yian-system

Examples:
  ${SCRIPT_NAME} effy
  ${SCRIPT_NAME} checknm --frontend
  ${SCRIPT_NAME} yian --backend-port 48090 --frontend-port 3010
  ${SCRIPT_NAME} effy --db-up
  ${SCRIPT_NAME} yian --reset-db --yes

Environment overrides:
  CODE_ROOT=\${HOME}/code
  FRONTEND_BASE_PORT=3000
  BACKEND_BASE_PORT=48080
  SPRING_BOOT_PLUGIN_VERSION=3.4.5
USAGE
}

die() {
  echo "ERROR: $*" >&2
  exit 1
}

is_port_busy() {
  local port="$1"
  lsof -nP -iTCP:"${port}" -sTCP:LISTEN >/dev/null 2>&1
}

find_free_port() {
  local port="$1"
  while is_port_busy "${port}"; do
    port=$((port + 1))
  done
  echo "${port}"
}

require_dir() {
  local dir="$1"
  [[ -d "${dir}" ]] || die "Directory not found: ${dir}"
}

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || die "Command not found: $1"
}

compose_cmd() {
  docker compose -f "${COMPOSE_FILE}" "$@"
}

project_config() {
  case "${PROJECT}" in
    effy)
      PROJECT_LABEL="Effy"
      FRONTEND_DIR="${CODE_ROOT}/Effy/effy-system-frontend"
      BACKEND_DIR="${CODE_ROOT}/Effy/effy-system-backend"
      SERVER_MODULE="effy-server"
      COMPOSE_FILE="${BACKEND_DIR}/script/docker/docker-compose.yml"
      MYSQL_VOLUME="effy-system_mysql"
      ;;
    checknm)
      PROJECT_LABEL="CheckNM"
      FRONTEND_DIR="${CODE_ROOT}/checknm-system/checknm-dashboard-ui"
      BACKEND_DIR="${CODE_ROOT}/checknm-system/checknm-dashboard-jdk17"
      SERVER_MODULE="checknm-server"
      COMPOSE_FILE="${BACKEND_DIR}/script/docker/docker-compose.yml"
      MYSQL_VOLUME="checknm-system_mysql"
      ;;
    ruoqi)
      PROJECT_LABEL="Ruoqi"
      FRONTEND_DIR="${CODE_ROOT}/ruoqi-system/ruoqi-system-frontend"
      BACKEND_DIR="${CODE_ROOT}/ruoqi-system/ruoqi-system-backend"
      SERVER_MODULE="ruoqi-server"
      COMPOSE_FILE="${BACKEND_DIR}/script/docker/docker-compose.yml"
      MYSQL_VOLUME="ruoqi-system_mysql"
      ;;
    yian|shanghai-yian)
      PROJECT_LABEL="Shanghai Yian"
      FRONTEND_DIR="${CODE_ROOT}/shanghai-yian-system/yian-system-frontend"
      BACKEND_DIR="${CODE_ROOT}/shanghai-yian-system/yian-system-backend"
      SERVER_MODULE="yian-server"
      COMPOSE_FILE="${BACKEND_DIR}/script/docker/docker-compose.yml"
      MYSQL_VOLUME="yian-system_mysql"
      ;;
    *)
      die "Unknown project: ${PROJECT}"
      ;;
  esac
}

run_db_up() {
  require_cmd docker
  require_dir "${BACKEND_DIR}"
  [[ -f "${COMPOSE_FILE}" ]] || die "Docker compose file not found: ${COMPOSE_FILE}"

  echo "[db] ${PROJECT_LABEL}: starting mysql redis adminer"

  if [[ "${DRY_RUN}" == true ]]; then
    echo "docker compose -f '${COMPOSE_FILE}' up -d mysql redis adminer"
    return
  fi

  compose_cmd up -d mysql redis adminer
}

run_reset_db() {
  require_cmd docker
  require_dir "${BACKEND_DIR}"
  [[ -f "${COMPOSE_FILE}" ]] || die "Docker compose file not found: ${COMPOSE_FILE}"

  echo "[db] ${PROJECT_LABEL}: reset MySQL"
  echo "[db] Compose file: ${COMPOSE_FILE}"
  echo "[db] MySQL volume to remove: ${MYSQL_VOLUME}"

  if [[ "${YES}" != true ]]; then
    echo
    echo "This will delete the local MySQL data volume for ${PROJECT_LABEL}."
    echo "Re-run with --reset-db --yes to remove ${MYSQL_VOLUME} and recreate it from init SQL."
    return
  fi

  if [[ "${DRY_RUN}" == true ]]; then
    echo "docker compose -f '${COMPOSE_FILE}' stop mysql"
    echo "docker compose -f '${COMPOSE_FILE}' rm -f mysql"
    echo "docker volume rm '${MYSQL_VOLUME}'"
    echo "docker compose -f '${COMPOSE_FILE}' up -d mysql redis adminer"
    return
  fi

  compose_cmd stop mysql || true
  compose_cmd rm -f mysql || true
  docker volume rm "${MYSQL_VOLUME}" 2>/dev/null || true
  compose_cmd up -d mysql redis adminer
}

run_frontend() {
  require_cmd pnpm
  require_dir "${FRONTEND_DIR}"

  echo "[frontend] ${PROJECT_LABEL}: http://localhost:${FRONTEND_PORT}"
  echo "[frontend] API: ${VITE_BASE_URL}"

  if [[ "${DRY_RUN}" == true ]]; then
    echo "(cd '${FRONTEND_DIR}' && VITE_BASE_URL='${VITE_BASE_URL}' pnpm exec vite --mode env.local --host 0.0.0.0 --port ${FRONTEND_PORT})"
    return
  fi

  (
    cd "${FRONTEND_DIR}"
    VITE_BASE_URL="${VITE_BASE_URL}" pnpm exec vite --mode env.local --host 0.0.0.0 --port "${FRONTEND_PORT}"
  )
}

run_backend() {
  require_cmd mvn
  require_dir "${BACKEND_DIR}"

  echo "[backend] ${PROJECT_LABEL}: http://localhost:${BACKEND_PORT}"

  if [[ "${DRY_RUN}" == true ]]; then
    echo "(cd '${BACKEND_DIR}' && mvn -pl '${SERVER_MODULE}' -am compile && mvn -pl '${SERVER_MODULE}' org.springframework.boot:spring-boot-maven-plugin:${SPRING_BOOT_PLUGIN_VERSION}:run -Dspring-boot.run.profiles=local -Dspring-boot.run.arguments='--server.port=${BACKEND_PORT}')"
    return
  fi

  (
    cd "${BACKEND_DIR}"
    mvn -pl "${SERVER_MODULE}" -am compile
    mvn -pl "${SERVER_MODULE}" "org.springframework.boot:spring-boot-maven-plugin:${SPRING_BOOT_PLUGIN_VERSION}:run" \
      -Dspring-boot.run.profiles=local \
      -Dspring-boot.run.arguments="--server.port=${BACKEND_PORT}"
  )
}

cleanup() {
  local status=$?
  if [[ "${DRY_RUN}" != true ]]; then
    trap - INT TERM EXIT
    if (( ${#CHILD_PIDS[@]} > 0 )); then
      echo
      echo "Stopping ${PROJECT_LABEL} local processes..."
      kill "${CHILD_PIDS[@]}" >/dev/null 2>&1 || true
      wait "${CHILD_PIDS[@]}" >/dev/null 2>&1 || true
    fi
  fi
  exit "${status}"
}

if (($# == 0)); then
  usage
  exit 0
fi

if [[ "$1" == "-h" || "$1" == "--help" ]]; then
  usage
  exit 0
fi

PROJECT="$1"
shift

while (($# > 0)); do
  case "$1" in
    --frontend)
      PART="frontend"
      shift
      ;;
    --backend)
      PART="backend"
      shift
      ;;
    --all)
      PART="all"
      shift
      ;;
    --db-up)
      PART="db-up"
      shift
      ;;
    --reset-db)
      PART="reset-db"
      shift
      ;;
    --frontend-port)
      [[ $# -ge 2 ]] || die "--frontend-port requires a value"
      FRONTEND_BASE_PORT="$2"
      shift 2
      ;;
    --backend-port)
      [[ $# -ge 2 ]] || die "--backend-port requires a value"
      BACKEND_BASE_PORT="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN=true
      shift
      ;;
    --yes|-y)
      YES=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      die "Unknown option: $1"
      ;;
  esac
done

project_config

case "${PART}" in
  frontend|backend|all|db-up|reset-db) ;;
  *) die "Invalid part: ${PART}" ;;
esac

if [[ "${PART}" == "db-up" ]]; then
  run_db_up
  exit 0
fi

if [[ "${PART}" == "reset-db" ]]; then
  run_reset_db
  exit 0
fi

if [[ "${PART}" == "backend" ]]; then
  FRONTEND_PORT="${FRONTEND_BASE_PORT}"
  BACKEND_PORT="$(find_free_port "${BACKEND_BASE_PORT}")"
elif [[ "${PART}" == "frontend" ]]; then
  FRONTEND_PORT="$(find_free_port "${FRONTEND_BASE_PORT}")"
  BACKEND_PORT="${BACKEND_BASE_PORT}"
else
  FRONTEND_PORT="$(find_free_port "${FRONTEND_BASE_PORT}")"
  BACKEND_PORT="$(find_free_port "${BACKEND_BASE_PORT}")"
fi
VITE_BASE_URL="http://localhost:${BACKEND_PORT}"
CHILD_PIDS=()

echo "Project: ${PROJECT_LABEL}"
echo "Mode: ${PART}"

if [[ "${PART}" == "backend" ]]; then
  run_backend
  exit 0
fi

if [[ "${PART}" == "frontend" ]]; then
  run_frontend
  exit 0
fi

if [[ "${DRY_RUN}" == true ]]; then
  run_backend
  run_frontend
  exit 0
fi

trap cleanup INT TERM EXIT

run_backend &
CHILD_PIDS+=("$!")

run_frontend &
CHILD_PIDS+=("$!")

while :; do
  for pid in "${CHILD_PIDS[@]}"; do
    if ! kill -0 "${pid}" >/dev/null 2>&1; then
      wait "${pid}" || true
      exit 0
    fi
  done
  sleep 1
done
