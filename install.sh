#!/usr/bin/env bash
set -e

# --------------------------------------------------
# Elevate if needed
# --------------------------------------------------
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

# --------------------------------------------------
# 1. System dependencies
# --------------------------------------------------
echo "[1/6] Checking system packages..."

REQUIRED_PACKAGES=(
    git
    python3
    python3-smbus
    python3-dotenv
    python3-libgpiod
    i2c-tools
)

apt update

for pkg in "${REQUIRED_PACKAGES[@]}"; do
    if ! dpkg -s "$pkg" >/dev/null 2>&1; then
        echo "Installing missing package: $pkg"
        apt install -y "$pkg"
    else
        echo "Package already installed: $pkg"
    fi
done

# --------------------------------------------------
# 2. Fetch repo to temp directory
# --------------------------------------------------
echo "[2/6] Fetching latest code from GitHub..."

rm -rf "$TMP_DIR"
sudo -u "$APP_USER" git clone "$REPO_URL" "$TMP_DIR"

# --------------------------------------------------
# 3. Sync repo into install directory
# --------------------------------------------------
echo "[3/6] Syncing application files..."

mkdir -p "$APP_DIR"

# Preserve existing .env
if [ -f "$APP_DIR/.env" ]; then
    rsync -a --delete --exclude=".env" "$TMP_DIR/" "$APP_DIR/"
else
    rsync -a --delete "$TMP_DIR/" "$APP_DIR/"
fi

chown -R "$APP_USER:$APP_USER" "$APP_DIR"

# --------------------------------------------------
# 4. Ensure log file exists
# --------------------------------------------------
echo "[4/6] Ensuring log file exists..."

LOG_FILE="$APP_DIR/rv-generator.log"

if [ ! -f "$LOG_FILE" ]; then
    touch "$LOG_FILE"
fi

chown root:root "$LOG_FILE"
chmod 644 "$LOG_FILE"

# --------------------------------------------------
# 5. Install / update systemd service
# --------------------------------------------------
echo "[5/6] Installing/updating systemd service..."

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

chmod 644 "$SERVICE_FILE"

# --------------------------------------------------
# 6. Reload systemd and restart service
# --------------------------------------------------
echo "[6/6] Reloading systemd and restarting service..."

systemctl daemon-reexec
systemctl daemon-reload
systemctl enable "$APP_NAME"
systemctl restart "$APP_NAME"

rm -rf "$TMP_DIR"

echo "======================================"
echo " ✅ RV Generator install/update complete"
echo "======================================"
