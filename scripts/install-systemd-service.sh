#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="${SERVICE_NAME:-systemctl-api}"
SERVICE_USER="${SERVICE_USER:-root}"
SERVICE_GROUP="${SERVICE_GROUP:-root}"
PORT="${PORT:-51000}"
PYTHON_BIN="${PYTHON_BIN:-python3}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
APP_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
VENV_DIR="${APP_DIR}/.venv"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

if [[ "$(id -u)" -ne 0 ]]; then
  echo "Run this script with sudo or as root."
  exit 1
fi

if ! command -v systemctl >/dev/null 2>&1; then
  echo "systemctl was not found. This script must run on a systemd-based Ubuntu host."
  exit 1
fi

if ! command -v "${PYTHON_BIN}" >/dev/null 2>&1; then
  echo "${PYTHON_BIN} was not found. Install python3 before running this script."
  exit 1
fi

if [[ ! -f "${APP_DIR}/requirements.txt" ]]; then
  echo "requirements.txt was not found in ${APP_DIR}."
  exit 1
fi

echo "Creating virtual environment in ${VENV_DIR}..."
if ! "${PYTHON_BIN}" -m venv "${VENV_DIR}"; then
  echo "Failed to create venv. On Ubuntu, install it with: apt-get install -y python3-venv"
  exit 1
fi

echo "Installing Python dependencies..."
"${VENV_DIR}/bin/pip" install --upgrade pip
"${VENV_DIR}/bin/pip" install -r "${APP_DIR}/requirements.txt"

if [[ ! -f "${APP_DIR}/.env" ]]; then
  if command -v openssl >/dev/null 2>&1; then
    SECRET_KEY="$(openssl rand -hex 32)"
  elif [[ -r /proc/sys/kernel/random/uuid ]]; then
    SECRET_KEY="$(cat /proc/sys/kernel/random/uuid)"
  else
    SECRET_KEY="$(date +%s)-change-this-secret"
  fi

  echo "Creating ${APP_DIR}/.env..."
  {
    echo "SECRET_KEY=${SECRET_KEY}"
  } > "${APP_DIR}/.env"
  chmod 600 "${APP_DIR}/.env"
else
  echo "Using existing ${APP_DIR}/.env."
fi

echo "Writing systemd service to ${SERVICE_FILE}..."
cat > "${SERVICE_FILE}" <<EOF
[Unit]
Description=Systemctl API
After=network.target

[Service]
Type=simple
User=${SERVICE_USER}
Group=${SERVICE_GROUP}
WorkingDirectory=${APP_DIR}
EnvironmentFile=${APP_DIR}/.env
ExecStart=${VENV_DIR}/bin/uvicorn app.main:app --host 0.0.0.0 --port ${PORT}
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

echo "Reloading systemd and starting ${SERVICE_NAME}..."
systemctl daemon-reload
systemctl enable "${SERVICE_NAME}"
systemctl restart "${SERVICE_NAME}"

echo
echo "Service installed."
echo "Name: ${SERVICE_NAME}"
echo "Port: ${PORT}"
echo "URL: http://localhost:${PORT}"
echo
echo "Useful commands:"
echo "  systemctl status ${SERVICE_NAME}"
echo "  journalctl -u ${SERVICE_NAME} -f"
echo "  systemctl restart ${SERVICE_NAME}"
