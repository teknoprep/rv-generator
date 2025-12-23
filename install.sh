#!/usr/bin/env bash
set -e

APP_NAME="rv-generator"
APP_DIR="/usr/local/${APP_NAME}"
APP_USER="bluecloud"
VENV_DIR="${APP_DIR}/venv"
REPO_URL="https://github.com/teknoprep/rv-generator.git"
SERVICE_FILE="/etc/systemd/system/${APP_NAME}.service"

echo "======================================"
echo " Installing RV Generator Controller"
echo "======================================"

# --------------------------------------------------
# 1. Install system dependencies
# --------------------------------------------------
echo "[1/7] Installing system packages..."

apt update
apt install -y \
    git \
    python3 \
    python3-full \
    python3-venv \
    python3-pip \
    libgpiod3 \
    i2c-tools

# --------------------------------------------------
# 2. Create application directory
# --------------------------------------------------
echo "[2/7] Creating application directory..."

mkdir -p "${APP_DIR}"
chown -R "${APP_USER}:${APP_USER}" "${APP_DIR}"

# --------------------------------------------------
# 3. Clone or update repository
# --------------------------------------------------
echo "[3/7] Fetching application from GitHub..."

if [ -d "${APP_DIR}/.git" ]; then
    echo "Repo exists, updating..."
    cd "${APP_DIR}"
    git pull
else
    git clone "${REPO_URL}" "${APP_DIR}"
    chown -R "${APP_USER}:${APP_USER}" "${APP_DIR}"
fi

# --------------------------------------------------
# 4. Create Python virtual environment
# --------------------------------------------------
echo "[4/7] Creating Python virtual environment..."

sudo -u "${APP_USER}" python3 -m venv "${VENV_DIR}"

# --------------------------------------------------
# 5. Install Python dependencies
# --------------------------------------------------
echo "[5/7] Installing Python dependencies..."

sudo -u "${APP_USER}" "${VENV_DIR}/bin/pip" install --upgrade pip

# If requirements.txt exists, install it
if [ -f "${APP_DIR}/requirements.txt" ]; then
    sudo -u "${APP_USER}" "${VENV_DIR}/bin/pip" install -r "${APP_DIR}/requirements.txt"
else
    # Fallback: install known dependencies explicitly
    sudo -u "${APP_USER}" "${VENV_DIR}/bin/pip" install \
        RPi.GPIO \
        adafruit-circuitpython-dht \
        adafruit-circuitpython-ina226
fi

# --------------------------------------------------
# 6. Install systemd service
# --------------------------------------------------
echo "[6/7] Installing systemd service..."

cat <<EOF > "${SERVICE_FILE}"
[Unit]
Description=RV Generator Controller
After=network.target
Wants=network.target

[Service]
Type=simple
ExecStart=${VENV_DIR}/bin/python ${APP_DIR}/rv_generator.py
WorkingDirectory=${APP_DIR}
Restart=always
RestartSec=5
User=root

[Install]
WantedBy=multi-user.target
EOF

chmod 644 "${SERVICE_FILE}"

# --------------------------------------------------
# 7. Enable and start service
# --------------------------------------------------
echo "[7/7] Enabling and starting service..."

systemctl daemon-reexec
systemctl daemon-reload
systemctl enable "${APP_NAME}.service"
systemctl restart "${APP_NAME}.service"

echo "======================================"
echo " ✅ RV Generator installed successfully"
echo "======================================"
echo
echo "Service status:"
systemctl status "${APP_NAME}.service" --no-pager
