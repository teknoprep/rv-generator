#!/usr/bin/env bash
set -e

if [ "$EUID" -ne 0 ]; then
  exec sudo bash "$0"
fi

APP_DIR="/usr/local/rv-generator"
SERVICE="/etc/systemd/system/rv-generator.service"
USER_NAME="${SUDO_USER}"

apt update
apt install -y git python3 python3-smbus python3-pip python3-venv

mkdir -p "$APP_DIR"
cp rv_generator.py requirements.txt .env "$APP_DIR"
chown -R "$USER_NAME:$USER_NAME" "$APP_DIR"

python3 -m venv "$APP_DIR/venv"
"$APP_DIR/venv/bin/pip" install -r "$APP_DIR/requirements.txt"

cat <<EOF > "$SERVICE"
[Unit]
Description=RV Generator Controller
After=network.target

[Service]
ExecStart=$APP_DIR/venv/bin/python $APP_DIR/rv_generator.py
WorkingDirectory=$APP_DIR
Restart=always
User=root

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable rv-generator
systemctl restart rv-generator

echo "✅ RV Generator installed and running"
