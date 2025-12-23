#!/usr/bin/env bash
set -e

if [ "$EUID" -ne 0 ]; then
    echo "Re-running installer with sudo..."
    exec sudo bash "$0" "$@"
fi

APP_NAME="rv-generator"
APP_DIR="/usr/local/${APP_NAME}"
REPO_URL="https://github.com/teknoprep/rv-generator.git"
SERVICE_FILE="/etc/systemd/system/${APP_NAME}.service"
TMP_DIR="/tmp/${APP_NAME}-install"
APP_USER="${SUDO_USER:-root}"

echo "======================================"
echo " RV Generator Installer / Updater"
echo " User: ${APP_USER}"
echo "======================================"

echo "[1/6] Installing system packages..."

apt update
apt install -y \
    git \
    python3 \
    python3-smbus \
    python3-dotenv \
    python3-libgpiod \
    python3-adafruit-circuitpython-dht \
    i2c-tools

echo "[2/6] Fetching latest code..."

rm -rf "$TMP_DIR"
sudo -u "$APP_USER" git clone "$REPO_URL" "$TMP_DIR"

echo "[3/6] Syncing application files..."

mkdir -p "$APP_DIR"

if [ -f "$APP_DIR/.env" ]; then
    rsync -a --delete --exclude=".env" "$TMP_DIR/" "$APP_DIR/"
else
    rsync -a --delete "$TMP_DIR/" "$APP_DIR/"
fi

chown -R "$APP_USER:$APP_USER" "$APP_DIR"

echo "[4/6] Ensuring log file exists..."

LOG_FILE="$APP_DIR/rv-generator.log"
touch "$LOG_FILE"
chmod 644 "$LOG_FILE"

echo "[5/6] Installing systemd service..."

cat <<EOF > "$SERVICE_FILE"
[Unit]
Description=RV Generator Controller
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 $APP_DIR/rv_generator.py
WorkingDirectory=$APP_DIR
Restart=always
RestartSec=5
User=root

[Install]
WantedBy=multi-user.target
EOF

echo "[6/6] Reloading and restarting service..."

systemctl daemon-reexec
systemctl daemon-reload
systemctl enable "$APP_NAME"
systemctl restart "$APP_NAME"

rm -rf "$TMP_DIR"

echo "======================================"
echo " ✅ RV Generator install/update complete"
echo "======================================"
