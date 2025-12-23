#!/usr/bin/env bash
set -e

# --------------------------------------------------
# Elevate privileges if needed
# --------------------------------------------------
if [ "$EUID" -ne 0 ]; then
    echo "Re-running installer with sudo..."
    exec sudo bash "$0" "$@"
fi

APP_NAME="rv-generator"
APP_DIR="/usr/local/${APP_NAME}"
REPO_URL="https://github.com/teknoprep/rv-generator.git"
SERVICE_FILE="/etc/systemd/system/${APP_NAME}.service"

APP_USER="${SUDO_USER:-root}"
USER_HOME=$(eval echo "~${APP_USER}")
VENV_DIR="${APP_DIR}/venv"
TMP_DIR="/tmp/${APP_NAME}-install"

echo "======================================"
echo " RV Generator Installer / Updater"
echo " User: ${APP_USER}"
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
    python3-smbus
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
# 2. Clone or update repository to temp dir
# --------------------------------------------------
echo "[2/7] Fetching latest code from GitHub..."

rm -rf "$TMP_DIR"

sudo -u "$APP_USER" git clone "$REPO_URL" "$TMP_DIR"

# --------------------------------------------------
# 3. Sync repo contents to install dir
# --------------------------------------------------
echo "[3/7] Syncing application files..."

mkdir -p "$APP_DIR"

# Preserve existing .env
if [ -f "$APP_DIR/.env" ]; then
    rsync -a --delete --exclude=".env" "$TMP_DIR/" "$APP_DIR/"
else
    rsync -a --delete "$TMP_DIR/" "$APP_DIR/"
fi

chown -R "$APP_USER:$APP_USER" "$APP_DIR"

# --------------------------------------------------
# 4. Python virtual environment
# --------------------------------------------------
echo "[4/7] Checking Python virtual environment..."

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    sudo -u "$APP_USER" python3 -m venv "$VENV_DIR"
else
    echo "Virtual environment already exists"
fi

# --------------------------------------------------
# 5. Python dependencies
# --------------------------------------------------
echo "[5/7] Installing/updating Python dependencies..."

sudo -u "$APP_USER" "$VENV_DIR/bin/pip" install --upgrade pip setuptools wheel
sudo -u "$APP_USER" "$VENV_DIR/bin/pip" install --upgrade -r "$APP_DIR/requirements.txt"

# --------------------------------------------------
# 6. systemd service
# --------------------------------------------------
echo "[6/7] Installing/updating systemd service..."

cat <<EOF > "$SERVICE_FILE"
[Unit]
Description=RV Generator Controller
After=network.target

[Service]
Type=simple
ExecStart=$VENV_DIR/bin/python $APP_DIR/rv_generator.py
WorkingDirectory=$APP_DIR
Restart=always
RestartSec=5
User=root

[Install]
WantedBy=multi-user.target
EOF

chmod 644 "$SERVICE_FILE"

# --------------------------------------------------
# 7. Reload & restart service
# --------------------------------------------------
echo "[7/7] Reloading and restarting service..."

systemctl daemon-reexec
systemctl daemon-reload
systemctl enable "$APP_NAME"
systemctl restart "$APP_NAME"

rm -rf "$TMP_DIR"

echo "======================================"
echo " ✅ RV Generator install/update complete"
echo "======================================"
