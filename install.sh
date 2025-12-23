#!/usr/bin/env bash
set -e

APP_NAME="rv-generator"
APP_DIR="/usr/local/${APP_NAME}"
APP_USER="bluecloud"
VENV_DIR="${APP_DIR}/venv"
SERVICE_FILE="/etc/systemd/system/${APP_NAME}.service"
REPO_URL="https://github.com/teknoprep/rv-generator.git"

echo "======================================"
echo " RV Generator Installer / Updater"
echo "======================================"

# --------------------------------------------------
# 1. System dependencies (install if missing)
# --------------------------------------------------
echo "[1/7] Checking system packages..."

REQUIRED_PACKAGES=(
    git
    python3
    python3-full
    python3-venv
    python3-pip
    libgpiod3
    i2c-tools
)

for pkg in "${REQUIRED_PACKAGES[@]}"; do
    if ! dpkg -s "$pkg" >/dev/null 2>&1; then
        echo "Installing missing package: $pkg"
        apt install -y "$pkg"
    else
        echo "Package already installed: $pkg"
    fi
done

# --------------------------------------------------
# 2. Application directory
# --------------------------------------------------
echo "[2/7] Preparing application directory..."

mkdir -p "${APP_DIR}"
chown -R "${APP_USER}:${APP_USER}" "${APP_DIR}"

# --------------------------------------------------
# 3. Clone or update repository
# --------------------------------------------------
echo "[3/7] Syncing GitHub repository..."

if [ -d "${APP_DIR}/.git" ]; then
    echo "Repository exists, pulling updates..."
    cd "${APP_DIR}"
    git fetch origin
    git pull
else
    echo "Cloning repository..."
    git clone "${REPO_URL}" "${APP_DIR}"
    chown -R "${APP_USER}:${APP_USER}" "${APP_DIR}"
fi

# --------------------------------------------------
# 4. Python virtual environment
# --------------------------------------------------
echo "[4/7] Checking Python virtual environment..."

if [ ! -d "${VENV_DIR}" ]; then
    echo "Creating virtual environment..."
    sudo -u "${APP_USER}" python3 -m venv "${VENV_DIR}"
else
    echo "Virtual environment already exists"
fi

# --------------------------------------------------
# 5. Python dependencies
# --------------------------------------------------
echo "[5/7] Installing/updating Python dependencies..."

sudo -u "${APP_USER}" "${VENV_DIR}/bin/pip" install --upgrade pip setuptools wheel

if [ -f "${APP_DIR}/requirements.txt" ]; then
    sudo -u "${APP_USER}" "${VENV_DIR}/bin/pip" install --upgrade -r "${APP_DIR}/requirements.txt"
else
    echo "WARNING: requirements.txt not found, installing defaults"
    sudo -u "${APP_USER}" "${VENV_DIR}/bin/pip" install --upgrade \
        RPi.GPIO \
        adafruit-circuitpython-dht \
        adafruit-circuitpython-ina226
fi

# --------------------------------------------------
# 6. systemd service
# --------------------------------------------------
echo "[6/7] Installing/updating systemd service..."

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
# 7. Reload and restart service
# --------------------------------------------------
echo "[7/7] Reloading and restarting service..."

systemctl daemon-reexec
systemctl daemon-reload

if systemctl is-enabled --quiet "${APP_NAME}.service"; then
    echo "Service already enabled"
else
    systemctl enable "${APP_NAME}.service"
fi

systemctl restart "${APP_NAME}.service"

echo "======================================"
echo " ✅ RV Generator install/update complete"
echo "======================================"
echo
systemctl status "${APP_NAME}.service" --no-pager
